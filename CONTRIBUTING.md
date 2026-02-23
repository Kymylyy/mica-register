# Contributing

Thanks for contributing to MiCA Register.

## Development Setup

1. Create a branch from `main`.
2. Set up backend and frontend using the commands from `README.md`.
3. Implement your change in small, reviewable commits.

## Local Checks (Required)

Run these before opening a pull request:

- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`
- `python3 -m pytest`

## Pull Requests

- Keep PRs focused on one logical change.
- Include a short summary of what changed and why.
- Mention any follow-up work that is intentionally out of scope.

## Commit Style

Use Conventional Commits when possible:

- `feat:` new behavior
- `fix:` bug fix
- `docs:` documentation-only change
- `chore:` maintenance
