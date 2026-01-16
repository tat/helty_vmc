"""Binary sensor platform for Helty VMC."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import HeltyVMCCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helty VMC binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HeltyVMCCoordinator = data["coordinator"]
    name = entry.data.get(CONF_NAME, "Helty VMC")

    async_add_entities([
        HeltyVMCFilterWarningSensor(coordinator, entry, name),
        HeltyVMCOnlineSensor(coordinator, entry, name),
    ])


class HeltyVMCFilterWarningSensor(CoordinatorEntity[HeltyVMCCoordinator], BinarySensorEntity):
    """Binary sensor for filter warning."""

    _attr_has_entity_name = True
    _attr_translation_key = "filter_warning"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:air-filter"

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_filter_warning"
        self._name = name
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._name,
            manufacturer="Helty",
            model="Flow Plus/Elite",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if filter warning is active."""
        if self.coordinator.status:
            return self.coordinator.status.led_filter_warning
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class HeltyVMCOnlineSensor(CoordinatorEntity[HeltyVMCCoordinator], BinarySensorEntity):
    """Binary sensor for device online status."""

    _attr_has_entity_name = True
    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:lan-connect"

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_online"
        self._name = name
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._name,
            manufacturer="Helty",
            model="Flow Plus/Elite",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if device is online."""
        if self.coordinator.status:
            return self.coordinator.status.is_online
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
