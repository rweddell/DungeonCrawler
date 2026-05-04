// ─── Character ───────────────────────────────────────────────────────────────

export interface AbilityScores {
  strength: number
  dexterity: number
  constitution: number
  intelligence: number
  wisdom: number
  charisma: number
}

export interface SavingThrows {
  strength: boolean
  dexterity: boolean
  constitution: boolean
  intelligence: boolean
  wisdom: boolean
  charisma: boolean
}

export interface Skills {
  acrobatics: boolean
  animal_handling: boolean
  arcana: boolean
  athletics: boolean
  deception: boolean
  history: boolean
  insight: boolean
  intimidation: boolean
  investigation: boolean
  medicine: boolean
  nature: boolean
  perception: boolean
  performance: boolean
  persuasion: boolean
  religion: boolean
  sleight_of_hand: boolean
  stealth: boolean
  survival: boolean
}

export interface SpellSlots {
  level_1: number
  level_2: number
  level_3: number
  level_4: number
  level_5: number
  level_6: number
  level_7: number
  level_8: number
  level_9: number
}

export interface Spell {
  name: string
  level: number
  school: string
  casting_time: string
  range: string
  components: string
  duration: string
  description: string
  prepared: boolean
}

export interface Currency {
  cp: number
  sp: number
  ep: number
  gp: number
  pp: number
}

export interface Item {
  id: string
  name: string
  quantity: number
  weight: number
  description: string
  equipped: boolean
  attuned: boolean
  item_type: string
  properties: Record<string, unknown>
}

export interface Inventory {
  items: Item[]
  currency: Currency
}

export interface Character {
  id: string
  name: string
  race: string
  char_class: string
  subclass: string
  level: number
  experience: number
  background: string
  alignment: string
  age: string
  appearance: string
  personality_traits: string
  ideals: string
  bonds: string
  flaws: string
  ability_scores: AbilityScores
  saving_throws: SavingThrows
  skills: Skills
  max_hp: number
  current_hp: number
  temp_hp: number
  hit_dice: string
  hit_dice_remaining: number
  armor_class: number
  initiative_bonus: number
  speed: number
  proficiency_bonus: number
  features: string[]
  traits: string[]
  languages: string[]
  proficiencies: string[]
  spell_slots: SpellSlots
  spell_slots_used: SpellSlots
  spells_known: Spell[]
  spell_save_dc: number
  spell_attack_bonus: number
  spellcasting_ability: string
  inventory: Inventory
  death_saves_successes: number
  death_saves_failures: number
  conditions: string[]
  notes: string
}

export interface CharacterCreate {
  name: string
  race?: string
  char_class?: string
  level?: number
  background?: string
  alignment?: string
  ability_scores?: Partial<AbilityScores>
}

// ─── Story ────────────────────────────────────────────────────────────────────

export interface NPC {
  name: string
  description: string
  role: string
}

export interface Story {
  id: string
  title: string
  synopsis: string
  opening_narration: string
  setting: string
  npcs: NPC[]
  special_rules: string[]
  tags: string[]
  is_custom: boolean
  filename: string
}

// ─── Game State ───────────────────────────────────────────────────────────────

export interface RollRequest {
  roll_type: 'ability_check' | 'saving_throw' | 'attack_roll'
  ability: string
  dc: number | null
  advantage: boolean
  disadvantage: boolean
}

export interface RollResult {
  d20: number
  modifier: number
  total: number
  dc: number | null
  success: boolean | null
  label: string
}

export interface Combatant {
  id: string
  name: string
  initiative: number
  is_player: boolean
  hp: number | null
  max_hp: number | null
  conditions: string[]
  is_defeated: boolean
}

export interface CombatState {
  active: boolean
  round: number
  current_turn_index: number
  combatants: Combatant[]
  log: string[]
}

export type NarrativeRole = 'aidm' | 'player' | 'system' | 'roll'

export interface NarrativeEntry {
  role: NarrativeRole
  content: string
  timestamp: string
  roll_request?: RollRequest | null
  roll_result?: RollResult | null
  scene_keywords: string[]
  combat_signal?: 'start' | 'end' | null
}

export interface GameSession {
  id: string
  story_id: string
  character_id: string
  narrative_history: NarrativeEntry[]
  combat_state: CombatState
  turn_count: number
  current_scene_keywords: string[]
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface SaveFileMeta {
  id: string
  character_name: string
  story_title: string
  saved_at: string
  turn_count: number
}

export interface PlayerAction {
  text: string
  roll_result?: RollResult | null
}

// ─── Settings ─────────────────────────────────────────────────────────────────

export interface RuntimeSettings {
  ollama_model: string
  assessor_model: string
  dice_agent_model: string
  responder_model: string
  context_length: number
  auto_save: boolean
  auto_save_interval: number
  audio_enabled: boolean
  audio_volume: number
  images_enabled: boolean
  theme: string
}

// ─── Images ───────────────────────────────────────────────────────────────────

export interface DeviantArtImage {
  url: string
  title: string
  author: string
  page_url: string
}
