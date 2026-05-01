from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import game, characters, stories, ollama, images, audio, app_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directories exist on startup
    for d in [
        settings.saves_dir,
        settings.characters_dir,
        settings.stories_dir,
        settings.srd_dir,
        settings.audio_cache_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="DungeonCrawler API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve cached audio files as static
app.mount(
    "/audio-files",
    StaticFiles(directory=str(settings.audio_cache_dir), check_dir=False),
    name="audio_files",
)

PREFIX = "/api/v1"
app.include_router(ollama.router, prefix=PREFIX)
app.include_router(game.router, prefix=PREFIX)
app.include_router(characters.router, prefix=PREFIX)
app.include_router(stories.router, prefix=PREFIX)
app.include_router(images.router, prefix=PREFIX)
app.include_router(audio.router, prefix=PREFIX)
app.include_router(app_settings.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}
