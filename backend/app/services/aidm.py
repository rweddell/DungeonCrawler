from __future__ import annotations
import json
import re
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from app.models.character import Character
from app.models.game_state import GameMemory, GameSession, NarrativeEntry, RollRequest, PlayerAction
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


def _apply_memory_update(session: GameSession, update: GameMemory) -> None:
    existing_people = {e.split("—")[0].strip().lower() for e in session.memory.people}
    for entry in update.people:
        name = entry.split("—")[0].strip().lower()
        if name and name not in existing_people:
            session.memory.people.append(entry)
            existing_people.add(name)

    existing_places = {e.split("—")[0].strip().lower() for e in session.memory.places}
    for entry in update.places:
        name = entry.split("—")[0].strip().lower()
        if name and name not in existing_places:
            session.memory.places.append(entry)
            existing_places.add(name)

    session.memory.events.extend(update.events)


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


async def _run_assessor(action_text: str, context: str, model: str, temperature: float) -> bool:
    messages = [
        {"role": "system", "content": _ASSESSOR_SYSTEM},
        {"role": "user", "content": f"Context:\n{context}\n\nAction: {action_text}"},
    ]
    try:
        raw = await ollama_client.chat(model=model, messages=messages, options={"temperature": temperature})
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


async def _run_dice_agent(action_text: str, context: str, model: str, temperature: float) -> RollRequest | None:
    messages = [
        {"role": "system", "content": _DICE_AGENT_SYSTEM},
        {"role": "user", "content": f"Context:\n{context}\n\nAction: {action_text}"},
    ]
    try:
        raw = await ollama_client.chat(model=model, messages=messages, options={"temperature": temperature})
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

    mem = session.memory
    if mem.people or mem.places or mem.events:
        mem_lines: list[str] = []
        if mem.people:
            mem_lines.append("People: " + "; ".join(mem.people[-20:]))
        if mem.places:
            mem_lines.append("Places: " + "; ".join(mem.places[-20:]))
        if mem.events:
            mem_lines.append("Past events: " + "; ".join(mem.events[-10:]))
        messages.append({"role": "user", "content": "[MEMORY]\n" + "\n".join(mem_lines)})
        messages.append({"role": "assistant", "content": "Memory noted."})

    for entry in session.narrative_history[-context_limit:]:
        if entry.role == "aidm" and entry.content:
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


