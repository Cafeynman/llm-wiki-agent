# MinerU API Reference

Use this reference only when MinerU API mode, API smoke checks, or endpoint details are relevant. Keep `usage.md` as the provider-selection and wiki-intake contract.

Upstream documentation:

- <https://mineru.net/apiManage/docs>
- <https://opendatalab.github.io/MinerU/zh/usage/quick_usage/>

Check the upstream documentation before changing endpoint names, request parameters, limits, or response handling. This file records the provider workflow used by this package; the upstream documentation remains the source of truth for current API behavior.

## User Link Policy

When MinerU API configuration is missing, invalid, or rejected, send the user the selected profile's documentation link so they can view setup instructions or verify the active deployment contract.

Do not ask the user to paste secrets into chat. Ask them to copy `.env.example` to `.env` in the project root and fill only the variables required by the selected profile.

When an API request returns an error that appears to be caused by an invalid token, expired access, endpoint drift, permission limits, or deployment health, include the selected profile documentation link in the user-facing message and ask the user to verify the local configuration or current API instructions there.

## API Profiles

For implemented API profile paths, use:

- `profiles/public-api.md`
- `profiles/fastapi.md`

Each profile owns its active route family, request examples, documented limits, smoke-check entrypoint, and local upload parse script. This file remains a narrow reference and link surface, not the primary home for the profile contract.

## Smoke Checks

Run the smoke check defined by the active profile before the first API extraction in a workspace. The route family, request shape, credential requirement, success meaning, and failure handling belong to the active profile.

## Extraction Boundary

When the user later asks for real API parsing, start from the original source path and follow `usage.md` plus the selected profile. Record provider profile, batch id or task id, model version, warnings, missing content, and result URLs in the intake manifest or review notes. The API result still must be normalized into the WIKI intake output contract before Source Review Gate.
