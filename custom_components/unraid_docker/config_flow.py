"""Config Flow fuer die Unraid Docker Integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback

from .const import (
    CONF_KNOWN_HOSTS,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .unraid_api import UnraidApiClient, UnraidApiError, UnraidAuthenticationError, UnraidConnectionConfig

_LOGGER = logging.getLogger(__name__)


class UnraidDockerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfigurationsfluss fuer die Integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Erster Schritt: Zugangsdaten abfragen und testen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_USERNAME]}@{user_input[CONF_HOST]}")
            self._abort_if_unique_id_configured()

            connection_config = UnraidConnectionConfig(
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                known_hosts=user_input.get(CONF_KNOWN_HOSTS),
            )
            api = UnraidApiClient(connection_config)

            try:
                await api.test_connection()
            except UnraidAuthenticationError:
                errors["base"] = "invalid_auth"
            except UnraidApiError as err:
                _LOGGER.error("Verbindungstest fehlgeschlagen: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # pragma: no cover - Schutz fuer unerwartete Fehler
                _LOGGER.exception(
                    "Unerwarteter Fehler im Config Flow fuer Host=%s Benutzer=%s",
                    user_input.get(CONF_HOST),
                    user_input.get(CONF_USERNAME),
                )
                errors["base"] = "cannot_connect"
            else:
                data = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_KNOWN_HOSTS: user_input.get(CONF_KNOWN_HOSTS, ""),
                }
                options = {
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                }
                return self.async_create_entry(
                    title=f"{user_input[CONF_HOST]}",
                    data=data,
                    options=options,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_KNOWN_HOSTS, default=""): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Stellt den Options-Flow bereit."""
        return UnraidDockerOptionsFlow(config_entry)


class UnraidDockerOptionsFlow(config_entries.OptionsFlow):
    """Optionen zur Laufzeitanpassung der Integration."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Erlaubt das Aendern des Polling-Intervalls."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            DEFAULT_SCAN_INTERVAL,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                }
            ),
        )
