"""Data update coordinator for Helty VMC."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .protocol import HeltyVMCProtocol, VMCSensors, VMCStatus

_LOGGER = logging.getLogger(__name__)


class HeltyVMCCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for fetching data from Helty VMC."""

    def __init__(
        self,
        hass: HomeAssistant,
        protocol: HeltyVMCProtocol,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.protocol = protocol

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from VMC."""
        try:
            status = await self.protocol.get_status()
            sensors = await self.protocol.get_sensors()

            if not status.is_online:
                raise UpdateFailed("VMC is offline or not responding")

            return {
                "status": status,
                "sensors": sensors,
            }

        except Exception as err:
            raise UpdateFailed(f"Error fetching VMC data: {err}") from err

    @property
    def status(self) -> VMCStatus | None:
        """Return the current status."""
        if self.data:
            return self.data.get("status")
        return None

    @property
    def sensors(self) -> VMCSensors | None:
        """Return the current sensor readings."""
        if self.data:
            return self.data.get("sensors")
        return None
