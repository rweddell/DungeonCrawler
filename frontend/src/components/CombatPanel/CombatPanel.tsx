import React from 'react'
import type { CombatState } from '../../types'
import './CombatPanel.css'

interface CombatPanelProps {
  combat: CombatState
}

export function CombatPanel({ combat }: CombatPanelProps) {
  if (!combat.active) return null

  const currentCombatant = combat.combatants[combat.current_turn_index]

  return (
    <div className="combat-panel parchment medieval-border">
      <div className="combat-header">
        <h3 className="combat-title">⚔ Combat</h3>
        <span className="combat-round">Round {combat.round}</span>
      </div>

      <div className="initiative-list">
        <div className="section-header">Initiative Order</div>
        {combat.combatants.map((c, i) => (
          <div
            key={c.id}
            className={`initiative-row ${i === combat.current_turn_index ? 'current-turn' : ''} ${c.is_defeated ? 'defeated' : ''}`}
          >
            <span className="initiative-num">{c.initiative}</span>
            <span className={`initiative-name ${c.is_player ? 'player-name' : ''}`}>
              {c.name}
            </span>
            {c.is_player && c.hp !== null && c.max_hp !== null && (
              <span className="initiative-hp">
                {c.hp}/{c.max_hp}
              </span>
            )}
            {c.conditions.length > 0 && (
              <span className="initiative-conditions">
                {c.conditions.map((cond) => (
                  <span key={cond} className="cond-badge">{cond}</span>
                ))}
              </span>
            )}
          </div>
        ))}
      </div>

      {combat.log.length > 0 && (
        <div className="combat-log">
          <div className="section-header">Combat Log</div>
          <div className="combat-log-scroll">
            {combat.log.map((entry, i) => (
              <div key={i} className="combat-log-entry">{entry}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
