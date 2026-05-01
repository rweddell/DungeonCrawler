from __future__ import annotations
import json
import uuid
from pathlib import Path
from app.config import settings
from app.models.character import Character, CharacterCreate, CharacterUpdate


def _path(char_id: str) -> Path:
    return settings.characters_dir / f"{char_id}.json"


def _proficiency_bonus(level: int) -> int:
    return max(2, (level - 1) // 4 + 2)


def _modifier(score: int) -> int:
    return (score - 10) // 2


async def list_characters() -> list[Character]:
    chars = []
    for f in settings.characters_dir.glob("*.json"):
        try:
            chars.append(Character.model_validate_json(f.read_text()))
        except Exception:
            pass
    return chars


async def get_character(char_id: str) -> Character | None:
    p = _path(char_id)
    if not p.exists():
        return None
    return Character.model_validate_json(p.read_text())


async def create_character(data: CharacterCreate) -> Character:
    char_id = str(uuid.uuid4())
    level = max(1, data.level)
    prof = _proficiency_bonus(level)

    char = Character(
        id=char_id,
        name=data.name,
        race=data.race,
        char_class=data.char_class,
        level=level,
        background=data.background,
        alignment=data.alignment,
        ability_scores=data.ability_scores,
        proficiency_bonus=prof,
        initiative_bonus=_modifier(data.ability_scores.dexterity),
        max_hp=8 + _modifier(data.ability_scores.constitution),
        current_hp=8 + _modifier(data.ability_scores.constitution),
        hit_dice=f"1d8",
        hit_dice_remaining=level,
    )
    _path(char_id).write_text(char.model_dump_json(indent=2))
    return char


async def update_character(char_id: str, data: CharacterUpdate) -> Character | None:
    char = await get_character(char_id)
    if not char:
        return None

    update_data = data.model_dump(exclude_unset=True)
    updated = char.model_copy(update=update_data)
    _path(char_id).write_text(updated.model_dump_json(indent=2))
    return updated


async def delete_character(char_id: str) -> bool:
    p = _path(char_id)
    if not p.exists():
        return False
    p.unlink()
    return True


async def save_character(char: Character) -> None:
    _path(char.id).write_text(char.model_dump_json(indent=2))
