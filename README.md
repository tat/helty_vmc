# Helty VMC Integration for Home Assistant

A clean, modern Home Assistant custom integration for Helty VMC (Flow Plus/Elite) devices.

## Credits

Protocol reverse-engineered from the [VMC-HELTY-FLOW](https://github.com/DanRobo76/VMC-HELTY-FLOW) project by Ing. Danilo Robotti.

## Features

- **Fan Entity**: Control fan speed with preset modes (Speed 1-4, Boost, Night, Free Cooling)
- **Sensors**:
  - Internal Temperature
  - External Temperature
  - Internal Humidity
  - CO2 (Elite model only)
  - VOC (Elite model only)
  - Current Speed Mode
  - Airflow Rate (m³/h)
- **Switches**:
  - LED Panel On/Off
  - Sensors On/Off
- **Button**:
  - Reset Filter Counter

## Prerequisites

1. **Static IP**: Configure your router to assign a static IP to your VMC device
2. **Network Access**: Ensure Home Assistant can reach the VMC on port 5001
3. **Air Guard App**: Make sure your VMC is visible in the Helty Air Guard app first

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/helty_vmc` folder to your Home Assistant `config/custom_components/` directory:
   ```
   config/
   └── custom_components/
       └── helty_vmc/
           ├── __init__.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── fan.py
           ├── sensor.py
           ├── switch.py
           ├── button.py
           ├── protocol.py
           ├── manifest.json
           ├── strings.json
           └── translations/
               ├── en.json
               └── it.json
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "Helty VMC"

5. Enter your VMC's IP address and configure options

### Method 2: HACS (if published)

1. Add this repository to HACS as a custom repository
2. Install "Helty VMC" integration
3. Restart Home Assistant
4. Configure via UI

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| IP Address | Required | Static IP of your VMC device |
| Port | 5001 | TCP port (don't change unless necessary) |
| Name | Helty VMC | Display name for the device |
| Update Interval | 30 | How often to poll the device (seconds) |

## Usage

### Fan Control

The VMC appears as a fan entity with these preset modes:
- `speed_1` - Speed 1 (~15 m³/h)
- `speed_2` - Speed 2 (~30 m³/h)
- `speed_3` - Speed 3 (~45 m³/h)
- `speed_4` - Speed 4 (~60 m³/h)
- `boost` - Boost/Hyperventilation (~80 m³/h)
- `night` - Night mode (~10 m³/h)
- `free_cooling` - Free Cooling/Heating (~60 m³/h)

### Automation Examples

#### Set speed based on CO2 levels
```yaml
automation:
  - alias: "VMC Auto Speed by CO2"
    trigger:
      - platform: numeric_state
        entity_id: sensor.helty_vmc_co2
        above: 1000
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.helty_vmc
        data:
          preset_mode: speed_3

  - alias: "VMC Normal Speed when CO2 OK"
    trigger:
      - platform: numeric_state
        entity_id: sensor.helty_vmc_co2
        below: 800
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.helty_vmc
        data:
          preset_mode: speed_1
```

#### Night mode schedule
```yaml
automation:
  - alias: "VMC Night Mode"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.helty_vmc
        data:
          preset_mode: night

  - alias: "VMC Day Mode"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.helty_vmc
        data:
          preset_mode: speed_2
```

#### Humidity-based ventilation
```yaml
automation:
  - alias: "VMC Boost on High Humidity"
    trigger:
      - platform: numeric_state
        entity_id: sensor.helty_vmc_humidity_internal
        above: 70
        for:
          minutes: 5
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.helty_vmc
        data:
          preset_mode: boost
```

#### Turn off when away
```yaml
automation:
  - alias: "VMC Off When Away"
    trigger:
      - platform: state
        entity_id: group.family
        to: "not_home"
        for:
          minutes: 30
    action:
      - service: fan.turn_off
        target:
          entity_id: fan.helty_vmc
```

## Lovelace Card Example

```yaml
type: entities
title: Helty VMC
entities:
  - entity: fan.helty_vmc
  - entity: sensor.helty_vmc_speed_mode
  - entity: sensor.helty_vmc_airflow_rate
  - entity: sensor.helty_vmc_internal_temperature
  - entity: sensor.helty_vmc_external_temperature
  - entity: sensor.helty_vmc_internal_humidity
  - entity: sensor.helty_vmc_co2
  - entity: sensor.helty_vmc_voc
  - entity: switch.helty_vmc_led_panel
  - entity: switch.helty_vmc_sensors
  - entity: button.helty_vmc_reset_filter
```

## Testing the Connection

You can test connectivity to your VMC from the command line:

```bash
# Test connection (should return VMGO,...)
echo "VMGH?" | nc YOUR_VMC_IP 5001

# Get sensor data (should return VMIO,...)
echo "VMGI?" | nc YOUR_VMC_IP 5001

# Get device name
echo "VMNM?" | nc YOUR_VMC_IP 5001
```

## Troubleshooting

### Cannot connect to VMC
1. Verify the IP address is correct
2. Check that port 5001 is not blocked by firewall
3. Ensure VMC is visible in the Air Guard app
4. Try the `nc` commands above to test connectivity

### Sensors show unavailable
1. The VMC sensors feature might be disabled - use the Sensors switch to enable
2. CO2 and VOC sensors are only available on the Elite model

### Filter reset doesn't work
The filter reset command sends the reset signal to the VMC. Verify by checking the Air Guard app.

## Protocol Reference

| Command | Description |
|---------|-------------|
| `VMGH?` | Get fan status |
| `VMGI?` | Get sensor readings |
| `VMNM?` | Get device name |
| `VMSL?` | Get LAN info |
| `VMWH0000000` | Set speed 0 (off) |
| `VMWH0000001` | Set speed 1 |
| `VMWH0000002` | Set speed 2 |
| `VMWH0000003` | Set speed 3 |
| `VMWH0000004` | Set speed 4 |
| `VMWH0000005` | Set boost mode |
| `VMWH0000006` | Set night mode |
| `VMWH0000007` | Set free cooling |
| `VMWH0300000` | Sensors on |
| `VMWH0300002` | Sensors off |
| `VMWH0100010` | LED panel on |
| `VMWH0100000` | LED panel off |
| `VMWH0417744` | Reset filter |

## License

MIT License

