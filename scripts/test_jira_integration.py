"""Unit tests for Jira Integration Script."""

import unittest
from unittest.mock import MagicMock, patch
from requests.exceptions import HTTPError
import requests

from scripts.jira_integration import (
    load_jira_credentials,
    transition_issue,
    assign_issue_to_me,
    comment_pr_link,
    get_issue_info,
    run_sync_workflow,
    extract_api_error_message,
)


class TestJiraIntegration(unittest.TestCase):

    def test_load_credentials_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                load_jira_credentials(env_path="non_existent.env")
            self.assertIn("Missing required Jira credentials", str(ctx.exception))

    def test_load_credentials_valid(self):
        env_vars = {
            "JIRA_URL": "https://company.atlassian.net",
            "JIRA_USER_EMAIL": "dev@company.com",
            "JIRA_API_TOKEN": "secret-token",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            url, email, token = load_jira_credentials(env_path="non_existent.env")
            self.assertEqual(url, "https://company.atlassian.net")
            self.assertEqual(email, "dev@company.com")
            self.assertEqual(token, "secret-token")

    def test_transition_issue_by_status_name(self):
        mock_jira = MagicMock()
        mock_jira.get_issue_transitions.return_value = [
            {"id": 11, "name": "Start Progress", "to": "In Progress"},
            {"id": 21, "name": "Submit for Review", "to": "In Review"},
            {"id": 31, "name": "Close", "to": "Done"},
        ]

        result = transition_issue("SGR-43", "In Review", jira=mock_jira)
        self.assertTrue(result)
        mock_jira.set_issue_status_by_transition_id.assert_called_once_with("SGR-43", 21)

    def test_transition_issue_by_transition_name(self):
        mock_jira = MagicMock()
        mock_jira.get_issue_transitions.return_value = [
            {"id": 11, "name": "Start Progress", "to": "In Progress"},
            {"id": 21, "name": "Submit for Review", "to": "In Review"},
        ]

        result = transition_issue("SGR-43", "Submit for Review", jira=mock_jira)
        self.assertTrue(result)
        mock_jira.set_issue_status_by_transition_id.assert_called_once_with("SGR-43", 21)

    def test_transition_issue_not_found(self):
        mock_jira = MagicMock()
        mock_jira.get_issue_transitions.return_value = [
            {"id": 11, "name": "Start Progress", "to": "In Progress"}
        ]

        result = transition_issue("SGR-43", "Done", jira=mock_jira)
        self.assertFalse(result)
        mock_jira.set_issue_status_by_transition_id.assert_not_called()

    def test_assign_issue_to_me(self):
        mock_jira = MagicMock()
        mock_jira.myself.return_value = {
            "accountId": "acc-123456",
            "displayName": "Simon Lopez",
            "emailAddress": "simon@example.com",
        }

        result = assign_issue_to_me("SGR-43", jira=mock_jira)
        self.assertTrue(result)
        mock_jira.assign_issue.assert_called_once_with(issue="SGR-43", account_id="acc-123456")

    def test_comment_pr_link_valid(self):
        mock_jira = MagicMock()
        pr_url = "https://github.com/org/repo/pull/43"

        result = comment_pr_link("SGR-43", pr_url, note="Fixes table layout", jira=mock_jira)
        self.assertTrue(result)
        mock_jira.issue_add_comment.assert_called_once()
        args, _ = mock_jira.issue_add_comment.call_args
        self.assertEqual(args[0], "SGR-43")
        self.assertIn(pr_url, args[1])
        self.assertIn("Fixes table layout", args[1])

    def test_comment_pr_link_invalid_url(self):
        mock_jira = MagicMock()
        result = comment_pr_link("SGR-43", "not-a-url", jira=mock_jira)
        self.assertFalse(result)
        mock_jira.issue_add_comment.assert_not_called()

    def test_error_handling_http_error(self):
        mock_jira = MagicMock()
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"errorMessages": ["Issue Does Not Exist"]}
        mock_jira.get_issue_transitions.side_effect = HTTPError("404 Error", response=mock_resp)

        result = transition_issue("SGR-999", "Done", jira=mock_jira)
        self.assertFalse(result)

    def test_extract_api_error_message_401(self):
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 401
        err = HTTPError("Unauthorized", response=mock_resp)
        msg = extract_api_error_message(err)
        self.assertIn("401 Unauthorized", msg)

    def test_run_sync_workflow(self):
        mock_jira = MagicMock()
        mock_jira.myself.return_value = {
            "accountId": "acc-123",
            "displayName": "Simon",
            "emailAddress": "simon@example.com",
        }
        mock_jira.get_issue_transitions.return_value = [
            {"id": 21, "name": "Review", "to": "In Review"}
        ]

        result = run_sync_workflow(
            "SGR-43",
            status="In Review",
            assign_to_me=True,
            pr_url="https://github.com/org/repo/pull/43",
            jira=mock_jira,
        )
        self.assertTrue(result)
        mock_jira.assign_issue.assert_called_once_with(issue="SGR-43", account_id="acc-123")
        mock_jira.set_issue_status_by_transition_id.assert_called_once_with("SGR-43", 21)
        mock_jira.issue_add_comment.assert_called_once()


if __name__ == "__main__":
    unittest.main()
