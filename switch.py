"""Switch platform for Helty VMC."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CMD_LED_OFF, CMD_LED_ON, CMD_SENSORS_OFF, CMD_SENSORS_ON, CONF_NAME, DOMAIN
from .coordinator import HeltyVMCCoordinator
from .protocol import HeltyVMCProtocol

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helty VMC switches."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HeltyVMCCoordinator = data["coordinator"]
    protocol: HeltyVMCProtocol = data["protocol"]
    name = entry.data.get(CONF_NAME, "Helty VMC")

    async_add_entities([
        HeltyVMCLedSwitch(coordinator, protocol, entry, name),
        HeltyVMCSensorsSwitch(coordinator, protocol, entry, name),
    ])


class HeltyVMCLedSwitch(CoordinatorEntity[HeltyVMCCoordinator], SwitchEntity):
    """Switch for LED panel."""

    _attr_has_entity_name = True
    _attr_translation_key = "led_panel"
    _attr_icon = "mdi:led-on"

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        protocol: HeltyVMCProtocol,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._protocol = protocol
        self._attr_unique_id = f"{entry.entry_id}_led_panel"
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
        """Return true if LED is on."""
        if self.coordinator.status:
            return self.coordinator.status.led_on
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the LED."""
        await self._protocol.send_raw_command(CMD_LED_ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the LED."""
        await self._protocol.send_raw_command(CMD_LED_OFF)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class HeltyVMCSensorsSwitch(CoordinatorEntity[HeltyVMCCoordinator], SwitchEntity):
    """Switch for sensors."""

    _attr_has_entity_name = True
    _attr_translation_key = "sensors"
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        protocol: HeltyVMCProtocol,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._protocol = protocol
        self._attr_unique_id = f"{entry.entry_id}_sensors"
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
        """Return true if sensors are on."""
        if self.coordinator.status:
            return self.coordinator.status.sensors_on
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the sensors."""
        await self._protocol.send_raw_command(CMD_SENSORS_ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the sensors."""
        await self._protocol.send_raw_command(CMD_SENSORS_OFF)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
