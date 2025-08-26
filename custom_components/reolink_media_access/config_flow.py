from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from . import DOMAIN


class ReolinkMediaAccessConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
	VERSION = 1

	async def async_step_user(self, user_input=None):
		return self.async_create_entry(title="Reolink Media Access", data={})
