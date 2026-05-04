from __future__ import annotations
import uuid
from pathlib import Path
from app.config import settings
from app.models.story import Story, StoryCreate


def _story_path(story_id: str) -> Path:
    return settings.stories_dir / f"{story_id}.json"


async def list_stories() -> list[Story]:
    stories = []
    for f in settings.stories_dir.glob("*.json"):
        try:
            stories.append(Story.model_validate_json(f.read_text()))
        except Exception:
            pass
    return stories


async def get_story(story_id: str) -> Story | None:
    # Fast path: story was created with a matching UUID filename
    p = _story_path(story_id)
    if p.exists():
        return Story.model_validate_json(p.read_text())
    # Slow path: built-in stories have human-readable IDs that don't match filenames
    for f in settings.stories_dir.glob("*.json"):
        try:
            story = Story.model_validate_json(f.read_text())
            if story.id == story_id:
                return story
        except Exception:
            pass
    return None


async def create_story(data: StoryCreate) -> Story:
    story_id = str(uuid.uuid4())
    story = Story(id=story_id, filename=f"{story_id}.json", **data.model_dump())
    _story_path(story_id).write_text(story.model_dump_json(indent=2))
    return story


async def upload_story_from_json(content: str) -> Story:
    """Parse a .json upload into a Story object. The id field is replaced with a new UUID."""
    data = StoryCreate.model_validate_json(content)
    return await create_story(data)


async def delete_story(story_id: str) -> bool:
    # Find the actual file regardless of naming convention
    target: Path | None = None
    for f in settings.stories_dir.glob("*.json"):
        try:
            story = Story.model_validate_json(f.read_text())
            if story.id == story_id:
                if not story.is_custom:
                    return False  # Don't delete built-in stories
                target = f
                break
        except Exception:
            pass
    if target is None:
        return False
    target.unlink()
    return True
