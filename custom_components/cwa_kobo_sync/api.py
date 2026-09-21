"""Kobo Sync protocol client and response parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiohttp

from .const import SYNC_TOKEN_HEADER


class CwaKoboSyncError(Exception):
    """Base error raised by the CWA Kobo Sync client."""


class CwaKoboSyncAuthError(CwaKoboSyncError):
    """The CWA Kobo Sync link was rejected."""


@dataclass(frozen=True)
class BookMetadata:
    """The metadata CWA includes in a Kobo entitlement."""

    title: str
    author: str | None


@dataclass(frozen=True)
class ReadingState:
    """The latest Kobo reading state for one CWA book."""

    entitlement_id: str
    status: str
    progress_percent: float | None
    reading_minutes: int | None
    remaining_minutes: int | None
    last_modified: str | None


@dataclass(frozen=True)
class KoboSyncResponse:
    """One CWA Kobo sync response plus its cursor headers."""

    results: list[dict[str, Any]]
    sync_token: str | None
    has_more: bool


def normalize_sync_url(value: str) -> str:
    """Validate a pasted CWA Kobo Sync link and return its stable base URL."""
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("The link must start with http:// or https://")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("The link must not contain credentials, a query, or a fragment")

    parts = [part for part in parsed.path.split("/") if part]
    try:
        kobo_index = parts.index("kobo")
        token = parts[kobo_index + 1]
    except (ValueError, IndexError) as err:
        raise ValueError("This is not a CWA Kobo Sync link") from err

    suffix = parts[kobo_index + 2 :]
    if not token or suffix not in ([], ["v1", "library", "sync"]):
        raise ValueError("This is not a CWA Kobo Sync link")

    return urlunsplit((parsed.scheme, parsed.netloc, f"/kobo/{token}", "", ""))


async def async_get_sync(
    session: aiohttp.ClientSession, sync_url: str, sync_token: str | None = None
) -> KoboSyncResponse:
    """Fetch one delta page from CWA's Kobo Sync endpoint."""
    headers = {SYNC_TOKEN_HEADER: sync_token} if sync_token else None
    try:
        async with session.get(
            f"{sync_url}/v1/library/sync", headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status in {401, 403}:
                raise CwaKoboSyncAuthError("CWA rejected the Kobo Sync link")
            response.raise_for_status()
            payload = await response.json(content_type=None)
            if not isinstance(payload, list):
                raise CwaKoboSyncError("CWA returned an invalid Kobo Sync response")
            return KoboSyncResponse(
                results=payload,
                sync_token=response.headers.get(SYNC_TOKEN_HEADER),
                has_more=response.headers.get("x-kobo-sync", "").casefold() == "continue",
            )
    except CwaKoboSyncError:
        raise
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        raise CwaKoboSyncError(f"Could not retrieve Kobo Sync data: {err}") from err


def apply_sync_results(
    results: list[dict[str, Any]],
    books: dict[str, BookMetadata],
    states: dict[str, ReadingState],
) -> None:
    """Merge Kobo Sync deltas into the local book and reading-state caches."""
    for item in results:
        if not isinstance(item, dict):
            continue
        entitlement = item.get("NewEntitlement") or item.get("ChangedEntitlement")
        if isinstance(entitlement, dict):
            _store_entitlement(entitlement, books, states)

        changed_state = item.get("ChangedReadingState")
        if isinstance(changed_state, dict):
            _store_reading_state(changed_state.get("ReadingState"), states)


def current_reading(
    books: dict[str, BookMetadata], states: dict[str, ReadingState]
) -> ReadingState | None:
    """Return the most recently updated book which Kobo reports as Reading."""
    candidates = [state for state in states.values() if state.status == "Reading"]
    if not candidates:
        return None
    # ISO 8601 timestamps sort lexicographically and CWA always emits UTC values.
    return max(candidates, key=lambda state: state.last_modified or "")


def _store_entitlement(
    entitlement: dict[str, Any],
    books: dict[str, BookMetadata],
    states: dict[str, ReadingState],
) -> None:
    book_entitlement = entitlement.get("BookEntitlement")
    metadata = entitlement.get("BookMetadata")
    if not isinstance(book_entitlement, dict) or not isinstance(metadata, dict):
        return

    entitlement_id = book_entitlement.get("Id") or metadata.get("EntitlementId")
    title = metadata.get("Title")
    if isinstance(entitlement_id, str) and isinstance(title, str):
        contributors = metadata.get("Contributors")
        author = ", ".join(item for item in contributors if isinstance(item, str)) if isinstance(contributors, list) else None
        books[entitlement_id] = BookMetadata(title=title, author=author or None)

    _store_reading_state(entitlement.get("ReadingState"), states)


def _store_reading_state(value: Any, states: dict[str, ReadingState]) -> None:
    if not isinstance(value, dict):
        return
    entitlement_id = value.get("EntitlementId")
    status_info = value.get("StatusInfo")
    if not isinstance(entitlement_id, str) or not isinstance(status_info, dict):
        return

    bookmark = value.get("CurrentBookmark")
    statistics = value.get("Statistics")
    progress = bookmark.get("ProgressPercent") if isinstance(bookmark, dict) else None
    reading_minutes = statistics.get("SpentReadingMinutes") if isinstance(statistics, dict) else None
    remaining_minutes = statistics.get("RemainingTimeMinutes") if isinstance(statistics, dict) else None
    states[entitlement_id] = ReadingState(
        entitlement_id=entitlement_id,
        status=str(status_info.get("Status", "")),
        progress_percent=float(progress) if isinstance(progress, int | float) else None,
        reading_minutes=reading_minutes if isinstance(reading_minutes, int) else None,
        remaining_minutes=remaining_minutes if isinstance(remaining_minutes, int) else None,
        last_modified=str(value.get("LastModified")) if value.get("LastModified") else None,
    )
