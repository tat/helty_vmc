"""Sensor platform for Helty VMC."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import AIRFLOW_RATES, CONF_NAME, DOMAIN
from .coordinator import HeltyVMCCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class HeltyVMCSensorDescription(SensorEntityDescription):
    """Describes a Helty VMC sensor."""

    value_fn: str


SENSOR_DESCRIPTIONS: tuple[HeltyVMCSensorDescription, ...] = (
    HeltyVMCSensorDescription(
        key="temperature_internal",
        translation_key="temperature_internal",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="temperature_internal",
    ),
    HeltyVMCSensorDescription(
        key="temperature_external",
        translation_key="temperature_external",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="temperature_external",
    ),
    HeltyVMCSensorDescription(
        key="humidity_internal",
        translation_key="humidity_internal",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="humidity_internal",
    ),
    HeltyVMCSensorDescription(
        key="co2",
        translation_key="co2",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="co2",
    ),
    HeltyVMCSensorDescription(
        key="voc",
        translation_key="voc",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_BILLION,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="voc",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helty VMC sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HeltyVMCCoordinator = data["coordinator"]
    name = entry.data.get(CONF_NAME, "Helty VMC")

    entities: list[SensorEntity] = []

    # Add sensor entities
    for description in SENSOR_DESCRIPTIONS:
        entities.append(HeltyVMCSensor(coordinator, entry, name, description))

    # Add speed and airflow sensors
    entities.append(HeltyVMCSpeedSensor(coordinator, entry, name))
    entities.append(HeltyVMCSpeedNumericSensor(coordinator, entry, name))
    entities.append(HeltyVMCAirflowSensor(coordinator, entry, name))

    async_add_entities(entities)


class HeltyVMCSensor(CoordinatorEntity[HeltyVMCCoordinator], SensorEntity):
    """Representation of a Helty VMC sensor."""

    _attr_has_entity_name = True
    entity_description: HeltyVMCSensorDescription

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        entry: ConfigEntry,
        name: str,
        description: HeltyVMCSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
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

    @property
    def native_value(self) -> float | int | None:
        """Return the sensor value."""
        if self.coordinator.sensors:
            return getattr(self.coordinator.sensors, self.entity_description.value_fn, None)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class HeltyVMCSpeedSensor(CoordinatorEntity[HeltyVMCCoordinator], SensorEntity):
    """Sensor for current speed mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "speed_mode"
    _attr_icon = "mdi:fan"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["off", "speed_1", "speed_2", "speed_3", "speed_4", "boost", "night", "free_cooling"]

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_speed_mode"
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
    def native_value(self) -> str | None:
        """Return the current speed mode."""
        if self.coordinator.status:
            mode = self.coordinator.status.speed_mode
            # Ensure returned value is always in options list
            if mode in self._attr_options:
                return mode
            return "off"
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class HeltyVMCSpeedNumericSensor(CoordinatorEntity[HeltyVMCCoordinator], SensorEntity):
    """Numeric sensor for current speed (0-7)."""

    _attr_has_entity_name = True
    _attr_translation_key = "speed"
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_speed"
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
    def native_value(self) -> int | None:
        """Return the current speed as number (0-7)."""
        if self.coordinator.status:
            return self.coordinator.status.speed
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class HeltyVMCAirflowSensor(CoordinatorEntity[HeltyVMCCoordinator], SensorEntity):
    """Sensor for airflow rate."""

    _attr_has_entity_name = True
    _attr_translation_key = "airflow"
    _attr_native_unit_of_measurement = "m³/h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weather-windy"

    def __init__(
        self,
        coordinator: HeltyVMCCoordinator,
        entry: ConfigEntry,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_airflow"
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
    def native_value(self) -> int | None:
        """Return the current airflow rate."""
        if self.coordinator.status:
            return AIRFLOW_RATES.get(self.coordinator.status.speed, 0)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