def _parse_responder_output(raw: str) -> tuple[str, list[str], Literal["start", "end"] | None, GameMemory]:
    narrative = raw
    scene_keywords: list[str] = []
    combat_signal: str | None = None

    # Extract keywords from raw before any stripping, then wipe every
    # SCENE_KEYWORDS line from narrative. Tolerates: different casing,
    # SCENE KEYWORDS (space), **SCENE_KEYWORDS** (bold), SCENE\_KEYWORDS
    # (markdown-escaped underscore that LLMs sometimes emit).
    kw_match = re.search(r'\*{0,2}SCENE\\?[_ ]KEYWORDS\*{0,2}\s*:\s*(.+)', raw, re.IGNORECASE)
    if kw_match:
        scene_keywords = [k.strip().strip('*') for k in kw_match.group(1).strip().split(",") if k.strip().strip('*')][:3]
    narrative = re.sub(r'^[ \t]*\*{0,2}SCENE\\?[_ ]KEYWORDS\*{0,2}[ \t]*:[ \t]*.+$\n?', '', narrative, flags=re.MULTILINE | re.IGNORECASE).strip()

    # Match COMBAT_START/COMBAT_END tokens and COMBAT: <value> lines.
    # The \\? handles the backslash-escaped variant the model sometimes emits (COMBAT\_START).
    combat_match = re.search(r'^[ \t]*COMBAT(?:\\?_|\s*:\s*)(\S+)[ \t]*$', raw, re.MULTILINE | re.IGNORECASE)
    if combat_match:
        value = combat_match.group(1).lower().lstrip('\\')
        if value in ("start", "combat_start", "begin", "active"):
            combat_signal = "start"
        elif value in ("end", "combat_end", "over", "finished"):
            combat_signal = "end"
    narrative = re.sub(r'^[ \t]*COMBAT(?:\\?_(?:START|END)|\s*:\s*\S+)[ \t]*$\n?', '', narrative, flags=re.MULTILINE | re.IGNORECASE).strip()

    # Strip inline marker tags (model echoing roll-state placeholders)
    narrative = re.sub(r'<<[A-Z][A-Z _]*:[^>]*>>', '', narrative).strip()
    narrative = re.sub(r'\[(?:PENDING|ROLL)[^\]]*\]', '', narrative).strip()

    # Strip section-header lines echoed from the system prompt.
    # Matches bare label lines like "ROLL HANDLING —", "GENERAL RULES:", "OUTPUT RULE:", etc.
    _HEADER_PAT = (
        r'^[ \t]*(?:'
        r'ROLL[ _]HANDLING'
        r'|GENERAL[ _]RULES'
        r'|OUTPUT[ _]RULE'
        r'|SCENE[ _]KEYWORDS'
        r'|MEMORY'
        r'|COMBAT'
        r'|DC'
        r'|ABILITY'
        r'|ROLL[ _]TYPE'
        r'|OOC'
        r'|OUT[ _]OF[ _]CHARACTER'
        r')[ \t]*[:\-—].*$\n?'
    )
    narrative = re.sub(_HEADER_PAT, '', narrative, flags=re.MULTILINE | re.IGNORECASE).strip()

    # Extract MEMORY_ entries from raw (handles both MEMORY_TAG and MEMORY\_TAG),
    # then strip all such lines from the narrative.
    memory_update = GameMemory()
    for tag_pat, target in (
        (r'MEMORY\\?_PERSON', 'people'),
        (r'MEMORY\\?_PLACE', 'places'),
        (r'MEMORY\\?_EVENT', 'events'),
    ):
        for m in re.finditer(rf'^[ \t]*{tag_pat}[ \t]*:[ \t]*(.+)$', raw, re.MULTILINE | re.IGNORECASE):
            getattr(memory_update, target).append(m.group(1).strip())
    narrative = re.sub(r'^[ \t]*MEMORY\\?_(?:PERSON|PLACE|EVENT)[ \t]*:.+$\n?', '', narrative, flags=re.MULTILINE | re.IGNORECASE).strip()

    # Truncate at a markdown thematic break (--- *** ___) — model playing player's turn.
    hr_match = re.search(r'\n[ \t]*[-*_]{3,}[ \t]*(\n|$)', narrative)
    if hr_match and hr_match.start() > 0:
        narrative = narrative[:hr_match.start()].strip()

    # Truncate at instruction-echo phrases the model sometimes repeats verbatim.
    for echo_pat in (
        r'\n{0,2}If (?:the|this) action includes',
        r'\n{0,2}(?:ROLL HANDLING|GENERAL RULES|OUTPUT RULE)\b',
    ):
        m = re.search(echo_pat, narrative, re.IGNORECASE)
        if m and m.start() > 0:
            narrative = narrative[:m.start()].strip()

    return narrative, scene_keywords, combat_signal, memory_update


# ─── Public API ───────────────────────────────────────────────────────────────

async def process_action(
    session: GameSession,
    character: Character,
    story: Story,
    action: PlayerAction,
    assessor_model: str,
    dice_agent_model: str,
    responder_model: str,
    assessor_temperature: float = 0.1,
    dice_agent_temperature: float = 0.1,
    responder_temperature: float = 0.8,
    context_limit: int = 50,
) -> tuple[GameSession, NarrativeEntry]:
    """Process a player action through the 3-agent pipeline and return the updated session + entry."""

    # Build display-friendly player entry content (not appended yet — see below)
    player_entry_content = action.text
    if action.roll_result:
        r = action.roll_result
        success_str = f" ({'Success' if r.success else 'Failure'})" if r.success is not None else ""
        player_entry_content = f"{action.text}\n**{r.label}: {r.total}**{success_str}"

    # Assessor + dice agent — only for fresh actions, not roll result submissions
    roll_request: RollRequest | None = None
    if not action.roll_result:
        ctx = _short_context(session, character)
        if await _run_assessor(action.text, ctx, assessor_model, assessor_temperature):
            roll_request = await _run_dice_agent(action.text, ctx, dice_agent_model, dice_agent_temperature)

    # Responder always runs — generates narrative for all cases.
    # The player entry is NOT yet in narrative_history so it cannot appear in the
    # history loop AND as the explicit final user message at the same time.
    messages = _build_responder_messages(session, character, story, action, roll_request, context_limit)
    raw = await ollama_client.chat(model=responder_model, messages=messages, options={"temperature": responder_temperature})
    narrative, scene_keywords, combat_signal, memory_update = _parse_responder_output(raw)

    # Commit both entries together after generation
    session.narrative_history.append(NarrativeEntry(
        role="player",
        content=player_entry_content,
        timestamp=datetime.now(timezone.utc),
    ))

    aidm_entry = NarrativeEntry(
        role="aidm",
        content=narrative,
        timestamp=datetime.now(timezone.utc),
        roll_request=roll_request,
        scene_keywords=scene_keywords,
        combat_signal=combat_signal,
    )
    session.narrative_history.append(aidm_entry)

    # Update session state
    if scene_keywords:
        session.current_scene_keywords = scene_keywords
    _apply_memory_update(session, memory_update)
    if combat_signal == "start" and not session.combat_state.active:
        session.combat_state.active = True
        session.combat_state.round = 1
    elif combat_signal == "end" and session.combat_state.active:
        session.combat_state.active = False

    session.turn_count += 1
    session.updated_at = datetime.now(timezone.utc)

    return session, aidm_entry


