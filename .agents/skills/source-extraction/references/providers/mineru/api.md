# MinerU API Reference

Use this reference only when MinerU API mode, API smoke checks, or endpoint details are relevant. Keep `usage.md` as the provider-selection and wiki-intake contract.

Upstream documentation:

- <https://mineru.net/apiManage/docs>

Check the upstream documentation before changing endpoint names, request parameters, limits, or response handling. This file records the provider workflow used by this package; the upstream documentation remains the source of truth for current API behavior.

## User Link Policy

When MinerU API configuration is missing, invalid, or rejected, send the user the upstream API management documentation link so they can view setup instructions, apply for access, or regenerate the API key:

- <https://mineru.net/apiManage/docs>

Do not ask the user to paste secrets into chat. Ask them to copy `.env.example` to `.env` in the project root and fill only the variables required by the selected profile.

When an API request returns an error that appears to be caused by an invalid token, expired access, endpoint drift, or permission limits, include the same link in the user-facing message and ask the user to verify the key or current API instructions there.

## Public API Profile

For the implemented API profile path, use:

- `profiles/public-api.md`

That profile owns the active route family, request examples, documented limits, smoke-check entrypoint, and the local upload parse script. This file remains a narrow reference and link surface, not the primary home for the profile contract.

## Smoke Checks

Run the smoke check defined by the active profile before the first API extraction in a workspace. The route family, request shape, credential requirement, success meaning, and failure handling belong to the active profile.

## Extraction Boundary

When the user later asks for real API parsing, start from the original source path and follow `usage.md` plus the selected profile. Record provider profile, batch id or task id, model version, warnings, missing content, and result URLs in the intake manifest or review notes. The API result still must be normalized into the WIKI intake output contract before Source Review Gate.
