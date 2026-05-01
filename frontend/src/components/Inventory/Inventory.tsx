import React, { useState } from 'react'
import type { Character, Item } from '../../types'
import { charactersApi } from '../../services/api'
import './Inventory.css'

interface InventoryProps {
  character: Character
  onUpdate: (char: Character) => void
}

export function Inventory({ character, onUpdate }: InventoryProps) {
  const [addName, setAddName] = useState('')
  const [addQty, setAddQty] = useState(1)
  const [addType, setAddType] = useState('misc')
  const [adding, setAdding] = useState(false)
  const [showAdd, setShowAdd] = useState(false)

  const inv = character.inventory
  const totalWeight = inv.items.reduce((s, i) => s + i.weight * i.quantity, 0)

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!addName.trim()) return
    setAdding(true)
    try {
      const item = await charactersApi.addItem(character.id, {
        name: addName,
        quantity: addQty,
        item_type: addType,
      })
      const updated: Character = {
        ...character,
        inventory: { ...inv, items: [...inv.items, item] },
      }
      onUpdate(updated)
      setAddName('')
      setAddQty(1)
      setShowAdd(false)
    } catch {
      // ignore
    } finally {
      setAdding(false)
    }
  }

  async function toggleEquip(item: Item) {
    try {
      const updated = await charactersApi.updateItem(character.id, item.id, {
        equipped: !item.equipped,
      })
      const newItems = inv.items.map((i) => (i.id === item.id ? updated : i))
      onUpdate({ ...character, inventory: { ...inv, items: newItems } })
    } catch {
      // ignore
    }
  }

  async function removeItem(itemId: string) {
    try {
      await charactersApi.removeItem(character.id, itemId)
      onUpdate({ ...character, inventory: { ...inv, items: inv.items.filter((i) => i.id !== itemId) } })
    } catch {
      // ignore
    }
  }

  const currencies = [
    { label: 'CP', value: inv.currency.cp },
    { label: 'SP', value: inv.currency.sp },
    { label: 'EP', value: inv.currency.ep },
    { label: 'GP', value: inv.currency.gp },
    { label: 'PP', value: inv.currency.pp },
  ]

  return (
    <div className="inventory-panel parchment medieval-border">
      <h3 className="inventory-title">Inventory</h3>

      <div className="currency-row">
        {currencies.map((c) => (
          <div key={c.label} className="currency-item">
            <span className="currency-label">{c.label}</span>
            <span className="currency-value">{c.value}</span>
          </div>
        ))}
      </div>

      <div className="weight-line">Weight: {totalWeight.toFixed(1)} lbs</div>

      <div className="items-list">
        {inv.items.length === 0 && (
          <div className="items-empty">No items</div>
        )}
        {inv.items.map((item) => (
          <div key={item.id} className={`item-row ${item.equipped ? 'equipped' : ''}`}>
            <span className="item-qty">{item.quantity}×</span>
            <span className="item-name">{item.name}</span>
            <span className="item-type">{item.item_type}</span>
            <div className="item-actions">
              <button
                className={`equip-btn ${item.equipped ? 'on' : ''}`}
                onClick={() => toggleEquip(item)}
                title={item.equipped ? 'Unequip' : 'Equip'}
              >
                {item.equipped ? '⚔' : '○'}
              </button>
              <button className="remove-btn" onClick={() => removeItem(item.id)} title="Remove">✕</button>
            </div>
          </div>
        ))}
      </div>

      {showAdd ? (
        <form className="add-item-form" onSubmit={handleAdd}>
          <input
            value={addName}
            onChange={(e) => setAddName(e.target.value)}
            placeholder="Item name"
            className="add-item-input"
            autoFocus
          />
          <div className="add-item-row">
            <input
              type="number" min={1}
              value={addQty}
              onChange={(e) => setAddQty(Number(e.target.value))}
              className="add-qty-input"
              style={{ width: 52 }}
            />
            <select
              value={addType}
              onChange={(e) => setAddType(e.target.value)}
              className="add-type-select"
            >
              {['misc', 'weapon', 'armor', 'potion', 'spell_focus', 'tool', 'treasure'].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <button type="submit" className="add-confirm-btn" disabled={adding}>Add</button>
            <button type="button" className="add-cancel-btn" onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </form>
      ) : (
        <button className="add-item-btn" onClick={() => setShowAdd(true)}>+ Add Item</button>
      )}
    </div>
  )
}