async def start_session(
    session: GameSession,
    character: Character,
    story: Story,
    responder_model: str,
    responder_temperature: float = 0.8,
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

    raw = await ollama_client.chat(model=responder_model, messages=messages, options={"temperature": responder_temperature})
    narrative, scene_keywords, _, memory_update = _parse_responder_output(raw)

    if scene_keywords:
        session.current_scene_keywords = scene_keywords
    _apply_memory_update(session, memory_update)

    entry = NarrativeEntry(
        role="aidm",
        content=narrative,
        timestamp=datetime.now(timezone.utc),
        scene_keywords=scene_keywords,
    )
    session.narrative_history.append(entry)
    session.updated_at = datetime.now(timezone.utc)
    return entry


async def process_action_stream(
    session: GameSession,
    character: Character,
    story: Story,
    action: PlayerAction,
    assessor_model: str,
    dice_agent_model: str,
    responder_model: str,
    assessor_temperature: float = 0.1,
    dice_agent_temperature: float = 0.1,
    responder_temperature: float = 0.8,
    context_limit: int = 50,
) -> AsyncGenerator[dict, None]:
    """Stream the responder's output chunk by chunk, then yield a final 'done' event."""

    player_entry_content = action.text
    if action.roll_result:
        r = action.roll_result
        success_str = f" ({'Success' if r.success else 'Failure'})" if r.success is not None else ""
        player_entry_content = f"{action.text}\n**{r.label}: {r.total}**{success_str}"

    roll_request: RollRequest | None = None
    if not action.roll_result:
        ctx = _short_context(session, character)
        if await _run_assessor(action.text, ctx, assessor_model, assessor_temperature):
            roll_request = await _run_dice_agent(action.text, ctx, dice_agent_model, dice_agent_temperature)

    # When a roll is required, don't run the responder yet.
    # Return the roll card immediately; the responder runs after the player submits their result.
    if roll_request is not None:
        async def _await_roll() -> AsyncGenerator[dict, None]:
            session.narrative_history.append(NarrativeEntry(
                role="player",
                content=player_entry_content,
                timestamp=datetime.now(timezone.utc),
            ))
            aidm_entry = NarrativeEntry(
                role="aidm",
                content="",
                roll_request=roll_request,
                timestamp=datetime.now(timezone.utc),
            )
            session.narrative_history.append(aidm_entry)
            session.turn_count += 1
            session.updated_at = datetime.now(timezone.utc)
            yield {"type": "done", "entry": aidm_entry, "session": session}
        return _await_roll()

    messages = _build_responder_messages(session, character, story, action, roll_request, context_limit)

    async def _generate() -> AsyncGenerator[dict, None]:
        full_text = ""
        async for chunk in ollama_client.chat_stream(
            model=responder_model,
            messages=messages,
            options={"temperature": responder_temperature},
        ):
            full_text += chunk

        narrative, scene_keywords, combat_signal, memory_update = _parse_responder_output(full_text)

        session.narrative_history.append(NarrativeEntry(
            role="player",
            content=player_entry_content,
            timestamp=datetime.now(timezone.utc),
        ))
        aidm_entry = NarrativeEntry(
            role="aidm",
            content=narrative,
            timestamp=datetime.now(timezone.utc),
            roll_request=roll_request,
            scene_keywords=scene_keywords,
            combat_signal=combat_signal,
        )
        session.narrative_history.append(aidm_entry)

        if scene_keywords:
            session.current_scene_keywords = scene_keywords
        _apply_memory_update(session, memory_update)
        if combat_signal == "start" and not session.combat_state.active:
            session.combat_state.active = True
            session.combat_state.round = 1
        elif combat_signal == "end" and session.combat_state.active:
            session.combat_state.active = False

        session.turn_count += 1
        session.updated_at = datetime.now(timezone.utc)

        yield {"type": "chunk", "text": narrative}
        yield {"type": "done", "entry": aidm_entry, "session": session}

    return _generate()
