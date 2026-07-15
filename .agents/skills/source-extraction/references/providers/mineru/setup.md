# MinerU Setup

MinerU is documented here through API profiles. Shared setup notes stay here; API behavior belongs to the selected profile.

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

## Security Rules

Use `.env.example` as the non-secret template. Do not store tokens or private endpoint values in `PROJECT.md`, `WIKI.md`, agent entrypoint files, manifests, logs, wiki pages, source cards, or skill files. Agents may check whether required variables are present, but must not print or persist their values.

## Upstream Documentation

Use the upstream MinerU API documentation for current limits and parameters:

- <https://mineru.net/apiManage/docs>
- <https://opendatalab.github.io/MinerU/zh/usage/quick_usage/>
