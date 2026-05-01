import type { Character, RollRequest, RollResult } from '../types'

const SKILL_ABILITY: Record<string, keyof Character['ability_scores']> = {
  acrobatics: 'dexterity',
  animal_handling: 'wisdom',
  arcana: 'intelligence',
  athletics: 'strength',
  deception: 'charisma',
  history: 'intelligence',
  insight: 'wisdom',
  intimidation: 'charisma',
  investigation: 'intelligence',
  medicine: 'wisdom',
  nature: 'intelligence',
  perception: 'wisdom',
  performance: 'charisma',
  persuasion: 'charisma',
  religion: 'intelligence',
  sleight_of_hand: 'dexterity',
  stealth: 'dexterity',
  survival: 'wisdom',
}

function modifier(score: number): number {
  return Math.floor((score - 10) / 2)
}

function rollD20(): number {
  return Math.floor(Math.random() * 20) + 1
}

export function rollForRequest(request: RollRequest, character: Character): RollResult {
  const d20 = rollD20()
  const ability = request.ability.toLowerCase()

  let mod = 0
  const scores = character.ability_scores

  // Direct ability score
  if (ability in scores) {
    mod = modifier(scores[ability as keyof typeof scores])
  } else if (ability in SKILL_ABILITY) {
    const baseAbility = SKILL_ABILITY[ability]
    mod = modifier(scores[baseAbility])
    // Add proficiency if proficient in that skill
    const skillKey = ability as keyof Character['skills']
    if (character.skills[skillKey]) {
      mod += character.proficiency_bonus
    }
  }

  // Advantage/disadvantage
  let finalD20 = d20
  if (request.advantage) {
    const roll2 = rollD20()
    finalD20 = Math.max(d20, roll2)
  } else if (request.disadvantage) {
    const roll2 = rollD20()
    finalD20 = Math.min(d20, roll2)
  }

  const total = finalD20 + mod
  const success = request.dc !== null ? total >= request.dc : null

  const label = `${ability.charAt(0).toUpperCase() + ability.slice(1).replace(/_/g, ' ')} (${request.roll_type.replace(/_/g, ' ')})`

  return {
    d20: finalD20,
    modifier: mod,
    total,
    dc: request.dc,
    success,
    label,
  }
}
