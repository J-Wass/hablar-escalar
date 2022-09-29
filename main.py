from io import BytesIO
import base64
from pathlib import Path

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi_cache.coder import PickleCoder, JsonCoder
from gtts import gTTS


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MPEGResponse(Response):
    media_type = "audio/mpeg"

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

@app.get("/phrases/{lang}/{difficulty}")
@cache(expire=86400, coder=PickleCoder)
async def phrases(lang, difficulty):
    path = f"assets/{lang}/phrases_{difficulty}.json"
    phrase_book_path = Path(path)
    if phrase_book_path.is_file():
        return FileResponse(path)
    raise HTTPException(status_code=404, detail=f"Language/Difficulty not found: {lang}/{difficulty}")

@app.get("/tts/{lang}/{text_base64}", response_class=MPEGResponse)
@cache(expire=86400, coder=PickleCoder)
async def index(lang, text_base64):
    text = base64.b64decode(text_base64 + '==').decode("latin-1")  
    print(f"Building response for {text} ({lang})")

    # Generate mp3 bytes.
    tts = gTTS(text, lang=lang)

    # Write tts data to bytes, send it back as audio/mpeg.
    mp3_bytes = BytesIO()
    tts.write_to_fp(mp3_bytes)
    return Response(
        base64.b64encode(mp3_bytes.getvalue()),
        headers={"content-type":"audio/mpeg", "cache-control": "public, max-age:604800"},
    )
    # return Response(mp3_bytes.getvalue(), headers={"content-type":"audio/mpeg", "cache-control": "public, max-age:604800"})

