from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from . import DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
	VERSION = 1

	async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
		await self.async_set_unique_id(DOMAIN)
		self._abort_if_unique_id_configured()
		return self.async_create_entry(title="Reolink Media Access", data={})
