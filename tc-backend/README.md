# RDB backend

## Environment variables

- `TC_METAHUB` — MetaHub service host (default: `localhost:8033`)
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` / `POSTGRES_HOST` / `POSTGRES_PORT`
- `KC_SERVER_URL` / `KC_REALM` / `KC_CLIENT_ID` — Keycloak connection

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
