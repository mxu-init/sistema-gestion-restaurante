# sistema-gestion-restaurante

## Commit Guidelines

This repository is protected by a **commit guardian** built on
[pre-commit](https://pre-commit.com/). The guardian runs locally on every
`git commit` and **rejects** any message that does not follow the rules below,
so the history stays consistent and written in English.

### Install the guardian (once per local clone)

```bash
pip install pre-commit
pre-commit install
```

### Message format

```
<type>(<scope>): <subject written in English, lowercase start, max 100 chars>
```

| Rule | Detail |
| --- | --- |
| Format | Conventional Commits: `type(scope): subject` |
| Types | `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test` |
| Subject | lowercase start, no trailing period, no trailing whitespace, max **100** characters |
| Body | optional; separated from the subject by a blank line, max **100** characters per line (trailers such as `Signed-off-by:` are exempt) |
| Language | **English only**: Spanish words and accented characters (`á é í ó ú ü ñ ¿ ¡`) are rejected |
| Scope | optional, lowercase kebab-case (`auth`, `db`, `api-endpoints`) |
| Skips | git-generated `Merge ...` / `Revert "..."` messages are accepted as-is |

### Examples

**Accepted**

```bash
git commit -m "feat(auth): add login endpoint"
git commit -m "fix(db): correct nullable column"
git commit -m "docs: update installation guide"
```

**Rejected**

```bash
git commit -m "first commit"
git commit -m "feat: Add users."
git commit -m "fix: corrección del login"
git commit -m "arreglo: cosa rara"
```

### Validate a message manually

```bash
pre-commit run commit-msg --hook-stage commit-msg --commit-msg-filename path/to/message.txt
```

The guardian itself lives in [`scripts/check_commit_msg.py`](scripts/check_commit_msg.py)
and its configuration in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

