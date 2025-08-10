import os
import json
import logging
from typing import Any, Dict

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# ===== Logging =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("caption-debug")

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/caption")
async def caption(req: Request) -> Response:
    try:
        data: Dict[str, Any] = await req.json()
    except Exception:
        raw = await req.body()
        log.error("Could not parse JSON. Raw body=%s", raw)
        return JSONResponse({"error": "invalid_json"}, status_code=400)

    req_id = str(data.get("id"))
    image_url = str(data.get("image"))

    log.info("---- /caption CALLED ----")
    log.info("Incoming JSON: %s", json.dumps(data))
    log.info("req_id=%s  image_url=%s", req_id, image_url)

    if not image_url:
        log.error("Missing image URL.")
        return JSONResponse({"error": "missing_image"}, status_code=400)

    # Try download the image (no caching)
    # Accept any content-type; limit size to avoid surprises.
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(image_url, headers={"Cache-Control": "no-cache"})
            r.raise_for_status()
            content = r.content
            log.info("Downloaded image OK. bytes=%d  ct=%s", len(content), r.headers.get("content-type"))
    except Exception as e:
        log.exception("Failed to download image from URL.")
        # IMPORTANT: return a very explicit message so a fallback könnyen azonosítható
        return JSONResponse({"caption": "DEBUG: image_download_failed", "fileSize": 0}, status_code=200)

    # ---- Itt jönne az igazi AI hívás. Most direkt minimal. ----
    # Ha szeretnéd, ide be tudunk tenni egy későbbi modellt.
    # A lényeg: mindig írjunk ki mindent.
    if len(content) < 5000:
        log.warning("Very small image, suspicious. bytes=%d", len(content))

    # Példa: nagyon egyszerű "detekció"
    # (csak hogy lássunk változó outputot a Make-ben)
    guess = "face_detected" if len(content) > 10000 else "tiny_image"
    caption = f"DEBUG ok | id={req_id} | size={len(content)} | guess={guess}"
    log.info("Returning caption='%s'", caption)

    return JSONResponse({"caption": caption, "fileSize": len(content)}, status_code=200)
