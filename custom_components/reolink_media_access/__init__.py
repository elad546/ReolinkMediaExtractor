from __future__ import annotations

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.http import HomeAssistantView
from homeassistant.components import http
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.media_source import async_browse_media, async_resolve_media

# Import config flow
from .config_flow import ConfigFlow

DOMAIN = "reolink_media_access"
PANEL_URL = "/reolink-media-access/ui"

__all__ = ["ConfigFlow"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.http.register_view(ReolinkUiView(hass))
    hass.http.register_view(ReolinkBrowseView(hass))
    hass.http.register_view(ReolinkResolveView(hass))
    hass.http.register_view(ReolinkProxyView(hass))

    async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title="Reolink Media",
        sidebar_icon="mdi:cctv",
        js_url=None,
        url_path="reolink-media",
        config={"url": PANEL_URL},
        require_admin=False,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Frontend panels are auto-removed when component unloads
    return True


class ReolinkUiView(HomeAssistantView):
    url = PANEL_URL
    name = f"{DOMAIN}:ui"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        mcid = request.query.get("media_content_id", "media-source://reolink")
        data = await async_browse_media(self.hass, mcid)
        items = getattr(data, "children", []) or []

        def escape(txt: str) -> str:
            return (txt or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html = [
            "<html><head><meta charset='utf-8'><title>Reolink Media</title></head><body>",
            "<h3>Reolink Media Source</h3>",
            f"<p><code>{escape(mcid)}</code></p>",
        ]
        parent = getattr(data, "parent")
        if parent:
            html.append(f"<p><a href=\"{self.url}?media_content_id={web.URL.build(path='/', query={'media_content_id': parent}).query['media_content_id']}\">⬅ Up</a></p>")

        html.append("<ul>")
        for item in items:
            title = escape(getattr(item, "title", None) or getattr(item, "media_content_id", ""))
            child_id = getattr(item, "media_content_id", None)
            if not child_id:
                continue
            can_expand = getattr(item, "can_expand", False)
            if can_expand:
                html.append(
                    f'<li>📁 <a href="{self.url}?media_content_id={web.URL.build(path="/", query={"media_content_id": child_id}).query["media_content_id"]}">{title}</a></li>'
                )
            else:
                q = web.URL.build(path="/", query={"media_content_id": child_id}).query["media_content_id"]
                html.append(
                    f'<li>🎞 {title} — '
                    f'<a href="/api/reolink-media/browse/resolve?media_content_id={q}">resolve</a> | '
                    f'<a href="/api/reolink-media/browse/proxy?media_content_id={q}">proxy</a></li>'
                )
        html.append("</ul></body></html>")
        return web.Response(text="\n".join(html), content_type="text/html; charset=utf-8")


class ReolinkBrowseView(HomeAssistantView):
    url = "/api/reolink-media/browse"
    name = f"{DOMAIN}:browse"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        mcid = request.query.get("media_content_id", "media-source://reolink")
        data = await async_browse_media(self.hass, mcid)
        return self.json(data.as_dict())


class ReolinkResolveView(HomeAssistantView):
    url = "/api/reolink-media/browse/resolve"
    name = f"{DOMAIN}:resolve"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        mcid = request.query.get("media_content_id")
        if not mcid:
            return web.json_response({"error": "media_content_id required"}, status=400)
        resolved = await async_resolve_media(self.hass, mcid)
        return self.json({"url": resolved.url, "mime_type": resolved.mime_type})


class ReolinkProxyView(HomeAssistantView):
    url = "/api/reolink-media/browse/proxy"
    name = f"{DOMAIN}:proxy"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        mcid = request.query.get("media_content_id")
        if not mcid:
            return web.json_response({"error": "media_content_id required"}, status=400)
        resolved = await async_resolve_media(self.hass, mcid)

        # Stream the upstream response back
        session = request.app[http.KEY_HASS].helpers.aiohttp_client.async_get_clientsession()
        async with session.get(resolved.url) as resp:
            headers = {k: v for k, v in resp.headers.items() if k.lower() in ("content-type", "content-length")}
            stream_resp = web.StreamResponse(status=resp.status, headers=headers)
            await stream_resp.prepare(request)
            async for chunk in resp.content.iter_chunked(8192):
                await stream_resp.write(chunk)
            await stream_resp.write_eof()
            return stream_resp
