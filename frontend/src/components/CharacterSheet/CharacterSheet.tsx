import React, { useState } from 'react'
import type { Character, CharacterCreate, AbilityScores } from '../../types'
import { charactersApi } from '../../services/api'
import './CharacterSheet.css'

const ABILITIES: (keyof AbilityScores)[] = [
  'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma',
]

const SKILL_LIST = [
  { name: 'Acrobatics', key: 'acrobatics', ability: 'DEX' },
  { name: 'Animal Handling', key: 'animal_handling', ability: 'WIS' },
  { name: 'Arcana', key: 'arcana', ability: 'INT' },
  { name: 'Athletics', key: 'athletics', ability: 'STR' },
  { name: 'Deception', key: 'deception', ability: 'CHA' },
  { name: 'History', key: 'history', ability: 'INT' },
  { name: 'Insight', key: 'insight', ability: 'WIS' },
  { name: 'Intimidation', key: 'intimidation', ability: 'CHA' },
  { name: 'Investigation', key: 'investigation', ability: 'INT' },
  { name: 'Medicine', key: 'medicine', ability: 'WIS' },
  { name: 'Nature', key: 'nature', ability: 'INT' },
  { name: 'Perception', key: 'perception', ability: 'WIS' },
  { name: 'Performance', key: 'performance', ability: 'CHA' },
  { name: 'Persuasion', key: 'persuasion', ability: 'CHA' },
  { name: 'Religion', key: 'religion', ability: 'INT' },
  { name: 'Sleight of Hand', key: 'sleight_of_hand', ability: 'DEX' },
  { name: 'Stealth', key: 'stealth', ability: 'DEX' },
  { name: 'Survival', key: 'survival', ability: 'WIS' },
]

function mod(score: number) {
  const m = Math.floor((score - 10) / 2)
  return m >= 0 ? `+${m}` : `${m}`
}

interface Props {
  characters: Character[]
  selectedId?: string
  onSelect: (char: Character) => void
  onUpdate: (char: Character) => void
}

function CreateCharacterForm({ onCreated }: { onCreated: (c: Character) => void }) {
  const [name, setName] = useState('')
  const [race, setRace] = useState('')
  const [charClass, setCharClass] = useState('')
  const [level, setLevel] = useState(1)
  const [background, setBackground] = useState('')
  const [scores, setScores] = useState<AbilityScores>({
    strength: 10, dexterity: 10, constitution: 10,
    intelligence: 10, wisdom: 10, charisma: 10,
  })
  const [creating, setCreating] = useState(false)

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setCreating(true)
    try {
      const char = await charactersApi.create({
        name, race, char_class: charClass, level, background,
        ability_scores: scores,
      })
      onCreated(char)
    } catch {
      // silently ignore
    } finally {
      setCreating(false)
    }
  }

  return (
    <form className="create-char-form parchment medieval-border" onSubmit={handleCreate}>
      <h3 className="create-char-title">New Character</h3>
      <div className="form-row">
        <label>Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div className="form-row-2col">
        <div className="form-row">
          <label>Race</label>
          <input value={race} onChange={(e) => setRace(e.target.value)} placeholder="Human" />
        </div>
        <div className="form-row">
          <label>Class</label>
          <input value={charClass} onChange={(e) => setCharClass(e.target.value)} placeholder="Fighter" />
        </div>
      </div>
      <div className="form-row-2col">
        <div className="form-row">
          <label>Level</label>
          <input type="number" min={1} max={20} value={level} onChange={(e) => setLevel(Number(e.target.value))} />
        </div>
        <div className="form-row">
          <label>Background</label>
          <input value={background} onChange={(e) => setBackground(e.target.value)} placeholder="Soldier" />
        </div>
      </div>
      <div className="ability-scores-grid">
        {ABILITIES.map((a) => (
          <div key={a} className="ability-input">
            <label>{a.slice(0, 3).toUpperCase()}</label>
            <input
              type="number" min={1} max={30}
              value={scores[a]}
              onChange={(e) => setScores((prev) => ({ ...prev, [a]: Number(e.target.value) }))}
            />
            <span className="ability-mod">{mod(scores[a])}</span>
          </div>
        ))}
      </div>
      <button type="submit" className="create-btn" disabled={creating}>
        {creating ? 'Creating...' : 'Create Character'}
      </button>
    </form>
  )
}

