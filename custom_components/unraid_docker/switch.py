"""Switch-Entitaeten fuer Docker Container Start/Stop."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API, COORDINATOR, DOMAIN
from .coordinator import UnraidDockerDataUpdateCoordinator
from .unraid_api import UnraidApiClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setzt Container-Switches fuer einen ConfigEntry auf."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator: UnraidDockerDataUpdateCoordinator = runtime[COORDINATOR]
    api: UnraidApiClient = runtime[API]

    known: set[str] = set()

    def _build_entities() -> list[UnraidContainerSwitch]:
        entities: list[UnraidContainerSwitch] = []
        containers = coordinator.data.get("containers", {}) if coordinator.data else {}
        for container_id in containers:
            if container_id in known:
                continue
            known.add(container_id)
            entities.append(
                UnraidContainerSwitch(
                    coordinator=coordinator,
                    api=api,
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


class UnraidContainerSwitch(
    CoordinatorEntity[UnraidDockerDataUpdateCoordinator],
    SwitchEntity,
):
    """Switch zur Steuerung eines einzelnen Docker Containers."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnraidDockerDataUpdateCoordinator,
        api: UnraidApiClient,
        entry_id: str,
        container_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._api = api
        self._entry_id = entry_id
        self._container_id = container_id

    @property
    def _container(self) -> dict[str, Any]:
        containers = self.coordinator.data.get("containers", {}) if self.coordinator.data else {}
        return containers.get(self._container_id, {})

    @property
    def name(self) -> str:
        """Anzeige-Name des Switches."""
        return self._container.get("name", self._container_id)

    @property
    def unique_id(self) -> str:
        """Eindeutige ID fuer Entity Registry."""
        return f"{self._entry_id}_{self._container_id}_switch"

    @property
    def available(self) -> bool:
        """Entity gilt als verfuegbar, wenn der Coordinator Daten hat."""
        return super().available and bool(self._container)

    @property
    def is_on(self) -> bool | None:
        """Container gilt als eingeschaltet, wenn er laeuft."""
        return self._container.get("state") == "running"

    @property
    def icon(self) -> str:
        return "mdi:docker"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Startet den zugeordneten Container."""
        container_name = self._container.get("name", self._container_id)
        _LOGGER.debug("Starte Container ueber Switch: %s", container_name)
        await self._api.start_container(container_name)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stoppt den zugeordneten Container."""
        container_name = self._container.get("name", self._container_id)
        _LOGGER.debug("Stoppe Container ueber Switch: %s", container_name)
        await self._api.stop_container(container_name)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Zusatzattribute fuer Debugging in Home Assistant."""
        return {
            "container_id": self._container.get("id"),
            "image": self._container.get("image"),
            "status": self._container.get("status"),
        }
