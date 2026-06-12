# BallistiCore vendor tools

## `license_gen.py` — license key generator

Mints the license keys that unlock BallistiCore for a customer. Keys are signed
with an **Ed25519 private key that only you hold**. BallistiCore ships only the
matching public key (`BallistiCore_app/backend/app/core/license_public_key.pem`),
so keys cannot be forged from the application source.

Requires `cryptography` (already in the backend venv).

### One-time: create the keypair

```bash
python tools/license_gen.py keygen \
    --private ~/.ballisticore/license_private.pem \
    --public  BallistiCore_app/backend/app/core/license_public_key.pem
```

- **Private key** (`license_private.pem`): keep it safe and backed up, **never
  commit it**. Anyone with it can mint valid keys. (`.gitignore` already excludes
  `*license_private*.pem`.)
- **Public key** (`license_public_key.pem`): commit it into the app. Re-running
  `keygen` makes a *new* keypair that invalidates every key issued from the old
  one — only do that to rotate.

### Mint a license for a customer

```bash
python tools/license_gen.py issue \
    --private ~/.ballisticore/license_private.pem \
    --company "Acme Security" \
    --expires 2027-06-30
```

`--company` **must exactly match** the customer's configured company name (Admin →
Company Details → Company Name). BallistiCore binds the key to it; a mismatch is
treated as no licence (read-only).

### Installing a key

Save the printed token as `BallistiCore_app/backend/license.key` on the
customer's machine (override the path with the `LICENSE_FILE` env var). Restart
the backend — the startup log prints the licence state.

### Behaviour

| Situation | Result |
|---|---|
| Valid, > 14 days left | Full access |
| Valid, ≤ 14 days left | Full access + amber "expires in N days" banner |
| Valid, past expiry | Read-only + red "Subscription expired" banner |
| Missing / bad signature / company mismatch | Read-only (fail-closed) |

Read-only blocks all create/update/delete actions (Issue, Return, Add User, …);
Dashboard, History, Permits and all record views stay available.

For development you can bypass enforcement with `LICENSE_ENFORCE=false` in the
backend `.env`.
