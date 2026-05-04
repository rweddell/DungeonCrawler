from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from app.models.character import Character
from app.models.game_state import GameSession, NarrativeEntry, RollRequest, PlayerAction
from app.models.story import Story
from app.services.ollama_client import ollama_client

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")

# ─── Shared helpers ───────────────────────────────────────────────────────────

def _char_summary(char: Character) -> str:
    a = char.ability_scores
    mods = {
        "STR": (a.strength - 10) // 2,
        "DEX": (a.dexterity - 10) // 2,
        "CON": (a.constitution - 10) // 2,
        "INT": (a.intelligence - 10) // 2,
        "WIS": (a.wisdom - 10) // 2,
        "CHA": (a.charisma - 10) // 2,
    }
    mod_str = ", ".join(f"{k}:{'+' if v >= 0 else ''}{v}" for k, v in mods.items())
    equipped = ", ".join(i.name for i in char.inventory.items if i.equipped) or "nothing"
    conditions = ", ".join(char.conditions) if char.conditions else "none"
    return (
        f"{char.name} | {char.race} {char.char_class} Lvl {char.level} | "
        f"HP {char.current_hp}/{char.max_hp} | AC {char.armor_class} | "
        f"Prof +{char.proficiency_bonus} | {mod_str} | Equipped: {equipped} | Conditions: {conditions}"
    )


def _short_context(session: GameSession, character: Character, turns: int = 6) -> str:
    """Compact recent-history string for the assessor and dice agent."""
    lines = [f"Character: {_char_summary(character)}"]
    for entry in session.narrative_history[-turns:]:
        if entry.role == "aidm":
            lines.append(f"DM: {entry.content[:300]}")
        elif entry.role == "player":
            lines.append(f"Player: {entry.content[:150]}")
    return "\n".join(lines)


# ─── Assessor ─────────────────────────────────────────────────────────────────

_ASSESSOR_SYSTEM = _load_prompt("assessor_system.txt")


async def _run_assessor(action_text: str, context: str, model: str) -> bool:
    messages = [
        {"role": "system", "content": _ASSESSOR_SYSTEM},
        {"role": "user", "content": f"Context:\n{context}\n\nAction: {action_text}"},
    ]
    try:
        raw = await ollama_client.chat(model=model, messages=messages)
        m = re.search(r'\{[^}]*"needs_roll"[^}]*\}', raw, re.DOTALL)
        if m:
            return bool(json.loads(m.group(0)).get("needs_roll", False))
    except Exception:
        pass
    return False


# ─── Dice Agent ───────────────────────────────────────────────────────────────

_DICE_AGENT_SYSTEM = _load_prompt("dice_agent_system.txt")

_ABILITY_ALIASES: dict[str, str] = {
    "str": "strength", "dex": "dexterity", "con": "constitution",
    "int": "intelligence", "wis": "wisdom", "cha": "charisma",
    "initiative": "dexterity",
    "animal handling": "animal_handling", "sleight of hand": "sleight_of_hand",
}
_VALID_ABILITIES = {
    "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
    "acrobatics", "animal_handling", "arcana", "athletics", "deception", "history",
    "insight", "intimidation", "investigation", "medicine", "nature", "perception",
    "performance", "persuasion", "religion", "sleight_of_hand", "stealth", "survival",
}
_VALID_ROLL_TYPES = {"ability_check", "saving_throw", "attack_roll"}


