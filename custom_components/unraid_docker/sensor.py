"""Sensoren fuer Host- und Container-Metriken."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN
from .coordinator import UnraidDockerDataUpdateCoordinator

@dataclass(slots=True)
class ContainerSensorDescription:
    """Definiert, welcher Wert als Sensor ausgegeben wird."""

    key: str
    suffix: str
    unit: str | None = None


CONTAINER_SENSOR_TYPES = [
    ContainerSensorDescription(key="status", suffix="status"),
    ContainerSensorDescription(key="cpu_percent", suffix="cpu", unit=PERCENTAGE),
    ContainerSensorDescription(key="mem_percent", suffix="memory", unit=PERCENTAGE),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setzt Sensoren fuer Host und Container auf."""
    coordinator: UnraidDockerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        COORDINATOR
    ]

    # Host Sensor ist statisch und wird immer erzeugt.
    async_add_entities(
        [UnraidHostUptimeSensor(coordinator=coordinator, entry_id=entry.entry_id)]
    )

    known: set[tuple[str, str]] = set()

    def _build_container_entities() -> list[UnraidContainerMetricSensor]:
        entities: list[UnraidContainerMetricSensor] = []
        containers = coordinator.data.get("containers", {}) if coordinator.data else {}

        for container_id in containers:
            for description in CONTAINER_SENSOR_TYPES:
                key = (container_id, description.key)
                if key in known:
                    continue
                known.add(key)
                entities.append(
                    UnraidContainerMetricSensor(
                        coordinator=coordinator,
                        entry_id=entry.entry_id,
                        container_id=container_id,
                        description=description,
                    )
                )

        return entities

    async_add_entities(_build_container_entities())

    @callback
    def _async_handle_coordinator_update() -> None:
        new_entities = _build_container_entities()
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_async_handle_coordinator_update))


class UnraidHostUptimeSensor(
    CoordinatorEntity[UnraidDockerDataUpdateCoordinator],
    SensorEntity,
):
    """Zeigt die Unraid Host-Uptime in Sekunden an."""

    _attr_has_entity_name = True
    _attr_name = "host uptime"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: UnraidDockerDataUpdateCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_host_uptime"

    @property
    def native_value(self) -> int:
        host = self.coordinator.data.get("host", {}) if self.coordinator.data else {}
        return int(host.get("uptime_seconds", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        host = self.coordinator.data.get("host", {}) if self.coordinator.data else {}
        return {
            "hostname": host.get("hostname"),
            "unraid_version": host.get("unraid_version"),
        }


class UnraidContainerMetricSensor(
    CoordinatorEntity[UnraidDockerDataUpdateCoordinator],
    SensorEntity,
):
    """Generischer Container-Sensor fuer Status, CPU und Speicher."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnraidDockerDataUpdateCoordinator,
        entry_id: str,
        container_id: str,
        description: ContainerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._container_id = container_id
        self._description = description

    @property
    def _container(self) -> dict[str, Any]:
        containers = self.coordinator.data.get("containers", {}) if self.coordinator.data else {}
        return containers.get(self._container_id, {})

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_{self._container_id}_{self._description.key}_sensor"

    @property
    def name(self) -> str:
        return (
            f"{self._container.get('name', self._container_id)} "
            f"{self._description.suffix}"
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._description.unit

    @property
    def native_value(self) -> Any:
        return self._container.get(self._description.key)

    @property
    def available(self) -> bool:
        return super().available and bool(self._container)

    @property
    def icon(self) -> str:
        return "mdi:docker"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "container_id": self._container.get("id"),
            "image": self._container.get("image"),
            "state": self._container.get("state"),
            "mem_usage": self._container.get("mem_usage"),
        }
