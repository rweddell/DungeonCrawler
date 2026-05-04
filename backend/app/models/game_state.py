from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class RollRequest(BaseModel):
    roll_type: str  # "ability_check", "saving_throw", "attack_roll"
    ability: str    # "strength", "dexterity", "perception", etc.
    dc: Optional[int] = None
    advantage: bool = False
    disadvantage: bool = False


class RollResult(BaseModel):
    d20: int
    modifier: int
    total: int
    dc: Optional[int] = None
    success: Optional[bool] = None
    label: str


class Combatant(BaseModel):
    id: str
    name: str
    initiative: int
    is_player: bool
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    conditions: list[str] = Field(default_factory=list)
    is_defeated: bool = False


class CombatState(BaseModel):
    active: bool = False
    round: int = 1
    current_turn_index: int = 0
    combatants: list[Combatant] = Field(default_factory=list)
    log: list[str] = Field(default_factory=list)


class NarrativeEntry(BaseModel):
    role: Literal["aidm", "player", "system", "roll"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    roll_request: Optional[RollRequest] = None
    roll_result: Optional[RollResult] = None
    scene_keywords: list[str] = Field(default_factory=list)
    combat_signal: Optional[Literal["start", "end"]] = None


class GameSession(BaseModel):
    id: str
    story_id: str
    character_id: str
    narrative_history: list[NarrativeEntry] = Field(default_factory=list)
    combat_state: CombatState = Field(default_factory=CombatState)
    turn_count: int = 0
    current_scene_keywords: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class SaveFile(BaseModel):
    id: str
    session: GameSession
    character_snapshot: dict
    story_title: str
    character_name: str
    saved_at: datetime = Field(default_factory=datetime.utcnow)
    turn_count: int = 0


class SaveFileMeta(BaseModel):
    id: str
    character_name: str
    story_title: str
    saved_at: datetime
    turn_count: int


class PlayerAction(BaseModel):
    text: str
    roll_result: Optional[RollResult] = None


class GameStartRequest(BaseModel):
    story_id: str
    character_id: str


class RuntimeSettings(BaseModel):
    ollama_model: str = "llama3"
    assessor_model: str = "mistral:instruct"
    dice_agent_model: str = "mistral:instruct"
    responder_model: str = "mistral:instruct"
    context_length: int = 50
    auto_save: bool = True
    auto_save_interval: int = 5
    audio_enabled: bool = True
    audio_volume: float = 0.7
    images_enabled: bool = True
    theme: str = "parchment"
