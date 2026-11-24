"""Shared secure TLS context for outbound provider requests.

On managed Windows networks, the system trust store may contain an approved
inspection proxy root that certifi does not know about. truststore bridges the
OS trust store to Python. An explicit PEM bundle can be supplied with
CAMPUSFIX_CA_BUNDLE. Certificate verification is never disabled.
"""
from __future__ import annotations
import os, ssl
from pathlib import Path
from .config import settings

def provider_ssl_context() -> ssl.SSLContext:
    try:
        from .config import settings
        configured = settings.campusfix_ca_bundle
    except Exception:
        configured = ""
    bundle = (configured or os.getenv("CAMPUSFIX_CA_BUNDLE", "")).strip()
    if bundle:
        path = Path(bundle).expanduser()
        if not path.is_file():
            raise RuntimeError(f"CAMPUSFIX_CA_BUNDLE does not exist: {path}")
        context = ssl.create_default_context()
        context.load_verify_locations(cafile=str(path))
        return context
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        return ssl.create_default_context()
