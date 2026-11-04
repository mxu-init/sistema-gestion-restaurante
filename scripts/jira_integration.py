"""Jira Cloud Integration Utility.

This script integrates the local development workflow with Jira Cloud REST API
using the `atlassian-python-api` library.

Supported Operations:
- Transition issue status (e.g. SGR-43 to 'In Review' or 'Done').
- Assign issue to current authenticated user.
- Post a comment to an issue with a GitHub Pull Request link.
- Inspect issue status, assignee, and available transitions.
- Multi-step workflow sync (assign + transition + PR comment in a single command).

Credentials (read from .env):
- JIRA_URL: Base URL of Jira instance (e.g., https://your-domain.atlassian.net)
- JIRA_USER_EMAIL: Atlassian account email
- JIRA_API_TOKEN: Atlassian API Token
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from atlassian import Jira
from dotenv import load_dotenv
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout


# ANSI escape sequences for clean, colored terminal output
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def print_success(msg: str) -> None:
    """Print success message to stdout."""
    print(f"{Style.GREEN}{Style.BOLD}[SUCCESS]{Style.RESET} {msg}")


def print_info(msg: str) -> None:
    """Print info message to stdout."""
    print(f"{Style.CYAN}{Style.BOLD}[INFO]{Style.RESET} {msg}")


def print_warning(msg: str) -> None:
    """Print warning message to stderr."""
    print(f"{Style.YELLOW}{Style.BOLD}[WARNING]{Style.RESET} {msg}", file=sys.stderr)


def print_error(msg: str) -> None:
    """Print error message to stderr."""
    print(f"{Style.RED}{Style.BOLD}[ERROR]{Style.RESET} {msg}", file=sys.stderr)


def find_default_env_path() -> Path:
    """Locate the .env file in the current working directory or repository root."""
    cwd = Path.cwd()
    if (cwd / ".env").is_file():
        return cwd / ".env"

    # Walk up to repo root (looking for .git, .env, or requirements.txt)
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        env_candidate = parent / ".env"
        if env_candidate.is_file():
            return env_candidate
        if (parent / ".git").is_dir():
            return env_candidate

    return cwd / ".env"


def load_jira_credentials(env_path: Path | str | None = None) -> tuple[str, str, str]:
    """Load and validate Jira credentials from environment or .env file.

    Returns:
        tuple[str, str, str]: (jira_url, jira_user_email, jira_api_token)

    Raises:
        ValueError: If any required credential is missing or invalid.
    """
    target_env = Path(env_path) if env_path else find_default_env_path()
    if target_env.is_file():
        load_dotenv(dotenv_path=target_env, override=False)

    jira_url = (os.getenv("JIRA_URL") or "").strip().rstrip("/")
    jira_user_email = (os.getenv("JIRA_USER_EMAIL") or "").strip()
    jira_api_token = (os.getenv("JIRA_API_TOKEN") or "").strip()

    missing = []
    if not jira_url:
        missing.append("JIRA_URL")
    if not jira_user_email:
        missing.append("JIRA_USER_EMAIL")
    if not jira_api_token:
        missing.append("JIRA_API_TOKEN")

    if missing:
        source_desc = f" ({target_env})" if target_env.is_file() else " (no .env found)"
        raise ValueError(
            f"Missing required Jira credentials in environment/.env{source_desc}: "
            f"{', '.join(missing)}.\n"
            "Please check your .env file or refer to .env.example for required variables."
        )

    if not (jira_url.startswith("https://") or jira_url.startswith("http://")):
        raise ValueError(
            f"Invalid JIRA_URL '{jira_url}'. Must begin with 'https://' or 'http://'."
        )

    return jira_url, jira_user_email, jira_api_token


def get_jira_client(
    url: str | None = None,
    username: str | None = None,
    token: str | None = None,
    env_path: Path | str | None = None,
) -> Jira:
    """Create and return an authenticated Atlassian Jira client.

    If credentials are not explicitly passed, they are loaded from .env.
    """
    if not (url and username and token):
        env_url, env_user, env_token = load_jira_credentials(env_path=env_path)
        url = url or env_url
        username = username or env_user
        token = token or env_token

    return Jira(url=url, username=username, password=token, cloud=True)


def extract_api_error_message(err: Exception) -> str:
    """Extract a user-friendly error message from Jira / requests exceptions."""
    if isinstance(err, HTTPError):
        response = getattr(err, "response", None)
        if response is not None:
            status = response.status_code
            if status == 401:
                return (
                    "401 Unauthorized: Invalid Jira credentials. "
                    "Verify JIRA_USER_EMAIL and JIRA_API_TOKEN."
                )
            if status == 403:
                return (
                    "403 Forbidden: Authenticated user does not have permission "
                    "to perform this action on the target project/issue."
                )
            if status == 404:
                return (
                    "404 Not Found: The specified issue or endpoint does not exist. "
                    "Verify the issue key and Jira URL."
                )

            # Try parsing JSON error messages returned by Jira Cloud REST API
            try:
                body = response.json()
                if isinstance(body, dict):
                    err_msgs = body.get("errorMessages", [])
                    field_errors = body.get("errors", {})
                    combined = []
                    if err_msgs:
                        combined.extend(err_msgs)
                    if isinstance(field_errors, dict):
                        for field, msg in field_errors.items():
                            combined.append(f"{field}: {msg}")
                    if combined:
                        return f"HTTP {status}: {'; '.join(combined)}"
            except Exception:
                pass
            return f"HTTP {status}: {response.text.strip() or str(err)}"
        return f"HTTP Error: {err}"

    if isinstance(err, ReqConnectionError):
        return f"Connection Error: Unable to reach Jira server. Please check your network and JIRA_URL."

    if isinstance(err, Timeout):
        return "Timeout Error: Request to Jira server timed out."

    if isinstance(err, RequestException):
        return f"Request Error: {err}"

    return str(err)


def get_current_user(jira: Jira | None = None) -> dict[str, Any]:
    """Fetch currently authenticated Jira Cloud user profile.

    Returns:
        dict[str, Any]: Contains 'accountId', 'displayName', 'emailAddress'.
    """
    client = jira or get_jira_client()
    user_info = client.myself()
    if not isinstance(user_info, dict):
        raise ValueError("Unexpected response received when fetching current user.")
    return user_info


def transition_issue(
    issue_key: str,
    target_status: str,
    jira: Jira | None = None,
) -> bool:
    """Move an issue status using Jira transitions (e.g. SGR-43 to 'In Review' or 'Done').

    Finds the transition by matching either destination status name or transition name.

    Args:
        issue_key: Jira issue key, e.g. 'SGR-43'.
        target_status: Desired status name or transition action (case-insensitive).
        jira: Optional pre-configured Jira client instance.

    Returns:
        bool: True if transition succeeded, False otherwise.
    """
    clean_key = issue_key.strip().upper()
    target_clean = target_status.strip().lower()

    try:
        client = jira or get_jira_client()
        transitions = client.get_issue_transitions(clean_key)

        if not transitions:
            print_warning(
                f"No transitions available for issue '{clean_key}'. "
                "Check issue state or user permissions."
            )
            return False

        # Attempt to match either destination status ("to") or transition name ("name")
        matched_transition: dict[str, Any] | None = None
        for t in transitions:
            to_name = str(t.get("to", "")).strip().lower()
            t_name = str(t.get("name", "")).strip().lower()
            if target_clean == to_name or target_clean == t_name:
                matched_transition = t
                break

        if not matched_transition:
            print_error(
                f"Status/transition '{target_status}' is not valid from the current state of {clean_key}."
            )
            print_info(f"Available transitions for {clean_key}:")
            for t in transitions:
                print(
                    f"  - '{t.get('name')}' -> Leads to status: '{t.get('to')}' (ID: {t.get('id')})"
                )
            return False

        transition_id = matched_transition["id"]
        client.set_issue_status_by_transition_id(clean_key, transition_id)

        print_success(
            f"Issue {clean_key} successfully transitioned to '{matched_transition.get('to')}' "
            f"(via transition '{matched_transition.get('name')}', ID: {transition_id})."
        )
        return True

    except Exception as exc:
        print_error(f"Failed to transition {clean_key}: {extract_api_error_message(exc)}")
        return False


def assign_issue_to_me(
    issue_key: str,
    jira: Jira | None = None,
) -> bool:
    """Assign an issue to the currently authenticated Jira Cloud user.

    Args:
        issue_key: Jira issue key, e.g. 'SGR-43'.
        jira: Optional pre-configured Jira client instance.

    Returns:
        bool: True if assignment succeeded, False otherwise.
    """
    clean_key = issue_key.strip().upper()

    try:
        client = jira or get_jira_client()
        user_info = get_current_user(client)

        account_id = user_info.get("accountId")
        display_name = user_info.get("displayName", "Current User")
        email = user_info.get("emailAddress", "N/A")

        if not account_id:
            print_error("Unable to determine Atlassian accountId of current user.")
            return False

        client.assign_issue(issue=clean_key, account_id=account_id)

        print_success(
            f"Issue {clean_key} assigned to {display_name} ({email}) [accountId: {account_id}]."
        )
        return True

    except Exception as exc:
        print_error(f"Failed to assign {clean_key}: {extract_api_error_message(exc)}")
        return False


def comment_pr_link(
    issue_key: str,
    pr_url: str,
    note: str | None = None,
    jira: Jira | None = None,
) -> bool:
    """Post a comment to an issue containing a GitHub Pull Request link.

    Args:
        issue_key: Jira issue key, e.g. 'SGR-43'.
        pr_url: URL to the GitHub Pull Request.
        note: Optional extra note or description to include in the comment.
        jira: Optional pre-configured Jira client instance.

    Returns:
        bool: True if comment was posted, False otherwise.
    """
    clean_key = issue_key.strip().upper()
    clean_pr = pr_url.strip()

    if not (clean_pr.startswith("http://") or clean_pr.startswith("https://")):
        print_error(f"Invalid Pull Request URL '{pr_url}'. Must begin with 'https://' or 'http://'.")
        return False

    # Jira wiki markup formatting for clean rendering in Jira Cloud
    comment_lines = [
        "h4. 🔗 GitHub Pull Request",
        f"*PR Link:* [{clean_pr}|{clean_pr}]",
    ]
    if note and note.strip():
        comment_lines.append(f"*Note:* {note.strip()}")

    comment_body = "\n\n".join(comment_lines)

    try:
        client = jira or get_jira_client()
        client.issue_add_comment(clean_key, comment_body)
        print_success(f"Pull Request comment posted to {clean_key}: {clean_pr}")
        return True

    except Exception as exc:
        print_error(
            f"Failed to post comment to {clean_key}: {extract_api_error_message(exc)}"
        )
        return False


def get_issue_info(issue_key: str, jira: Jira | None = None) -> dict[str, Any] | None:
    """Fetch and display issue summary, current status, assignee, and available transitions."""
    clean_key = issue_key.strip().upper()
    try:
        client = jira or get_jira_client()
        issue_data = client.issue(clean_key, fields="summary,status,assignee")
        fields = issue_data.get("fields", {})

        summary = fields.get("summary", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        assignee = fields.get("assignee")
        assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"

        print_info(f"Issue {clean_key} Overview:")
        print(f"  Summary:     {summary}")
        print(f"  Status:      {status}")
        print(f"  Assignee:    {assignee_name}")

        transitions = client.get_issue_transitions(clean_key)
        if transitions:
            print("  Transitions:")
            for t in transitions:
                print(f"    - '{t.get('name')}' -> '{t.get('to')}' (ID: {t.get('id')})")
        else:
            print("  Transitions: None available")

        return {
            "key": clean_key,
            "summary": summary,
            "status": status,
            "assignee": assignee_name,
            "transitions": transitions,
        }
    except Exception as exc:
        print_error(f"Failed to fetch {clean_key}: {extract_api_error_message(exc)}")
        return None


def run_sync_workflow(
    issue_key: str,
    status: str | None = None,
    assign_to_me: bool = False,
    pr_url: str | None = None,
    note: str | None = None,
    jira: Jira | None = None,
) -> bool:
    """Run an all-in-one local workflow sync on a Jira issue."""
    clean_key = issue_key.strip().upper()
    print_info(f"Starting Jira workflow sync for issue {clean_key}...")

    client = jira or get_jira_client()
    success = True

    if assign_to_me:
        if not assign_issue_to_me(clean_key, jira=client):
            success = False

    if status:
        if not transition_issue(clean_key, status, jira=client):
            success = False

    if pr_url:
        if not comment_pr_link(clean_key, pr_url, note=note, jira=client):
            success = False

    if success:
        print_success(f"All workflow steps for {clean_key} completed successfully.")
    else:
        print_warning(f"One or more workflow steps for {clean_key} encountered issues.")

    return success


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="jira_integration.py",
        description="Integrate local development workflow with Jira Cloud REST API.",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to custom .env file (defaults to finding .env in repo root).",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: transition
    p_trans = subparsers.add_parser("transition", help="Move issue status.")
    p_trans.add_argument("issue", type=str, help="Jira issue key (e.g. SGR-43)")
    p_trans.add_argument(
        "status",
        type=str,
        help="Target status or transition name (e.g. 'In Review', 'Done')",
    )

    # Command: assign
    p_assign = subparsers.add_parser(
        "assign", help="Assign issue to currently authenticated user."
    )
    p_assign.add_argument("issue", type=str, help="Jira issue key (e.g. SGR-43)")

    # Command: comment
    p_comment = subparsers.add_parser(
        "comment", help="Post a comment with a GitHub PR link to the issue."
    )
    p_comment.add_argument("issue", type=str, help="Jira issue key (e.g. SGR-43)")
    p_comment.add_argument("pr_url", type=str, help="GitHub Pull Request URL")
    p_comment.add_argument(
        "--note", type=str, default=None, help="Optional additional note"
    )

    # Command: info
    p_info = subparsers.add_parser(
        "info", help="Display issue status, assignee, and available transitions."
    )
    p_info.add_argument("issue", type=str, help="Jira issue key (e.g. SGR-43)")

    # Command: sync
    p_sync = subparsers.add_parser(
        "sync", help="Run workflow sync (assign + transition + PR comment)."
    )
    p_sync.add_argument("issue", type=str, help="Jira issue key (e.g. SGR-43)")
    p_sync.add_argument(
        "--status",
        type=str,
        default=None,
        help="Move to this status (e.g. 'In Review')",
    )
    p_sync.add_argument(
        "--assign",
        action="store_true",
        help="Assign the issue to currently authenticated user",
    )
    p_sync.add_argument(
        "--pr", type=str, default=None, help="GitHub Pull Request URL to attach"
    )
    p_sync.add_argument(
        "--note", type=str, default=None, help="Optional note for the PR comment"
    )

    return parser


def main() -> int:
    """CLI Entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        client = get_jira_client(env_path=args.env_file)
    except ValueError as val_err:
        print_error(str(val_err))
        return 1
    except Exception as exc:
        print_error(f"Failed to initialize Jira client: {exc}")
        return 1

    if args.command == "transition":
        ok = transition_issue(args.issue, args.status, jira=client)
        return 0 if ok else 1

    if args.command == "assign":
        ok = assign_issue_to_me(args.issue, jira=client)
        return 0 if ok else 1

    if args.command == "comment":
        ok = comment_pr_link(args.issue, args.pr_url, note=args.note, jira=client)
        return 0 if ok else 1

    if args.command == "info":
        res = get_issue_info(args.issue, jira=client)
        return 0 if res else 1

    if args.command == "sync":
        if not (args.status or args.assign or args.pr):
            print_warning("No action specified for sync. Use --status, --assign, and/or --pr.")
            return 1
        ok = run_sync_workflow(
            args.issue,
            status=args.status,
            assign_to_me=args.assign,
            pr_url=args.pr,
            note=args.note,
            jira=client,
        )
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
