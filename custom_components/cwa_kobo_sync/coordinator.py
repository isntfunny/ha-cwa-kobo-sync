"""Coordinator for CWA Kobo Sync reading data."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BookMetadata, ReadingState, apply_sync_results, async_get_sync, current_reading
from .const import CONF_SYNC_URL, DEFAULT_SCAN_INTERVAL, DOMAIN, MAX_SYNC_PAGES

_LOGGER = logging.getLogger(__name__)

CwaKoboSyncConfigEntry = ConfigEntry


@dataclass(frozen=True)
class KoboReadingData:
    """Current reading data exposed by the coordinator."""

    reading: ReadingState | None
    metadata: BookMetadata | None


class CwaKoboSyncCoordinator(DataUpdateCoordinator[KoboReadingData]):
    """Poll and cache the CWA Kobo Sync delta feed."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._sync_url = entry.data[CONF_SYNC_URL]
        self._session = async_get_clientsession(hass)
        self._sync_token: str | None = None
        self._books: dict[str, BookMetadata] = {}
        self._states: dict[str, ReadingState] = {}

    async def _async_update_data(self) -> KoboReadingData:
        """Fetch all available Kobo Sync deltas and select the current book."""
        token = self._sync_token
        try:
            for _ in range(MAX_SYNC_PAGES):
                response = await async_get_sync(self._session, self._sync_url, token)
                apply_sync_results(response.results, self._books, self._states)
                token = response.sync_token or token
                if not response.has_more:
                    break
            else:
                raise UpdateFailed("CWA returned too many Kobo Sync pages")
        except Exception as err:
            if isinstance(err, UpdateFailed):
                raise
            raise UpdateFailed(str(err)) from err

        self._sync_token = token
        reading = current_reading(self._books, self._states)
        return KoboReadingData(
            reading=reading,
            metadata=self._books.get(reading.entitlement_id) if reading else None,
        )
