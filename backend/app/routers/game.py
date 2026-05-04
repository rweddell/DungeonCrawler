from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.game_state import (
    GameSession,
    GameStartRequest,
    PlayerAction,
    SaveFileMeta,
    CombatState,
)
from app.services import aidm as aidm_svc
from app.services import character as char_svc
from app.services import story as story_svc
from app.services import save_manager
from app.routers.app_settings import _load_settings

router = APIRouter(prefix="/game", tags=["game"])

# In-memory session store (keyed by session_id)
_sessions: dict[str, GameSession] = {}


def _get_session(session_id: str) -> GameSession:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return _sessions[session_id]


@router.post("/start")
async def start_game(req: GameStartRequest):
    story = await story_svc.get_story(req.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    character = await char_svc.get_character(req.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    settings = _load_settings()
    session_id = str(uuid.uuid4())
    session = GameSession(
        id=session_id,
        story_id=req.story_id,
        character_id=req.character_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    _sessions[session_id] = session

    opening_entry = await aidm_svc.start_session(
        session=session,
        character=character,
        story=story,
        responder_model=settings.responder_model,
    )

    return {
        "session_id": session_id,
        "opening": opening_entry,
        "session": session,
    }


@router.get("/saves", response_model=list[SaveFileMeta])
async def list_saves():
    return await save_manager.list_saves()


@router.get("/{session_id}")
async def get_session(session_id: str):
    return _get_session(session_id)


@router.post("/{session_id}/action")
async def player_action(session_id: str, action: PlayerAction):
    session = _get_session(session_id)

    character = await char_svc.get_character(session.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    story = await story_svc.get_story(session.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    settings = _load_settings()
    session, entry = await aidm_svc.process_action(
        session=session,
        character=character,
        story=story,
        action=action,
        assessor_model=settings.assessor_model,
        dice_agent_model=settings.dice_agent_model,
        responder_model=settings.responder_model,
        context_limit=settings.context_length,
    )
    _sessions[session_id] = session

    # Auto-save if configured
    if settings.auto_save and session.turn_count % settings.auto_save_interval == 0:
        await save_manager.save_game(session, character)

    return {"entry": entry, "session": session}


@router.post("/{session_id}/save")
async def save_session(session_id: str):
    session = _get_session(session_id)
    character = await char_svc.get_character(session.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    save_file = await save_manager.save_game(session, character)
    return {"save_id": save_file.id, "saved_at": save_file.saved_at}


@router.post("/load/{save_id}")
async def load_game(save_id: str):
    sf = await save_manager.load_game(save_id)
    if not sf:
        raise HTTPException(status_code=404, detail="Save not found")

    session = sf.session
    _sessions[session.id] = session

    return {"session_id": session.id, "session": session}


@router.delete("/saves/{save_id}", status_code=204)
async def delete_save(save_id: str):
    ok = await save_manager.delete_save(save_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Save not found")
