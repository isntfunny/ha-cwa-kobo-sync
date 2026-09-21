"""Shared entities for CWA Kobo Sync."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CwaKoboSyncCoordinator


class CwaKoboSyncEntity(CoordinatorEntity[CwaKoboSyncCoordinator]):
    """Base entity for the CWA Kobo Sync device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CwaKoboSyncCoordinator, entry: ConfigEntry, key: str) -> None:
        """Initialize a CWA Kobo Sync entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="CWA Kobo Sync",
            manufacturer="Calibre-Web Automated",
            model="Kobo Sync",
        )
