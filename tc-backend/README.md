# RDB backend

## Environment variables

- `TC_METAHUB` — MetaHub service host (default: `localhost:8033`)
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` / `POSTGRES_HOST` / `POSTGRES_PORT`
- `KC_SERVER_URL` / `KC_REALM` / `KC_CLIENT_ID` — Keycloak connection
- `TC_STORAGE_ROOT` — directory for uploaded file bytes (default: `./storage`)
- `TC_MAX_UPLOAD_MB` — maximum upload size in MB (default: `25`)

---

## Stored files

Uploads are written under `TC_STORAGE_ROOT` in a per-module subfolder
(`{TC_STORAGE_ROOT}/{data_type}/...`), with metadata in the `files` table
(see `tc/db/02-file-schema.sql`). Use `POST /api/files?data_type=...`
(multipart `file`), then reference the returned id from node content via a
`file_id` field; files are linked to the node on save and inherit its
visibility. `GET /api/files/{id}` and `GET /api/files/{id}/thumb` serve the
bytes.

---

## Cross-type retrieval & aggregation

Content stays in `nodes.content` (JSONB) untouched, but every write also
projects declared fields into the `node_fields` index (see
`tc/db/03-index-schema.sql`), which the app applies on startup. Declared
fields are described per type in `tc/types/registry.py` and mapped onto
canonical, shareable keys so values from different types can be compared.

- `GET /api/types` — registered type descriptors (fields, preview, ui).
- `GET /api/nodes/fields` — the shared field-key vocabulary.
- `GET /api/nodes/fields/{key}/values` — facets for a keyword key, or
  min/max/count for a numeric key.
- `POST /api/nodes/query` — cross-type search/filter over text, tags,
  types and field conditions.
- `POST /api/nodes/aggregate` — group numeric metrics by field keys and/or
  tags.
- `GET /api/nodes/data?ids=a,b,c` — batch content fetch.
- `POST /api/admin/reindex` — rebuild projections (and upcast content)
  for all nodes; requires `nodes:edit_any`.

Adding a type is code-only: define a `TypeDescriptor` in
`tc/types/registry.py` and (optionally) register a frontend renderer via
`ui.component`.

---

## Role-based access control

All authorization is driven by Keycloak roles. The backend reads roles from both **Realm roles** and **Client roles** under `resource_access.{KC_CLIENT_ID}`, merging them into a single set.

### Built-in action roles

| Role | Effect |
|---|---|
| `nodes:create` | Create new nodes |
| `nodes:read_all` | See all nodes regardless of visibility |
| `nodes:edit_any` | Edit any node (bypasses creator check) |
| `nodes:review` | Change node status (draft / pending_review / published / archived) |

**Owner fallback:** a node's creator can always edit and see their own nodes, even without the roles above.

### Visibility roles

Each node has a `visibility` field (default: `"public"`). To control who can see non-public nodes, create roles following the pattern:

```
nodes:visibility:{name}
```

Examples:

| Role | Effect |
|---|---|
| `nodes:visibility:internal` | See nodes with `visibility: "internal"` |
| `nodes:visibility:proj_a` | See nodes with `visibility: "proj_a"` |
| `nodes:visibility:proj_b` | See nodes with `visibility: "proj_b"` |

**Visibility rules** for read endpoints (list, search, get single node):

1. `nodes:read_all` → sees everything
2. `visibility == "public"` → everyone sees
3. `nodes:visibility:{x}` in user's roles → sees nodes with `visibility: "{x}"`
4. Creator of the node → always sees their own

Unauthenticated users can only see `public` nodes.

### Setting up in Keycloak

Example: a project setup with `proj_a` and `proj_b`:

**Realm roles** (Realm → Roles):
- `nodes:create`
- `nodes:visibility:proj_a`
- `nodes:visibility:proj_b`

**Client roles** (Clients → your-app → Roles):
- `admin` — associate: `nodes:read_all`, `nodes:create`, `nodes:edit_any`, `nodes:review`
- `member_proj_a` — associate: `nodes:create`, `nodes:visibility:proj_a`

Assign `member_proj_a` to users who should create nodes and see `proj_a` resources.

### Downstream customization

If you run your own instance with a different Keycloak client, just create the same role names. The backend does not have a hardcoded role list — any role matching the pattern `nodes:*` or `nodes:visibility:*` is honored.
