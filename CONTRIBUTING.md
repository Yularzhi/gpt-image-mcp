# Contributing

Thanks for helping improve GPT Image MCP.

## Workflow

1. Create a branch.
2. Make focused changes.
3. Run tests before opening a pull request.
4. Update docs when behavior changes.

## Verification

```bash
python3 -m unittest discover -s tests -p "test*.py" -v
```

If available:

```bash
ruff check app tests
pytest -q
```

## Style

- Keep public MCP tool names stable.
- Preserve `/mcp/`, `/health`, and `/images/{filename}`.
- Prefer small, reviewable changes.
- Update both `README.md` and `README.ru.md` when user-facing behavior changes.
