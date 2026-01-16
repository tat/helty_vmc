"""Fan platform for Helty VMC."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN, SPEED_COMMANDS
from .coordinator import HeltyVMCCoordinator
from .protocol import HeltyVMCProtocol

_LOGGER = logging.getLogger(__name__)

PRESET_MODES = ["speed_1", "speed_2", "speed_3", "speed_4", "boost", "night", "free_cooling"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Helty VMC fan."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HeltyVMCCoordinator = data["coordinator"]
    protocol: HeltyVMCProtocol = data["protocol"]
    name = entry.data.get(CONF_NAME, "Helty VMC")

    async_add_entities([HeltyVMCFan(coordinator, protocol, entry, name)])


class HeltyVMCFan(CoordinatorEntity[HeltyVMCCoordinator], FanEntity):
    """Representation of the Helty VMC fan."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        protocol: HeltyVMCProtocol,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the fan."""
        super().__init__(coordinator)
        self._protocol = protocol
        self._attr_unique_id = f"{entry.entry_id}_fan"
        self._attr_preset_modes = PRESET_MODES
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
        """Return true if the fan is on."""
        if self.coordinator.status:
            return self.coordinator.status.speed > 0
        return None

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if self.coordinator.status:
            mode = self.coordinator.status.speed_mode
            return mode if mode in PRESET_MODES else None
        return None

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        if self.coordinator.status:
            speed = self.coordinator.status.speed
            if speed == 0:
                return 0
            # Map speeds 1-4 to 25-100%, special modes to 100%
            if speed <= 4:
                return speed * 25
            return 100
        return None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
        elif percentage:
            # Map percentage to speed 1-4
            speed = max(1, min(4, (percentage + 24) // 25))
            command = SPEED_COMMANDS.get(f"speed_{speed}")
            if command:
                await self._protocol.send_raw_command(command)
                await self.coordinator.async_request_refresh()
        else:
            # Default to speed 2
            await self._protocol.send_raw_command(SPEED_COMMANDS["speed_2"])
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._protocol.send_raw_command(SPEED_COMMANDS["off"])
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        command = SPEED_COMMANDS.get(preset_mode)
        if command:
            await self._protocol.send_raw_command(command)
            await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
