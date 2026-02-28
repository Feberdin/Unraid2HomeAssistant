"""Binary Sensoren fuer Container Laufstatus."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN
from .coordinator import UnraidDockerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setzt Binary Sensoren fuer Containerstatus auf."""
    coordinator: UnraidDockerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        COORDINATOR
    ]
    known: set[str] = set()

    def _build_entities() -> list[UnraidContainerRunningBinarySensor]:
        entities: list[UnraidContainerRunningBinarySensor] = []
        containers = coordinator.data.get("containers", {}) if coordinator.data else {}
        for container_id in containers:
            if container_id in known:
                continue
            known.add(container_id)
            entities.append(
                UnraidContainerRunningBinarySensor(
                    coordinator=coordinator,
                    entry_id=entry.entry_id,
                    container_id=container_id,
                )
            )
        return entities

    async_add_entities(_build_entities())

    @callback
    def _async_handle_coordinator_update() -> None:
        new_entities = _build_entities()
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_async_handle_coordinator_update))


class UnraidContainerRunningBinarySensor(
    CoordinatorEntity[UnraidDockerDataUpdateCoordinator],
    BinarySensorEntity,
):
    """Zeigt an, ob ein Container aktuell laeuft."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: UnraidDockerDataUpdateCoordinator,
        entry_id: str,
        container_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._container_id = container_id

    @property
    def _container(self) -> dict[str, Any]:
        containers = self.coordinator.data.get("containers", {}) if self.coordinator.data else {}
        return containers.get(self._container_id, {})

    @property
    def name(self) -> str:
        return f"{self._container.get('name', self._container_id)} running"

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_{self._container_id}_running"

    @property
    def is_on(self) -> bool | None:
        return self._container.get("state") == "running"

    @property
    def available(self) -> bool:
        return super().available and bool(self._container)

    @property
    def icon(self) -> str:
        return "mdi:docker"
