"""Home Assistant Integration fuer Unraid Docker Steuerung."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    API,
    ATTR_CONTAINER,
    ATTR_ENTRY_ID,
    CONF_KNOWN_HOSTS,
    CONF_SCAN_INTERVAL,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_RESTART_CONTAINER,
    SERVICE_START_CONTAINER,
    SERVICE_STOP_CONTAINER,
)
from .coordinator import UnraidDockerDataUpdateCoordinator
from .unraid_api import UnraidApiClient, UnraidApiError, UnraidConnectionConfig

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONTAINER): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Initiales Setup der Integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt eine ConfigEntry Instanz auf."""
    hass.data.setdefault(DOMAIN, {})

    config = UnraidConnectionConfig(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        known_hosts=entry.data.get(CONF_KNOWN_HOSTS),
    )

    api = UnraidApiClient(config)
    coordinator = UnraidDockerDataUpdateCoordinator(
        hass=hass,
        api=api,
        scan_interval=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        API: api,
        COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_register_services(hass)

    _LOGGER.info("Unraid Docker Integration fuer %s erfolgreich gestartet", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlaedt eine ConfigEntry Instanz."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    if not hass.data[DOMAIN]:
        await _async_unregister_services(hass)

    return unload_ok


async def _async_register_services(hass: HomeAssistant) -> None:
    """Registriert Integrations-Services einmalig."""
    if hass.services.has_service(DOMAIN, SERVICE_START_CONTAINER):
        return

    async def _handle_start(call: ServiceCall) -> None:
        await _async_handle_container_action(hass, call, SERVICE_START_CONTAINER)

    async def _handle_stop(call: ServiceCall) -> None:
        await _async_handle_container_action(hass, call, SERVICE_STOP_CONTAINER)

    async def _handle_restart(call: ServiceCall) -> None:
        await _async_handle_container_action(hass, call, SERVICE_RESTART_CONTAINER)

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_CONTAINER,
        _handle_start,
        schema=SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_CONTAINER,
        _handle_stop,
        schema=SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTART_CONTAINER,
        _handle_restart,
        schema=SERVICE_SCHEMA,
    )


async def _async_unregister_services(hass: HomeAssistant) -> None:
    """Entfernt Services beim Entladen der letzten ConfigEntry."""
    for service in (SERVICE_START_CONTAINER, SERVICE_STOP_CONTAINER, SERVICE_RESTART_CONTAINER):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)


async def _async_handle_container_action(
    hass: HomeAssistant,
    call: ServiceCall,
    action: str,
) -> None:
    """Fuehrt Start/Stop/Restart fuer einen Container aus."""
    container = call.data[ATTR_CONTAINER]
    requested_entry_id = call.data.get(ATTR_ENTRY_ID)

    candidates = hass.data.get(DOMAIN, {})
    if not candidates:
        raise HomeAssistantError("Keine aktiven Unraid Docker Config Entries vorhanden")

    if requested_entry_id:
        if requested_entry_id not in candidates:
            raise HomeAssistantError(
                f"Config Entry '{requested_entry_id}' wurde nicht gefunden"
            )
        candidates = {requested_entry_id: candidates[requested_entry_id]}

    last_error: Exception | None = None

    for entry_id, runtime in candidates.items():
        api: UnraidApiClient = runtime[API]
        coordinator: UnraidDockerDataUpdateCoordinator = runtime[COORDINATOR]

        try:
            if action == SERVICE_START_CONTAINER:
                await api.start_container(container)
            elif action == SERVICE_STOP_CONTAINER:
                await api.stop_container(container)
            elif action == SERVICE_RESTART_CONTAINER:
                await api.restart_container(container)
            else:
                raise HomeAssistantError(f"Unbekannte Aktion: {action}")

            await coordinator.async_request_refresh()
            _LOGGER.info(
                "Container Aktion erfolgreich: action=%s container=%s entry_id=%s",
                action,
                container,
                entry_id,
            )
            return
        except UnraidApiError as err:
            _LOGGER.warning(
                "Container Aktion fehlgeschlagen: action=%s container=%s entry_id=%s error=%s",
                action,
                container,
                entry_id,
                err,
            )
            last_error = err

    raise HomeAssistantError(
        f"Container Aktion '{action}' fuer '{container}' fehlgeschlagen: {last_error}"
    )
