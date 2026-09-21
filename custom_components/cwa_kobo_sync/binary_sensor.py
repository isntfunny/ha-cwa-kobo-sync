"""Binary sensors for CWA Kobo Sync."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CwaKoboSyncCoordinator
from .entity import CwaKoboSyncEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up CWA Kobo Sync binary sensors."""
    coordinator: CwaKoboSyncCoordinator = entry.runtime_data
    async_add_entities([CwaKoboReadingSensor(coordinator, entry)])


class CwaKoboReadingSensor(CwaKoboSyncEntity, BinarySensorEntity):
    """Whether Kobo Sync currently reports a book as Reading."""

    _attr_translation_key = "reading"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: CwaKoboSyncCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "reading")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.reading)
