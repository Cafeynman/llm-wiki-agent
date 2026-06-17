# MinerU Setup

MinerU may be used through multiple runtime paths. Shared setup notes stay here; API behavior belongs to the selected profile.

## API Profiles

If `PROJECT.md` records:

```md
- MinerU profile: public-api
```

use the profile reference here:

- `profiles/public-api.md`

If `PROJECT.md` records:

```md
- MinerU profile: fastapi
```

use the profile reference here:

- `profiles/fastapi.md`

Each profile owns:

- required environment variables
- API endpoints
- documented limits
- smoke-check path
- local upload parse script

## CLI

The repository still supports the `mineru-open-api` CLI for other MinerU paths.

Install or update the CLI with the upstream installer for the current platform:

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

Verify the installed command:

```bash
mineru-open-api version
```

## Security Rules

Use `.env.example` as the non-secret template. Do not store tokens or private endpoint values in `PROJECT.md`, `WIKI.md`, `AGENTS.md`, `CLAUDE.md`, manifests, logs, wiki pages, source cards, or skill files. Agents may check whether required variables are present, but must not print or persist their values.

## Upstream Documentation

Use the upstream MinerU CLI and API documentation for current limits and parameters:

- <https://github.com/opendatalab/MinerU-Ecosystem/tree/main/cli>
- <https://mineru.net/apiManage/docs>
- <https://opendatalab.github.io/MinerU/zh/usage/quick_usage/>
