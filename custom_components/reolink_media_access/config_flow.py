from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult


class ConfigFlow(config_entries.ConfigFlow, domain="reolink_media_access"):
	VERSION = 1

	async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
		await self.async_set_unique_id("reolink_media_access")
		self._abort_if_unique_id_configured()
		return self.async_create_entry(title="Reolink Media Access", data={})
