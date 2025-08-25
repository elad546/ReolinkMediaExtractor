# Reolink Media Access (HACS)

A HACS custom integration that lets you browse and access items exposed by the Reolink integration in Home Assistant's Media Source. It provides a simple UI and HTTP endpoints to browse, resolve URLs, and proxy files.

This mirrors the media content made available by the official Reolink component's media source logic as in Home Assistant Core (`homeassistant/components/reolink/media_source.py`).

## Install via HACS

1. In Home Assistant, open HACS → Integrations → three dots → Custom repositories.
2. Add this repository URL: `https://github.com/elad546/ReolinkMediaExtractor` as type "Integration".
3. Search for "Reolink Media Access" and install.
4. Go to Settings → Devices & Services → Add Integration → "Reolink Media Access".
5. Open the sidebar item "Reolink Media".

## What you get

- Panel at `Sidebar → Reolink Media`.
- UI at `/reolink-media-access/ui`.
- API endpoints (authenticated):
  - `GET /api/reolink-media/browse?media_content_id=media-source://reolink`
  - `GET /api/reolink-media/browse/resolve?media_content_id=...`
  - `GET /api/reolink-media/browse/proxy?media_content_id=...`

## Notes

- Requires the official Reolink integration to be set up so the media source is populated.
- Uses Home Assistant `media_source` helpers to browse/resolve.
- The proxy endpoint streams content from the resolved URL through Home Assistant.
