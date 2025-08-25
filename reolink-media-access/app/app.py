import os
import urllib.parse

import requests
from flask import Flask, jsonify, redirect, request, Response

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
SUPERVISOR_API = os.environ.get("SUPERVISOR_API", "http://supervisor/core/api")

HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}" if SUPERVISOR_TOKEN else "",
}

app = Flask(__name__)


def ha_get(path: str, params: dict | None = None, stream: bool = False) -> requests.Response:
    url = f"{SUPERVISOR_API}{path}"
    resp = requests.get(url, headers=HEADERS, params=params, stream=stream, timeout=60)
    resp.raise_for_status()
    return resp


@app.route("/")
def index():
    mcid = request.args.get("media_content_id", "media-source://reolink")
    target = f"/ui?media_content_id={urllib.parse.quote(mcid, safe='')}"
    return redirect(target)


@app.route("/ui")
def ui():
    mcid = request.args.get("media_content_id", "media-source://reolink")
    data = ha_get("/media_source/browse", params={"media_content_id": mcid}).json()
    items = data.get("children", []) or []

    html: list[str] = [
        "<html><head><meta charset='utf-8'><title>Reolink Media</title></head><body>",
        "<h3>Reolink Media Source</h3>",
        f"<p><code>{mcid}</code></p>",
    ]

    parent = data.get("parent")
    if parent:
        html.append(
            f'<p><a href="/ui?media_content_id={urllib.parse.quote(parent, safe="")}">⬅ Up</a></p>'
        )

    html.append("<ul>")
    for item in items:
        title = item.get("title") or item.get("media_content_id")
        child_id = item.get("media_content_id")
        if not child_id:
            continue
        can_expand = item.get("can_expand", False)
        if can_expand:
            html.append(
                f'<li>📁 <a href="/ui?media_content_id={urllib.parse.quote(child_id, safe="")}">{title}</a></li>'
            )
        else:
            q = urllib.parse.quote(child_id, safe="")
            html.append(
                f'<li>🎞 {title} — '
                f'<a href="/resolve?media_content_id={q}">resolve</a> | '
                f'<a href="/proxy?media_content_id={q}">proxy</a></li>'
            )
    html.append("</ul></body></html>")
    return "\n".join(html)


@app.route("/browse")
def browse():
    mcid = request.args.get("media_content_id", "media-source://reolink")
    data = ha_get("/media_source/browse", params={"media_content_id": mcid}).json()
    return jsonify(data)


@app.route("/resolve")
def resolve():
    mcid = request.args.get("media_content_id")
    if not mcid:
        return jsonify({"error": "media_content_id required"}), 400
    data = ha_get("/media_source/resolve", params={"media_content_id": mcid}).json()
    return jsonify(data)


@app.route("/proxy")
def proxy():
    mcid = request.args.get("media_content_id")
    if not mcid:
        return jsonify({"error": "media_content_id required"}), 400

    data = ha_get("/media_source/resolve", params={"media_content_id": mcid}).json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL returned from resolve"}), 404

    upstream = requests.get(url, stream=True, timeout=60)

    def generate():
        for chunk in upstream.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    return Response(
        generate(),
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type", "application/octet-stream"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8099")))
