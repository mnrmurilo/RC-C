"""Sensor platform for RC-C Solar (rc-ess)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


def _energy_kwh(value) -> float | None:
    """Convert a Wh value (int or numeric string) to kWh."""
    if value is None:
        return None
    try:
        return round(float(value) / 1000.0, 3)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class RcEssSensorDescription(SensorEntityDescription):
    """Describes an RC-C Solar sensor."""

    value_fn: Callable[[dict], float | int | bool | None]


SENSORS: tuple[RcEssSensorDescription, ...] = (
    RcEssSensorDescription(
        key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("power"),
    ),
    RcEssSensorDescription(
        key="today_energy",
        name="Energy today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _energy_kwh(d.get("dayEnergy")),
    ),
    RcEssSensorDescription(
        key="month_energy",
        name="Energy this month",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _energy_kwh(d.get("monthEnergy")),
    ),
    RcEssSensorDescription(
        key="total_energy",
        name="Total energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _energy_kwh(d.get("accEnergy")),
    ),
    RcEssSensorDescription(
        key="efficiency",
        name="Efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("efficiency"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RC-C Solar sensors."""
    coordinator: DataUpdateCoordinator[dict[str, dict]] = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities: list[RcEssSensor] = []
    for device_id in coordinator.data:
        for description in SENSORS:
            entities.append(RcEssSensor(coordinator, device_id, description))
    async_add_entities(entities)


class RcEssSensor(CoordinatorEntity, SensorEntity):
    """A sensor reading from a single RC-C inverter."""

    entity_description: RcEssSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, dict]],
        device_id: str,
        description: RcEssSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def _device(self) -> dict:
        return self.coordinator.data.get(self._device_id, {})

    @property
    def device_info(self) -> DeviceInfo:
        device = self._device
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("name") or device.get("sn") or self._device_id,
            manufacturer="Rockcore",
            model=device.get("model"),
        )

    @property
    def native_value(self):
        return self.entity_description.value_fn(self._device)

    @property
    def available(self) -> bool:
        return super().available and self._device_id in self.coordinator.data
