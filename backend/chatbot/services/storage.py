"""Supabase Storage service for Nexus.

Uploads files (PDF, DOC, DOCX, ZIP) to a Supabase Storage bucket using the
Storage REST API. Implemented with Python's stdlib ``urllib`` only — no
third-party HTTP client is required, so no new dependencies are added to
requirements.txt.

Authentication
--------------
Supabase has two key formats in circulation:

1. **Legacy JWT** (starts with ``eyJ``):
   Sent both as ``apikey`` and as ``Authorization: Bearer <jwt>``.

2. **New secret keys** (starts with ``sb_secret_``):
   Opaque tokens, NOT JWTs. Sent **only** in the ``apikey`` header.

Sending a secret key as ``Authorization: Bearer <sb_secret_...>`` makes
Storage parse it as a JWS compact serialization and fail with::

    HTTP 400 {"message": "Invalid Compact JWS", "code": "AccessDenied"}

Verified directly against the Supabase Storage REST API::

    apikey only                            -> 200 OK
    apikey + Authorization: Bearer <sb_secret_>  -> 200 OK (apikey wins)
    Authorization: Bearer <sb_secret_> only      -> 400 Invalid Compact JWS

Because a request that reaches Storage without a usable ``apikey`` (or through
any path that only sets ``Authorization``) produces that 400, this service
sends the ``apikey`` header **always** and adds ``Authorization`` **only** for
legacy JWT keys — a secret key is never placed in a Bearer token.

The secret stays on the Django backend in ``SUPABASE_SERVICE_ROLE_KEY`` (an
environment variable); it is never sent to the frontend.

API reference:
  POST /storage/v1/object/{bucket}/{object_path}
  Headers:
    apikey:        <service_role_key>      (always)
    Authorization: Bearer <jwt>             (legacy JWT keys only)
    Content-Type:  <content type of the file>
    x-upsert:      false

Object path
-----------
``upload_file()`` returns the object key *inside* the bucket, e.g.
``university/a1b2c3-guidelines.pdf``. The bucket name lives in the URL only,
so it is never duplicated in the key::

    Supabase Storage
    └── documents (bucket)
        ├── university/uuid-name.pdf
        └── student/uuid-name.zip

Usage::

    from chatbot.services.storage import StorageService, StorageError

    service = StorageService.from_settings()
    storage_path = service.upload_file(
        file_bytes, original_name, source, content_type="application/zip"
    )
    # Returns e.g. "university/a1b2c3-guidelines.zip"
"""

from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    pass


class StorageError(Exception):
    """Raised when a Supabase Storage operation fails."""


