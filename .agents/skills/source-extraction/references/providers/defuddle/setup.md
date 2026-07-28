# Defuddle Setup

Defuddle is a CLI for extracting clean Markdown from web pages.

The tested version for this package is `0.19.2`.

## Preflight

```bash
defuddle --version
```

If the command is missing:

1. Run `node --version` and `npm --version`.
2. Tell the user that the exact command below changes the current user's global npm packages and request approval.
3. After approval, run the command yourself; do not ask the user to run it:

```bash
npm install -g defuddle@0.19.2
```

If Node.js or npm is missing, or installation fails, report the missing command or failed operation and stop. Do not silently switch providers. If another Defuddle version is already installed, report it and obtain approval before changing it.

## Verify

```bash
defuddle --version
defuddle parse --help
defuddle parse <temporary-smoke.html> --json
```

Parse the smoke-test JSON structurally and require a non-empty `contentMarkdown` string. Remove only the temporary smoke-test files after verification.

Defuddle does not require project API keys by default. Use it only for public, non-sensitive webpages; asynchronous extraction may use third-party services when local page content is empty.
