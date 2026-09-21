"""Config flow for the CWA Kobo Sync integration."""

from __future__ import annotations

import hashlib
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector

from .api import CwaKoboSyncAuthError, CwaKoboSyncError, async_get_sync, normalize_sync_url
from .const import CONF_SYNC_URL, DOMAIN


class CwaKoboSyncConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle setup from one pasted Kobo Sync link."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Accept and validate the CWA Kobo Sync link."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                sync_url = normalize_sync_url(user_input[CONF_SYNC_URL])
                await async_get_sync(async_get_clientsession(self.hass), sync_url)
            except ValueError:
                errors[CONF_SYNC_URL] = "invalid_sync_url"
            except CwaKoboSyncAuthError:
                errors["base"] = "invalid_auth"
            except CwaKoboSyncError:
                errors["base"] = "cannot_connect"
            else:
                # The secret link itself must not become an entity or device identifier.
                await self.async_set_unique_id(hashlib.sha256(sync_url.encode()).hexdigest())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="CWA Kobo Sync", data={CONF_SYNC_URL: sync_url})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_SYNC_URL): TextSelector()}),
            errors=errors,
        )
