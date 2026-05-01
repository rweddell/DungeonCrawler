from fastapi import APIRouter
from app.services.audio import freesound_client

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/scene")
async def get_scene_audio(keywords: str = ""):
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    sound = await freesound_client.get_audio_for_scene(kw_list)
    if not sound:
        return {"audio": None}

    sound_id = sound.get("id")
    previews = sound.get("previews", {})
    preview_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3", "")

    filename = None
    if preview_url and sound_id:
        filename = await freesound_client.download_preview(preview_url, sound_id)

    return {
        "audio": {
            "filename": filename,
            "url": f"/audio-files/{filename}" if filename else None,
            "name": sound.get("name", ""),
            "username": sound.get("username", ""),
            "license": sound.get("license", ""),
        }
    }
