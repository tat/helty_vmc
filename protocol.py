"""Protocol handler for Helty VMC communication."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from .const import (
    CMD_GET_NAME,
    CMD_GET_SENSORS,
    CMD_GET_STATUS,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    SPEED_MODES,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class VMCStatus:
    """VMC device status."""

    speed: int = 0
    speed_mode: str = "off"
    is_online: bool = False
    led_on: bool | None = None
    led_filter_warning: bool = False  # True when LED shows "check filter" (code 00032)
    sensors_on: bool | None = None


@dataclass
class VMCSensors:
    """VMC sensor readings."""

    temperature_external: float | None = None
    temperature_internal: float | None = None
    humidity_internal: float | None = None
    co2: int | None = None
    voc: int | None = None
    filter_hours: int | None = None


@dataclass
class VMCInfo:
    """VMC device info."""

    name: str = "Helty VMC"


class HeltyVMCProtocol:
    """Protocol handler for Helty VMC devices."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the protocol handler."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._lock = asyncio.Lock()

    async def _send_command(self, command: str) -> str | None:
        """Send a command and receive response."""
        async with self._lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self.timeout,
                )

                writer.write(command.encode())
                await writer.drain()

                response = await asyncio.wait_for(
                    reader.read(1024),
                    timeout=self.timeout,
                )

                writer.close()
                await writer.wait_closed()

                decoded = response.decode().strip()
                _LOGGER.debug("Command %s response: %s", command, decoded)
                return decoded

            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout communicating with VMC at %s:%s", self.host, self.port)
                return None
            except OSError as err:
                _LOGGER.warning("Error communicating with VMC at %s:%s: %s", self.host, self.port, err)
                return None

    async def send_raw_command(self, command: str) -> bool:
        """Send a raw command to the VMC."""
        result = await self._send_command(command)
        return result is not None

    async def get_status(self) -> VMCStatus:
        """Get the current VMC status.

        Response format: VMGO,00001,00000,00000,00000,00000,...,00000
        Index [1]: current speed (00000-00007)
        Index [4]: sensors status (00000/00001=on, 00002/00003=off)
        Index [14]: LED panel status (00000=off, others=on, 00032=check filter)
        """
        status = VMCStatus()
        response = await self._send_command(CMD_GET_STATUS)

        if response and response.startswith("VMGO"):
            parts = response.split(",")
            _LOGGER.debug("VMGH? parsed %d parts", len(parts))
            
            # Speed [1]
            if len(parts) > 1:
                try:
                    speed_val = int(parts[1])
                    status.speed = speed_val
                    status.speed_mode = SPEED_MODES.get(speed_val, "unknown")
                    status.is_online = True
                except ValueError:
                    _LOGGER.warning("Invalid speed value in response: %s", parts[1])
            
            # Sensors status [4]
            if len(parts) > 4:
                try:
                    sensors_code = parts[4]
                    status.sensors_on = sensors_code in ("00000", "00001")
                    _LOGGER.debug("Sensors status raw=%s parsed=%s", sensors_code, status.sensors_on)
                except (ValueError, IndexError):
                    pass
            
            # LED panel status [14]
            if len(parts) > 14:
                try:
                    led_code = parts[14]
                    status.led_on = led_code != "00000"
                    status.led_filter_warning = led_code == "00032"
                    _LOGGER.debug("LED status raw=%s on=%s filter_warning=%s", led_code, status.led_on, status.led_filter_warning)
                except (ValueError, IndexError):
                    pass
        else:
            status.is_online = response is not None

        return status

    async def get_sensors(self) -> VMCSensors:
        """Get sensor readings.

        Response format: VMIO,TTTTT,TTTTT,HHHHH,CCCCC,...,VVVVV,...
        Index [1]: External temperature (divide by 10, first digit 1 = negative)
        Index [2]: Internal temperature (divide by 10, first digit 1 = negative)
        Index [3]: Internal humidity (divide by 10)
        Index [4]: CO2 in ppm
        Index [11]: VOC in ppb
        """
        sensors = VMCSensors()
        response = await self._send_command(CMD_GET_SENSORS)

        _LOGGER.debug("VMGI? raw response: %s", response)

        if response:
            # Handle both VMIO prefix and raw response
            if response.startswith("VMIO"):
                parts = response.split(",")
            elif "," in response:
                # Some devices may respond without prefix
                parts = response.split(",")
            else:
                _LOGGER.warning("Unexpected sensor response format: %s", response)
                return sensors

            _LOGGER.debug("Parsed %d parts from sensor response", len(parts))

            # Internal temperature [1]
            if len(parts) > 1:
                sensors.temperature_internal = self._parse_temperature(parts[1])
                _LOGGER.debug("Internal temp raw=%s parsed=%s", parts[1], sensors.temperature_internal)

            # External temperature [2]
            if len(parts) > 2:
                sensors.temperature_external = self._parse_temperature(parts[2])
                _LOGGER.debug("External temp raw=%s parsed=%s", parts[2], sensors.temperature_external)

            # Internal humidity [3]
            if len(parts) > 3:
                sensors.humidity_internal = self._parse_humidity(parts[3])
                _LOGGER.debug("Humidity raw=%s parsed=%s", parts[3], sensors.humidity_internal)

            # CO2 [4]
            if len(parts) > 4:
                sensors.co2 = self._parse_int(parts[4])

            # VOC [11]
            if len(parts) > 11:
                sensors.voc = self._parse_int(parts[11])

        return sensors

    async def get_info(self) -> VMCInfo:
        """Get device information."""
        info = VMCInfo()
        response = await self._send_command(CMD_GET_NAME)

        if response:
            # Response format varies, typically contains the name
            info.name = response.strip()

        return info

    async def check_connection(self) -> bool:
        """Check if the device is reachable."""
        response = await self._send_command(CMD_GET_STATUS)
        return response is not None and response.startswith("VMGO")

    @staticmethod
    def _parse_temperature(value: str) -> float | None:
        """Parse temperature value.

        Format: 5 digits where first digit 1 = negative temperature.
        Example: 00215 = 21.5°C, 10200 = -20.0°C
        Value (without sign indicator) divided by 10 for actual temperature.
        """
        try:
            if not value or not value.strip():
                return None
            value = value.strip()
            if value.startswith("1") and len(value) == 5:
                # Negative temperature: first digit is 1, rest is temp * 10
                temp_part = value[1:]
                return -(int(temp_part) / 10)
            else:
                # Positive temperature
                return int(value) / 10
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_humidity(value: str) -> float | None:
        """Parse humidity value (divide by 10)."""
        try:
            val = float(value) / 10
            return min(val, 100.0) if val > 0 else None
        except ValueError:
            return None

    @staticmethod
    def _parse_int(value: str) -> int | None:
        """Parse integer value."""
        try:
            val = int(value)
            return val if val > 0 else None
        except ValueError:
            return None