class StorageService:
    """Thin wrapper around the Supabase Storage REST API."""

    def __init__(self, url: str, service_role_key: str, bucket: str) -> None:
        if not url:
            raise StorageError(
                "SUPABASE_URL is not configured. "
                "Add it to your .env file (see .env.example)."
            )
        if not service_role_key:
            raise StorageError(
                "SUPABASE_SERVICE_ROLE_KEY is not configured. "
                "Add it to your .env file (see .env.example)."
            )
        self._url = url.rstrip("/")
        self._key = service_role_key
        self._bucket = bucket

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_settings(cls) -> "StorageService":
        """Build a StorageService from Django settings."""
        return cls(
            url=getattr(settings, "SUPABASE_URL", ""),
            service_role_key=getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", ""),
            bucket=getattr(settings, "SUPABASE_STORAGE_BUCKET", "documents"),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload_file(
        self,
        file_bytes: bytes,
        original_name: str,
        source: str,
        content_type: str | None = None,
    ) -> str:
        """Upload a file and return its object key inside the bucket.

        The key is structured as::

            {source}/{uuid4}-{original_name}

        The bucket (``documents``) is already part of the request URL, so it
        is not repeated in the key.

        A UUID prefix prevents filename collisions even when two students
        upload a file with the same name.

        The file is stored exactly as received — no preprocessing, parsing or
        conversion happens here.

        Args:
            file_bytes: Raw file bytes read from the uploaded file.
            original_name: The user's original filename (stored for reference).
            source: Either ``"university"`` or ``"student"``.
            content_type: MIME type stored with the object (e.g.
                ``"application/zip"``). Guessed from the extension when the
                caller does not supply one.

        Returns:
            The storage key (e.g. ``"student/abc-thesis.pdf"``), as stored in
            ``Document.file_path``.

        Raises:
            StorageError: If the Supabase API returns a non-2xx status.
        """
        unique_prefix = uuid.uuid4().hex[:12]
        # Sanitise the original name so it is safe in a URL path.
        safe_name = _safe_filename(original_name)
        # Bucket is added by the URL below — do not repeat it in the key.
        object_path = f"{source}/{unique_prefix}-{safe_name}"

        upload_url = _object_url(self._url, self._bucket, object_path)

        req = urllib.request.Request(
            url=upload_url,
            data=file_bytes,
            method="POST",
            headers=_auth_headers(self._key, extra={
                "Content-Type": content_type or _guess_content_type(original_name),
                # x-upsert: false — fail if the key already exists (the UUID
                # prefix makes this practically impossible, but we stay safe).
                "x-upsert": "false",
            }),
        )

        try:
            with urllib.request.urlopen(req) as response:
                # Supabase returns 200 on success with {"Key": "..."}.
                _body = response.read()  # consume body to free the connection
        except urllib.error.HTTPError as exc:
            # Read the error body for a useful message.
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
                detail = json.loads(error_body).get("message", error_body)
            except Exception:
                detail = str(exc)
            raise StorageError(
                f"Supabase Storage upload failed (HTTP {exc.code}): {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise StorageError(
                f"Supabase Storage is unreachable: {exc.reason}"
            ) from exc

        return object_path

    def delete_object(self, object_path: str) -> None:
        """Delete an object by its storage path (best-effort cleanup).

        Silently ignores 404s (object already gone). Raises StorageError on
        other failures.
        """
        delete_url = _object_url(self._url, self._bucket, object_path)

        req = urllib.request.Request(
            url=delete_url,
            method="DELETE",
            headers=_auth_headers(self._key),
        )

        try:
            with urllib.request.urlopen(req) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return  # Already gone — nothing to clean up.
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
                detail = json.loads(error_body).get("message", error_body)
            except Exception:
                detail = str(exc)
            raise StorageError(
                f"Supabase Storage delete failed (HTTP {exc.code}): {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise StorageError(
                f"Supabase Storage is unreachable during delete: {exc.reason}"
            ) from exc


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _auth_headers(key: str, extra: dict | None = None) -> dict:
    """Return the authentication headers required by Supabase Storage.

    Supabase has two key formats:

    * Legacy JWT (``eyJ...``) — must be sent as ``Authorization: Bearer <jwt>``
      and as ``apikey``.
    * New secret keys (``sb_secret_...``) — opaque tokens sent **only** via the
      ``apikey`` header. Putting one in a Bearer token makes Storage parse it
      as a JWS and answer::

          HTTP 400 {"message": "Invalid Compact JWS"}

    ``apikey`` is therefore always present (it is the header Storage
    authenticates against), while ``Authorization`` is added only for legacy
    JWT keys. The secret key itself never leaves the backend.

    Args:
        key: The Supabase service-role key from the environment.
        extra: Additional request headers (Content-Type, x-upsert, ...).

    Returns:
        The header dictionary for the request.
    """
    headers: dict = {"apikey": key}

    # Only legacy JWT keys are valid Bearer tokens.
    if key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {key}"

    if extra:
        headers.update(extra)
    return headers


def _guess_content_type(name: str) -> str:
    """Best-effort MIME type for a filename.

    Callers should normally pass an explicit ``content_type`` (the upload
    endpoint derives it from ``EXTENSION_CONTENT_TYPES``); this is only the
    fallback for callers that do not.
    """
    guessed, _ = mimetypes.guess_type(name)
    return guessed or "application/octet-stream"


def _object_url(base_url: str, bucket: str, object_path: str) -> str:
    """Build the Storage REST URL for one object key.

    The key is percent-encoded so the request URL stays pure ASCII: ``urllib``
    refuses to emit any other encoding — without this, a stray non-ASCII
    character dies with ``UnicodeEncodeError: 'ascii' codec can't encode
    character`` in ``http.client`` before reaching Supabase. Supabase decodes
    the path, so the stored object key never changes; ASCII keys are sent
    byte-for-byte as before.
    """
    quoted_path = urllib.parse.quote(object_path, safe="/")
    return f"{base_url}/storage/v1/object/{bucket}/{quoted_path}"


def _safe_filename(name: str) -> str:
    """Return an ASCII-safe version of a filename.

    Supabase Storage rejects non-ASCII object keys with
    ``HTTP 400 Invalid key: ...`` — even when the request URL is correctly
    percent-encoded — so accents are transliterated first
    (``Mémoire.pdf`` -> ``Memoire.pdf``), then whitespace and most special
    characters become underscores while the extension, dots, hyphens and
    alphanumerics are kept. Only the *storage key* is ASCII: the original
    name is what ``Document.file_name`` stores and the UI displays.
    """
    import re
    import unicodedata

    # NFKD decomposition + drop combining marks: é -> e, ç -> c, ỡ -> o, ...
    ascii_name = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    )
    # Keep only safe characters.
    safe = re.sub(r"[^\w.\-]", "_", ascii_name)
    # Collapse consecutive underscores.
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_") or "document.pdf"
