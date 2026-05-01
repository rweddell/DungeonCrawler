from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class NPC(BaseModel):
    name: str
    description: str = ""
    role: str = ""


class Story(BaseModel):
    id: str
    title: str
    synopsis: str = ""
    opening_narration: str = ""
    setting: str = ""
    npcs: list[NPC] = Field(default_factory=list)
    special_rules: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    is_custom: bool = False
    filename: str = ""


class StoryCreate(BaseModel):
    title: str
    synopsis: str = ""
    opening_narration: str = ""
    setting: str = ""
    npcs: list[NPC] = Field(default_factory=list)
    special_rules: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