export function CharacterSheet({ characters, selectedId, onSelect, onUpdate }: Props) {
  const [showCreate, setShowCreate] = useState(false)
  const [allChars, setAllChars] = useState<Character[]>(characters)
  const selected = allChars.find((c) => c.id === selectedId) ?? null

  function handleCreated(c: Character) {
    setAllChars((prev) => [...prev, c])
    onSelect(c)
    setShowCreate(false)
  }

  return (
    <div className="char-sheet-panel">
      <div className="char-list">
        <h3 className="char-list-title">Characters</h3>
        {allChars.map((c) => (
          <div
            key={c.id}
            className={`char-list-item ${c.id === selectedId ? 'active' : ''}`}
            onClick={() => onSelect(c)}
          >
            <span className="char-list-name">{c.name}</span>
            <span className="char-list-sub">{c.race} {c.char_class} {c.level}</span>
          </div>
        ))}
        <button className="new-char-btn" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? '— Cancel' : '+ New Character'}
        </button>
        {showCreate && <CreateCharacterForm onCreated={handleCreated} />}
      </div>

      {selected && (
        <div className="char-sheet parchment medieval-border">
          <div className="char-sheet-header">
            <div className="char-name-block">
              <div className="char-name">{selected.name}</div>
              <div className="char-sub">
                {selected.race} {selected.char_class} {selected.subclass && `(${selected.subclass})`}
                {' '}— Level {selected.level}
              </div>
              {selected.background && (
                <div className="char-background">{selected.background} · {selected.alignment}</div>
              )}
            </div>
            <div className="char-stats-top">
              <div className="stat-pill">
                <span className="stat-label">HP</span>
                <span className="stat-value">{selected.current_hp}/{selected.max_hp}</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">AC</span>
                <span className="stat-value">{selected.armor_class}</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Prof</span>
                <span className="stat-value">+{selected.proficiency_bonus}</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Speed</span>
                <span className="stat-value">{selected.speed}ft</span>
              </div>
            </div>
          </div>

          <div className="ability-scores-row">
            {ABILITIES.map((a) => (
              <div key={a} className="ability-box">
                <div className="ability-label">{a.slice(0, 3).toUpperCase()}</div>
                <div className="ability-mod-big">{mod(selected.ability_scores[a])}</div>
                <div className="ability-score">{selected.ability_scores[a]}</div>
              </div>
            ))}
          </div>

          <div className="char-sheet-cols">
            <div className="skills-col">
              <div className="section-header">Skills</div>
              {SKILL_LIST.map((sk) => {
                const prof = selected.skills[sk.key as keyof typeof selected.skills]
                return (
                  <div key={sk.key} className={`skill-row ${prof ? 'proficient' : ''}`}>
                    <span className="skill-dot">{prof ? '●' : '○'}</span>
                    <span className="skill-name">{sk.name}</span>
                    <span className="skill-ability">{sk.ability}</span>
                  </div>
                )
              })}
            </div>
            <div className="features-col">
              {selected.features.length > 0 && (
                <>
                  <div className="section-header">Features & Traits</div>
                  {selected.features.map((f, i) => (
                    <div key={i} className="feature-item">{f}</div>
                  ))}
                </>
              )}
              {selected.conditions.length > 0 && (
                <>
                  <div className="section-header" style={{ marginTop: '0.75rem' }}>Conditions</div>
                  <div className="conditions-row">
                    {selected.conditions.map((c) => (
                      <span key={c} className="condition-badge">{c}</span>
                    ))}
                  </div>
                </>
              )}
              {selected.spells_known.length > 0 && (
                <>
                  <div className="section-header" style={{ marginTop: '0.75rem' }}>Spells</div>
                  {selected.spells_known.map((sp, i) => (
                    <div key={i} className="spell-item">
                      <span className={`spell-level level-${sp.level}`}>L{sp.level}</span>
                      {sp.name}
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