async def _run_dice_agent(action_text: str, context: str, model: str) -> RollRequest | None:
    messages = [
        {"role": "system", "content": _DICE_AGENT_SYSTEM},
        {"role": "user", "content": f"Context:\n{context}\n\nAction: {action_text}"},
    ]
    try:
        raw = await ollama_client.chat(model=model, messages=messages)
        m = re.search(r'\{[^}]*"roll_type"[^}]*\}', raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            roll_type = data.get("roll_type", "ability_check")
            raw_ability = str(data.get("ability", "strength")).lower().strip()
            ability = _ABILITY_ALIASES.get(raw_ability, raw_ability)
            if ability not in _VALID_ABILITIES:
                ability = "strength"
            if roll_type not in _VALID_ROLL_TYPES:
                roll_type = "ability_check"
            dc = data.get("dc") or None
            if dc is not None:
                dc = int(dc)
            return RollRequest(roll_type=roll_type, ability=ability, dc=dc)
    except Exception:
        pass
    return None


# ─── Responder ────────────────────────────────────────────────────────────────

_RESPONDER_SYSTEM = _load_prompt("responder_system.txt")


def _build_responder_messages(
    session: GameSession,
    character: Character,
    story: Story,
    action: PlayerAction,
    roll_request: RollRequest | None,
    context_limit: int,
) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": _RESPONDER_SYSTEM}]

    char_ctx = _char_summary(character)
    story_ctx = f"Story: {story.title}\nSetting: {story.setting}\nSynopsis: {story.synopsis}"
    messages.append({"role": "user", "content": f"[CONTEXT]\n{story_ctx}\n{char_ctx}"})
    messages.append({"role": "assistant", "content": "Understood. I'll keep these details in mind."})

    for entry in session.narrative_history[-context_limit:]:
        if entry.role == "aidm":
            messages.append({"role": "assistant", "content": entry.content})
        elif entry.role in ("player", "roll"):
            messages.append({"role": "user", "content": entry.content})

    action_text = action.text
    if action.roll_result:
        r = action.roll_result
        success_text = f" — {'Success' if r.success else 'Failure'}" if r.success is not None else ""
        action_text += (
            f"\n<<ROLL RESULT: {r.label} | d20: {r.d20} + {r.modifier} = {r.total}"
            + (f" vs DC {r.dc}" if r.dc else "")
            + success_text
            + ">>"
        )
    elif roll_request:
        ability_label = roll_request.ability.replace("_", " ").title()
        dc_text = f" DC {roll_request.dc}" if roll_request.dc else ""
        action_text += (
            f"\n<<AWAITING ROLL: {ability_label} {roll_request.roll_type.replace('_', ' ')}{dc_text}"
            f" — stop the narrative before the outcome is resolved>>"
        )

    messages.append({"role": "user", "content": action_text})
    return messages


def _parse_responder_output(raw: str) -> tuple[str, list[str], Literal["start", "end"] | None]:
    narrative = raw
    scene_keywords: list[str] = []
    combat_signal: str | None = None

    kw_match = re.search(r"SCENE_KEYWORDS:\s*(.+)$", raw, re.MULTILINE)
    if kw_match:
        scene_keywords = [k.strip() for k in kw_match.group(1).split(",") if k.strip()][:3]
        narrative = narrative.replace(kw_match.group(0), "").strip()

    if "COMBAT_START" in narrative:
        combat_signal = "start"
        narrative = narrative.replace("COMBAT_START", "").strip()
    elif "COMBAT_END" in narrative:
        combat_signal = "end"
        narrative = narrative.replace("COMBAT_END", "").strip()

    # Strip any metadata tags the model echoed into its output
    narrative = re.sub(r'<<AWAITING ROLL[^>]*>>', '', narrative).strip()
    narrative = re.sub(r'<<ROLL RESULT[^>]*>>', '', narrative).strip()
    narrative = re.sub(r'\[PENDING ROLL[^\]]*\]', '', narrative).strip()
    narrative = re.sub(r'\[ROLL RESULT[^\]]*\]', '', narrative).strip()

    # Strip instruction echo: model repeating its own system prompt conditions
    echo_match = re.search(r'\n{0,2}If (?:the|this) action includes', narrative, re.IGNORECASE)
    if echo_match:
        narrative = narrative[:echo_match.start()].strip()

    return narrative, scene_keywords, combat_signal


# ─── Public API ───────────────────────────────────────────────────────────────

async def process_action(
    session: GameSession,
    character: Character,
    story: Story,
    action: PlayerAction,
    assessor_model: str,
    dice_agent_model: str,
    responder_model: str,
    context_limit: int = 50,
) -> tuple[GameSession, NarrativeEntry]:
    """Process a player action through the 3-agent pipeline and return the updated session + entry."""

    # Record player action in history
    player_entry_content = action.text
    if action.roll_result:
        r = action.roll_result
        success_str = f" ({'Success' if r.success else 'Failure'})" if r.success is not None else ""
        player_entry_content = f"{action.text}\n**{r.label}: {r.total}**{success_str}"

    session.narrative_history.append(NarrativeEntry(
        role="player",
        content=player_entry_content,
        timestamp=datetime.utcnow(),
    ))

    # Assessor + dice agent — only for fresh actions, not roll result submissions
    roll_request: RollRequest | None = None
    if not action.roll_result:
        ctx = _short_context(session, character)
        if await _run_assessor(action.text, ctx, assessor_model):
            roll_request = await _run_dice_agent(action.text, ctx, dice_agent_model)

    # Responder always runs — generates narrative for all cases
    messages = _build_responder_messages(session, character, story, action, roll_request, context_limit)
    raw = await ollama_client.chat(model=responder_model, messages=messages)
    narrative, scene_keywords, combat_signal = _parse_responder_output(raw)

    # Update session state
    if scene_keywords:
        session.current_scene_keywords = scene_keywords
    if combat_signal == "start" and not session.combat_state.active:
        session.combat_state.active = True
        session.combat_state.round = 1
    elif combat_signal == "end" and session.combat_state.active:
        session.combat_state.active = False

    session.turn_count += 1
    session.updated_at = datetime.utcnow()

    aidm_entry = NarrativeEntry(
        role="aidm",
        content=narrative,
        timestamp=datetime.utcnow(),
        roll_request=roll_request,
        scene_keywords=scene_keywords,
        combat_signal=combat_signal,
    )
    session.narrative_history.append(aidm_entry)

    return session, aidm_entry


async def start_session(
    session: GameSession,
    character: Character,
    story: Story,
    responder_model: str,
) -> NarrativeEntry:
    """Generate the opening narration for a new game session."""
    opening = story.opening_narration or f"You are about to embark on an adventure: {story.title}."
    prompt = (
        f"Begin the adventure '{story.title}'. "
        f"The character is {character.name}, a level {character.level} {character.race} {character.char_class}. "
        f"Opening narration to draw from:\n\n{opening}\n\n"
        f"Set the scene vividly. End with SCENE_KEYWORDS as instructed."
    )
    messages = [
        {"role": "system", "content": _RESPONDER_SYSTEM},
        {
            "role": "user",
            "content": (
                f"[CONTEXT]\nStory: {story.title}\nSetting: {story.setting}\n"
                f"Character: {character.name} | {character.race} {character.char_class} "
                f"Level {character.level} | HP: {character.max_hp}/{character.max_hp} | AC: {character.armor_class}"
            ),
        },
        {"role": "assistant", "content": "Understood. Ready to begin."},
        {"role": "user", "content": prompt},
    ]

    raw = await ollama_client.chat(model=responder_model, messages=messages)
    narrative, scene_keywords, _ = _parse_responder_output(raw)

    if scene_keywords:
        session.current_scene_keywords = scene_keywords

    entry = NarrativeEntry(
        role="aidm",
        content=narrative,
        timestamp=datetime.utcnow(),
        scene_keywords=scene_keywords,
    )
    session.narrative_history.append(entry)
    session.updated_at = datetime.utcnow()
    return entry
