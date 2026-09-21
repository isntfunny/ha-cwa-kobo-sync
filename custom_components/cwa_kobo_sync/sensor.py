"""Sensors for CWA Kobo Sync reading data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import CwaKoboSyncCoordinator
from .entity import CwaKoboSyncEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up CWA Kobo Sync sensors."""
    coordinator: CwaKoboSyncCoordinator = entry.runtime_data
    async_add_entities(
        [
            CwaKoboCurrentBookSensor(coordinator, entry),
            CwaKoboProgressSensor(coordinator, entry),
            CwaKoboReadingTimeSensor(coordinator, entry),
            CwaKoboRemainingTimeSensor(coordinator, entry),
            CwaKoboLastSyncSensor(coordinator, entry),
        ]
    )


class CwaKoboCurrentBookSensor(CwaKoboSyncEntity, SensorEntity):
    """Current book reported as Reading by Kobo Sync."""

    _attr_icon = "mdi:book-open-page-variant"
    _attr_translation_key = "current_book"

    def __init__(self, coordinator: CwaKoboSyncCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "current_book")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.metadata.title if self.coordinator.data and self.coordinator.data.metadata else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data or not self.coordinator.data.reading:
            return {}
        reading = self.coordinator.data.reading
        metadata = self.coordinator.data.metadata
        return {
            "author": metadata.author if metadata else None,
            "book_id": reading.entitlement_id,
            "status": reading.status,
        }


class CwaKoboProgressSensor(CwaKoboSyncEntity, SensorEntity):
    """Current reading progress reported by Kobo Sync."""

    _attr_translation_key = "progress"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: CwaKoboSyncCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "progress")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.reading.progress_percent if self.coordinator.data and self.coordinator.data.reading else None


class _CwaKoboDurationSensor(CwaKoboSyncEntity, SensorEntity):
    """Base class for durations reported by Kobo Sync."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT


class CwaKoboReadingTimeSensor(_CwaKoboDurationSensor):
    """Minutes spent reading the current book."""

    _attr_translation_key = "reading_time"

    def __init__(self, coordinator: CwaKoboSyncCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "reading_time")

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.reading.reading_minutes if self.coordinator.data and self.coordinator.data.reading else None


class CwaKoboRemainingTimeSensor(_CwaKoboDurationSensor):
    """Kobo's remaining-time estimate for the current book."""

    _attr_translation_key = "remaining_time"

    def __init__(self, coordinator: CwaKoboSyncCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "remaining_time")

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.reading.remaining_minutes if self.coordinator.data and self.coordinator.data.reading else None


class CwaKoboLastSyncSensor(CwaKoboSyncEntity, SensorEntity):
    """Last time Kobo changed the current reading state."""

    _attr_translation_key = "last_sync"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: CwaKoboSyncCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "last_sync")

    @property
    def native_value(self) -> datetime | None:
        if not self.coordinator.data or not self.coordinator.data.reading:
            return None
        last_modified = self.coordinator.data.reading.last_modified
        return dt_util.parse_datetime(last_modified) if last_modified else None
