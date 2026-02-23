# Security Policy

## Reporting a Vulnerability

Do not open a public GitHub issue for security problems.

Please report vulnerabilities privately to the repository owner with:

- a short description
- reproduction steps or proof of concept
- impact assessment
- suggested remediation (optional)

## Secrets Handling

- Never commit secrets (`.env`, API keys, tokens, database credentials).
- Use platform secret stores (Railway/Vercel/GitHub Secrets).
- Rotate any key immediately if exposure is suspected.

## Scope Notes

This repository includes data snapshots from external public sources. Before redistribution, validate licensing and data-use constraints for your jurisdiction and use case.
