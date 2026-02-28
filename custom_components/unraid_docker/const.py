"""Konstanten fuer die Unraid Docker Integration."""

from __future__ import annotations

DOMAIN = "unraid_docker"

CONF_SCAN_INTERVAL = "scan_interval"
CONF_KNOWN_HOSTS = "known_hosts"

DEFAULT_NAME = "Unraid Docker"
DEFAULT_PORT = 22
DEFAULT_SCAN_INTERVAL = 30

PLATFORMS = ["switch", "binary_sensor", "sensor"]

SERVICE_START_CONTAINER = "start_container"
SERVICE_STOP_CONTAINER = "stop_container"
SERVICE_RESTART_CONTAINER = "restart_container"

ATTR_CONTAINER = "container"
ATTR_ENTRY_ID = "entry_id"

COORDINATOR = "coordinator"
API = "api"

LOGGER_NAME = "custom_components.unraid_docker"
