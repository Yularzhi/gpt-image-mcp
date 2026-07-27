# Security Policy

## Supported versions

The latest `main` branch is considered supported.

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report issues privately through the GitHub security tab or the maintainers' preferred private channel.

## Operational guidance

- Keep `OPENAI_API_KEY` private.
- Use `MCP_API_KEY` when exposing the service outside a trusted network.
- Prefer HTTPS in front of the service.
- Restrict `PUBLIC_URL` to the actual public hostname that serves images.
