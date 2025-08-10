from fastapi import FastAPI, Request
from pydantic import BaseModel, HttpUrl
import hashlib, requests, time
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

app = FastAPI()

class CaptionRequest(BaseModel):
    id: str
    image: HttpUrl

def add_cache_buster(url: str, token: str) -> str:
    u = urlparse(str(url))
    qs = dict(parse_qsl(u.query, keep_blank_values=True))
    # cache-buster: mindig új érték
    qs["_cb"] = f"{token}_{int(time.time())}"
    new_q = urlencode(qs)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))

@app.post("/caption")
def caption(req: CaptionRequest):
    # 1) log bejövő payload
    print(f"[IN] id={req.id} image={req.image}", flush=True)

    # 2) kép letöltése cache‑kerüléssel
    img_url = add_cache_buster(str(req.image), req.id)
    r = requests.get(img_url, timeout=30, headers={"Cache-Control": "no-cache"})
    r.raise_for_status()
    data = r.content

    # 3) “pszeudo‑elemzés”: hash, bájtok, pár meta -> ezek biztosan változnak képenként
    sha = hashlib.sha256(data).hexdigest()
    file_size = len(data)

    # 4) log feldolgozás
    print(f"[OK] bytes={file_size} sha256={sha[:16]}...", flush=True)

    # 5) vissza egyszerű, de informatív JSON
    return {
        "caption": f"debug: size={file_size}B sha16={sha[:16]}",
        "fileSize": file_size
    }

@app.get("/health")
def health():
    return {"ok": True}
