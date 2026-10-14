# Resource Database (RDB)

A team-oriented data asset manager built around a MetaHub tag service and a
TemplateClient (TC) storage/presentation layer. Store lightweight, structured
content, organise it with multi-dimensional hierarchical tags, and query or
aggregate across content types.

## Repository layout

| Path | Description |
|---|---|
| `tc-backend/` | TemplateClient backend — FastAPI + PostgreSQL |
| `tc-frontend/` | TemplateClient frontend — Svelte 5 + TypeScript |
| `mh-backend/` | MetaHub backend — tag management |
| `mh-frontend/` | MetaHub frontend |
| `docs/` | Design goals |
| `Dockerfile.tc`, `entrypoint.sh` | Container build/run for TemplateClient |

The Python projects form a uv workspace (`pyproject.toml`); the frontend
projects form a pnpm workspace (`pnpm-workspace.yaml`).
