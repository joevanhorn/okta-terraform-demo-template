# OAG (Okta Access Gateway)

This directory consolidates OAG-related scripts, documentation, and examples.

## Contents

- `docs/` — Deployment guide and API management documentation
- `examples/` — Demo application, infrastructure templates, and app configuration
- `scripts/` — OAG application management scripts

## Quick Start

1. Deploy OAG infrastructure using the examples in `examples/oag-infrastructure/`
2. Configure app definitions in a JSON config file (see `examples/oag_apps.json`)
3. Deploy apps via workflow:
   ```bash
   gh workflow run deploy-oag-app.yml -f environment=myorg -f action=deploy
   ```

See `docs/oag-deployment.md` for full setup instructions.
