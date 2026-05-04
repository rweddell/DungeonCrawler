# DungeonCrawler

An AI-powered Dungeon Master companion app for playing D&D 5th Edition solo adventures. The AI Dungeon Master (AIDM) is driven by a locally hosted LLM via [Ollama](https://ollama.com), with a parchment-themed UI, dynamic scene artwork from DeviantArt, ambient audio from Freesound, and full 5e character sheet management.

---

## Features

- **AI Dungeon Master** — Narratives in second person, skill checks, combat, and story continuity powered by your local Ollama model
- **Inline Dice Rolls** — When the AIDM calls for a check, click to roll a d20 with your character's modifier applied automatically
- **Full 5e Character Sheet** — Ability scores, skills, saving throws, spells, HP tracking, conditions, and more
- **Inventory System** — Items, currency (CP/SP/EP/GP/PP), equip/attune, encumbrance
- **Story System** — Three built-in adventures; upload your own `.json` story files (see [Custom Stories](#custom-stories))
- **Save / Load** — Manual and auto-save game sessions as JSON files
- **Scene Imagery** — DeviantArt images fetched based on scene keywords extracted from the AIDM's narration
- **Ambient Audio** — Scene-appropriate audio loops from Freesound (tavern chatter, cave drips, combat drums, etc.)
- **Combat Sidebar** — Initiative order, HP tracker, conditions, and a scrollable combat log
- **Settings Page** — Switch Ollama models mid-session, tune context length, toggle audio and images, configure auto-save

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| [Ollama](https://ollama.com) | Latest | Must be running locally with at least one model pulled |
| Python | 3.11+ | |
| [uv](https://docs.astral.sh/uv/) | Latest | Python package manager |
| Node.js | 18+ | |
| npm | 9+ | Comes with Node.js |

Install `uv` with:
```bash
pip install uv
```

Pull an Ollama model (if you haven't already):
```bash
ollama pull llama3
```

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/yourname/DungeonCrawler.git
cd DungeonCrawler
cp .env.example .env
```

Edit `.env` and fill in your API credentials (both are optional — the app runs without them):

```
DEVIANTART_CLIENT_ID=your_id_here
DEVIANTART_CLIENT_SECRET=your_secret_here
FREESOUND_API_KEY=your_key_here
```

- **DeviantArt** credentials: [deviantart.com/developers](https://www.deviantart.com/developers/)
- **Freesound** API key: [freesound.org/apiv2/apply](https://freesound.org/apiv2/apply/)

### 2. Install dependencies

```bash
# Backend
cd backend
uv sync

# Frontend
cd ../frontend
npm install
```

---

## Running the App

### Quick start (all-in-one)

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Mac / Linux / Git Bash:**
```bash
./start.sh
```

This starts Ollama, the backend, and the frontend in separate terminal windows and opens `http://localhost:5173` in your browser.

### Manual start

Run each in a separate terminal:

```bash
# 1. Start Ollama (if not already running)
ollama serve

# 2. Start the backend
cd backend
uv run uvicorn app.main:app --reload --port 8000

# 3. Start the frontend
cd frontend
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173).

---

## Playing Your First Game

1. **Stories tab** — Pick a built-in adventure or upload your own `.json` story file (see [Custom Stories](#custom-stories))
2. **Character tab** — Create a new character (name, race, class, ability scores)
3. Click **▶ Begin Adventure** in the navigation bar
4. Type your actions in the text box at the bottom (e.g., *"I search the chest"*, *"I attack the goblin with my longsword"*)
5. When the AIDM calls for a roll, a **🎲 Roll d20** button appears inline — click it to roll with your modifier applied
6. Use the **💾 Save** button in the Saves tab at any time; auto-save runs every 5 turns by default

---

## Built-in Stories

| Title | Description | Difficulty |
|-------|-------------|------------|
| The Lost Mine of Phandelver | Classic introductory adventure in the Forgotten Realms | Beginner |
| Curse of Strahd | Gothic horror in the dread domain of Barovia | Advanced |
| The Sunken Library of Aldrath | Exploration of flooded coastal ruins | Intermediate |

---

## Custom Stories

Stories must be uploaded as `.json` files. Drop them into `backend/app/data/stories/` directly, or upload them through the **Stories** tab in the UI.

### JSON Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier — use the filename without `.json` (e.g. `my-story`) |
| `title` | string | Yes | Displayed in the story selector |
| `synopsis` | string | No | Short description shown before starting |
| `opening_narration` | string | Recommended | Opening prose the AIDM uses to set the first scene; more detail = better opening |
| `setting` | string | Recommended | World, region, and tone — included in every AIDM prompt for consistency |
| `npcs` | array | No | Key NPCs; each has `name`, `description`, and `role` |
| `special_rules` | array of strings | No | House rules or special mechanics the AIDM should respect |
| `tags` | array of strings | No | Used for filtering/search in the story selector |

> `is_custom` and `filename` are set automatically — do not include them.

### Minimal example

```json
{
  "id": "the-haunted-manor",
  "title": "The Haunted Manor"
}
```

### Full example

```json
{
  "id": "the-haunted-manor",
  "title": "The Haunted Manor",
  "synopsis": "A crumbling noble estate hides a terrible secret beneath its floors.",
  "opening_narration": "Rain lashes the iron gates of Blackmoor Manor as you arrive at dusk. The caretaker warned you never to venture into the east wing after dark — but the screaming started an hour ago and has not stopped.",
  "setting": "A Gothic manor on the edge of a dying village in a land blighted by old magic. The estate is three stories of rotting wood and cold stone, its halls haunted by the restless dead.",
  "npcs": [
    {
      "name": "Lord Aldric",
      "description": "The spectral former master of the manor, bound to the estate by an unbroken oath",
      "role": "antagonist"
    },
    {
      "name": "Mira the Caretaker",
      "description": "An elderly woman who has tended the manor for forty years and refuses to leave",
      "role": "guide"
    }
  ],
  "special_rules": [
    "Undead enemies are resistant to non-magical weapons",
    "Wisdom saving throws vs. DC 12 are required when witnessing a horrific scene or gain the Frightened condition"
  ],
  "tags": ["gothic", "horror", "undead", "exploration"]
}
```

---

## Project Structure

```
DungeonCrawler/
├── backend/               # FastAPI (Python)
│   ├── app/
│   │   ├── main.py        # App entrypoint
│   │   ├── config.py      # Settings & env vars
│   │   ├── models/        # Pydantic v2 data models
│   │   ├── services/      # Business logic (AIDM, Ollama, DeviantArt, etc.)
│   │   ├── routers/       # REST API endpoints
│   │   └── data/          # JSON saves, characters, stories, audio cache
│   ├── tests/
│   └── pyproject.toml
├── frontend/              # React + Vite (TypeScript)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/    # All UI components
│   │   ├── hooks/         # useGameState (global), useDiceRoll
│   │   ├── services/      # API client wrappers
│   │   └── types/         # Shared TypeScript types
│   └── package.json
├── .env.example
├── start.ps1              # Windows launch script
├── start.sh               # Bash launch script
└── README.md
```

---

## Configuration

All settings are in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_DEFAULT_MODEL` | `llama3` | Default model (overridable in Settings) |
| `DEVIANTART_CLIENT_ID` | — | DeviantArt OAuth2 client ID |
| `DEVIANTART_CLIENT_SECRET` | — | DeviantArt OAuth2 client secret |
| `FREESOUND_API_KEY` | — | Freesound API key |
| `BACKEND_PORT` | `8000` | Backend server port |
| `AUTO_SAVE_INTERVAL` | `5` | Auto-save every N turns |
| `MAX_CONTEXT_TURNS` | `50` | AIDM conversation history depth |

In-app settings (model, context length, audio, images) can be changed at any time via the **⚙ Settings** button and persist to `backend/app/data/settings.json`.

---

## API

The backend exposes a REST API at `http://localhost:8000/api/v1`. Interactive docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) when the backend is running.

---

## Development

```bash
# Run backend tests
cd backend
uv run pytest

# Type-check frontend
cd frontend
npx tsc --noEmit
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, TypeScript |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| LLM | Ollama (local), model configurable |
| Storage | JSON flat files |
| Images | DeviantArt API (OAuth2 Client Credentials) |
| Audio | Freesound.org API |
| Package managers | `uv` (Python), `npm` (Node) |
