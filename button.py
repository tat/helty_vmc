"""Button platform for Helty VMC."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_LED_OFF,
    CMD_LED_ON,
    CMD_RESET_FILTER,
    CMD_SET_FREE_COOLING,
    CMD_SET_NIGHT,
    CMD_SET_BOOST,
    CMD_SET_SPEED_0,
    CMD_SET_SPEED_1,
    CMD_SET_SPEED_2,
    CMD_SET_SPEED_3,
    CMD_SET_SPEED_4,
    CONF_NAME,
    DOMAIN,
)
from .coordinator import HeltyVMCCoordinator
from .protocol import HeltyVMCProtocol

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class HeltyVMCButtonDescription(ButtonEntityDescription):
    """Describes a Helty VMC button."""

    command: str


BUTTON_DESCRIPTIONS: tuple[HeltyVMCButtonDescription, ...] = (
    HeltyVMCButtonDescription(
        key="speed_0",
        translation_key="speed_0",
        icon="mdi:fan-off",
        command=CMD_SET_SPEED_0,
    ),
    HeltyVMCButtonDescription(
        key="speed_1",
        translation_key="speed_1",
        icon="mdi:fan-speed-1",
        command=CMD_SET_SPEED_1,
    ),
    HeltyVMCButtonDescription(
        key="speed_2",
        translation_key="speed_2",
        icon="mdi:fan-speed-2",
        command=CMD_SET_SPEED_2,
    ),
    HeltyVMCButtonDescription(
        key="speed_3",
        translation_key="speed_3",
        icon="mdi:fan-speed-3",
        command=CMD_SET_SPEED_3,
    ),
    HeltyVMCButtonDescription(
        key="speed_4",
        translation_key="speed_4",
        icon="mdi:fan",
        command=CMD_SET_SPEED_4,
    ),
    HeltyVMCButtonDescription(
        key="boost",
        translation_key="boost",
        icon="mdi:fan-plus",
        command=CMD_SET_BOOST,
    ),
    HeltyVMCButtonDescription(
        key="night_mode",
        translation_key="night_mode",
        icon="mdi:weather-night",
        command=CMD_SET_NIGHT,
    ),
    HeltyVMCButtonDescription(
        key="free_cooling",
        translation_key="free_cooling",
        icon="mdi:snowflake",
        command=CMD_SET_FREE_COOLING,
    ),
    HeltyVMCButtonDescription(
        key="led_on",
        translation_key="led_on",
        icon="mdi:led-on",
        command=CMD_LED_ON,
    ),
    HeltyVMCButtonDescription(
        key="led_off",
        translation_key="led_off",
        icon="mdi:led-off",
        command=CMD_LED_OFF,
    ),
    HeltyVMCButtonDescription(
        key="reset_filter",
        translation_key="reset_filter",
        icon="mdi:air-filter",
        command=CMD_RESET_FILTER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helty VMC buttons."""
    data = hass.data[DOMAIN][entry.entry_id]
    protocol: HeltyVMCProtocol = data["protocol"]
    coordinator: HeltyVMCCoordinator = data["coordinator"]
    name = entry.data.get(CONF_NAME, "Helty VMC")

    entities = [
        HeltyVMCButton(protocol, coordinator, entry, name, description)
        for description in BUTTON_DESCRIPTIONS
    ]

    async_add_entities(entities)


class HeltyVMCButton(ButtonEntity):
    """Button to control Helty VMC."""

    _attr_has_entity_name = True
    entity_description: HeltyVMCButtonDescription

    def __init__(
        self,
        protocol: HeltyVMCProtocol,
        coordinator: HeltyVMCCoordinator,
        entry: ConfigEntry,
        name: str,
        description: HeltyVMCButtonDescription,
    ) -> None:
        """Initialize the button."""
        self._protocol = protocol
        self._coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
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

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._protocol.send_raw_command(self.entity_description.command)
        # Refresh state after command
        await self._coordinator.async_request_refresh()
