#!/usr/bin/env python3
"""
BallistiCore license key generator — ADMIN TOOL (kept by the vendor).

A license key is a compact signed token:  base64url(payload) "." base64url(sig)
The payload is canonical JSON carrying the licensed company and an expiry date.
Keys are signed with an Ed25519 private key that lives ONLY with you (never in
the app or the repo). BallistiCore ships only the matching public key, so keys
cannot be forged from the application source.

Usage
-----
  # One-time: create the keypair. Private key stays with you; public key is
  # written into the app package so BallistiCore can verify keys.
  python tools/license_gen.py keygen \
      --private ~/.ballisticore/license_private.pem \
      --public  BallistiCore_app/backend/app/core/license_public_key.pem

  # Mint a license for a customer (company must match their configured
  # company_name exactly — the app binds the key to it).
  python tools/license_gen.py issue \
      --private ~/.ballisticore/license_private.pem \
      --company "Acme Security" \
      --expires 2027-06-30

Keep the private key safe and backed up. Anyone with it can mint valid keys.
"""

import argparse
import base64
import json
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

LICENSE_VERSION = 1


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _canonical(payload: dict) -> bytes:
    # Deterministic encoding so the bytes that were signed can be reproduced
    # exactly during verification.
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def cmd_keygen(args: argparse.Namespace) -> int:
    priv_path = Path(args.private).expanduser()
    pub_path = Path(args.public).expanduser()

    if priv_path.exists() and not args.force:
        print(f"Refusing to overwrite existing private key at {priv_path} (use --force).")
        return 1

    private_key = Ed25519PrivateKey.generate()
    priv_path.parent.mkdir(parents=True, exist_ok=True)
    priv_path.write_bytes(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    try:
        priv_path.chmod(0o600)
    except OSError:
        pass  # best-effort on Windows

    pub_path.parent.mkdir(parents=True, exist_ok=True)
    pub_path.write_bytes(private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))

    print(f"Private key written to {priv_path}  (KEEP SAFE — never commit this)")
    print(f"Public  key written to {pub_path}  (commit this into the app)")
    return 0


def cmd_issue(args: argparse.Namespace) -> int:
    try:
        expires = datetime.strptime(args.expires, "%Y-%m-%d").date()
    except ValueError:
        print("--expires must be YYYY-MM-DD")
        return 1
    if expires < date.today():
        print(f"Warning: expiry {expires} is in the past — this key is already expired.")

    priv_path = Path(args.private).expanduser()
    if not priv_path.exists():
        print(f"Private key not found at {priv_path}. Run 'keygen' first.")
        return 1
    private_key = serialization.load_pem_private_key(priv_path.read_bytes(), password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        print("Private key is not an Ed25519 key.")
        return 1

    payload = {
        "v": LICENSE_VERSION,
        "company": args.company,
        "issued": date.today().isoformat(),
        "expires": expires.isoformat(),
        "license_id": str(uuid.uuid4()),
    }
    payload_bytes = _canonical(payload)
    signature = private_key.sign(payload_bytes)
    token = f"{_b64url(payload_bytes)}.{_b64url(signature)}"

    print()
    print(f"  Company : {args.company}")
    print(f"  Expires : {expires.isoformat()}")
    print(f"  License : {payload['license_id']}")
    print()
    print("License key (give this to the customer — save as backend/license.key):")
    print()
    print(token)
    print()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="BallistiCore license key generator (vendor tool).")
    sub = parser.add_subparsers(dest="command", required=True)

    pk = sub.add_parser("keygen", help="Create a new Ed25519 keypair.")
    pk.add_argument("--private", required=True, help="Where to write the private key PEM (keep safe).")
    pk.add_argument("--public", required=True, help="Where to write the public key PEM (commit into the app).")
    pk.add_argument("--force", action="store_true", help="Overwrite an existing private key.")
    pk.set_defaults(func=cmd_keygen)

    pi = sub.add_parser("issue", help="Mint a license key.")
    pi.add_argument("--private", required=True, help="Path to the private key PEM.")
    pi.add_argument("--company", required=True, help="Licensed company name (must match the customer's company_name).")
    pi.add_argument("--expires", required=True, help="Expiry date, YYYY-MM-DD.")
    pi.set_defaults(func=cmd_issue)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
