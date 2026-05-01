import json
from fastapi import APIRouter
from app.models.game_state import RuntimeSettings
from app.config import settings as app_config

router = APIRouter(prefix="/settings", tags=["settings"])


def _load_settings() -> RuntimeSettings:
    p = app_config.settings_file
    if p.exists():
        try:
            return RuntimeSettings.model_validate_json(p.read_text())
        except Exception:
            pass
    return RuntimeSettings()


def _save_settings(s: RuntimeSettings) -> None:
    app_config.settings_file.parent.mkdir(parents=True, exist_ok=True)
    app_config.settings_file.write_text(s.model_dump_json(indent=2))


@router.get("", response_model=RuntimeSettings)
async def get_settings():
    return _load_settings()


@router.put("", response_model=RuntimeSettings)
async def update_settings(data: RuntimeSettings):
    _save_settings(data)
    return data
