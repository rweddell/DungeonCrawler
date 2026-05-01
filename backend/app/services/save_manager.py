from __future__ import annotations
import uuid
from datetime import datetime
from app.config import settings
from app.models.game_state import GameSession, SaveFile, SaveFileMeta
from app.models.character import Character
from app.services.story import get_story


def _save_path(save_id: str):
    return settings.saves_dir / f"{save_id}.json"


async def list_saves() -> list[SaveFileMeta]:
    saves = []
    for f in settings.saves_dir.glob("*.json"):
        try:
            sf = SaveFile.model_validate_json(f.read_text())
            saves.append(
                SaveFileMeta(
                    id=sf.id,
                    character_name=sf.character_name,
                    story_title=sf.story_title,
                    saved_at=sf.saved_at,
                    turn_count=sf.turn_count,
                )
            )
        except Exception:
            pass
    saves.sort(key=lambda s: s.saved_at, reverse=True)
    return saves


async def save_game(session: GameSession, character: Character) -> SaveFile:
    story = await get_story(session.story_id)
    story_title = story.title if story else "Unknown Story"

    save_id = str(uuid.uuid4())
    sf = SaveFile(
        id=save_id,
        session=session,
        character_snapshot=character.model_dump(),
        story_title=story_title,
        character_name=character.name,
        saved_at=datetime.utcnow(),
        turn_count=session.turn_count,
    )
    _save_path(save_id).write_text(sf.model_dump_json(indent=2))
    return sf


async def load_game(save_id: str) -> SaveFile | None:
    p = _save_path(save_id)
    if not p.exists():
        return None
    return SaveFile.model_validate_json(p.read_text())


async def delete_save(save_id: str) -> bool:
    p = _save_path(save_id)
    if not p.exists():
        return False
    p.unlink()
    return True
