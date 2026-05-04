import React, { useEffect, useState } from 'react'
import type { RuntimeSettings } from '../../types'
import { settingsApi, ollamaApi } from '../../services/api'
import './Settings.css'

interface SettingsProps {
  onClose: () => void
  onSettingsChange: (s: RuntimeSettings) => void
}

export function Settings({ onClose, onSettingsChange }: SettingsProps) {
  const [settings, setSettings] = useState<RuntimeSettings | null>(null)
  const [models, setModels] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    settingsApi.get().then(setSettings)
    ollamaApi.listModels()
      .then((res) => setModels(res.models.map((m) => m.name)))
      .catch(() => setModels([]))
  }, [])

  async function handleSave() {
    if (!settings) return
    setSaving(true)
    try {
      const saved = await settingsApi.update(settings)
      onSettingsChange(saved)
      setSaved(true)
      setTimeout(() => setSaved(false), 1500)
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  if (!settings) return <div className="settings-loading"><div className="spinner" /></div>

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel parchment medieval-border" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2 className="settings-title">Settings</h2>
          <button className="settings-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="settings-section">
          <h3 className="settings-section-title">AI Agents</h3>

          <div className="setting-row setting-row--stacked">
            <label className="setting-label">
              Assessor
              <span className="setting-hint">Decides whether a dice roll is needed</span>
            </label>
            <select
              className="setting-select"
              value={settings.assessor_model}
              onChange={(e) => setSettings({ ...settings, assessor_model: e.target.value })}
            >
              {models.length === 0 && (
                <option value={settings.assessor_model}>{settings.assessor_model}</option>
              )}
              {models.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div className="setting-row setting-row--stacked">
            <label className="setting-label">
              Dice Agent
              <span className="setting-hint">Determines roll type, ability, and DC</span>
            </label>
            <select
              className="setting-select"
              value={settings.dice_agent_model}
              onChange={(e) => setSettings({ ...settings, dice_agent_model: e.target.value })}
            >
              {models.length === 0 && (
                <option value={settings.dice_agent_model}>{settings.dice_agent_model}</option>
              )}
              {models.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div className="setting-row setting-row--stacked">
            <label className="setting-label">
              Responder
              <span className="setting-hint">Narrates the story and resolves outcomes</span>
            </label>
            <select
              className="setting-select"
              value={settings.responder_model}
              onChange={(e) => setSettings({ ...settings, responder_model: e.target.value })}
            >
              {models.length === 0 && (
                <option value={settings.responder_model}>{settings.responder_model}</option>
              )}
              {models.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div className="setting-row">
            <label className="setting-label">Context Length (turns)</label>
            <input
              type="number" min={5} max={200}
              className="setting-input"
              value={settings.context_length}
              onChange={(e) => setSettings({ ...settings, context_length: Number(e.target.value) })}
            />
          </div>
        </div>

        <div className="settings-section">
          <h3 className="settings-section-title">Auto-Save</h3>
          <div className="setting-row">
            <label className="setting-label">Enable Auto-Save</label>
            <input
              type="checkbox"
              checked={settings.auto_save}
              onChange={(e) => setSettings({ ...settings, auto_save: e.target.checked })}
            />
          </div>
          <div className="setting-row">
            <label className="setting-label">Save Every (turns)</label>
            <input
              type="number" min={1} max={50}
              className="setting-input"
              value={settings.auto_save_interval}
              disabled={!settings.auto_save}
              onChange={(e) => setSettings({ ...settings, auto_save_interval: Number(e.target.value) })}
            />
          </div>
        </div>

        <div className="settings-section">
          <h3 className="settings-section-title">Audio</h3>
          <div className="setting-row">
            <label className="setting-label">Enable Ambient Audio</label>
            <input
              type="checkbox"
              checked={settings.audio_enabled}
              onChange={(e) => setSettings({ ...settings, audio_enabled: e.target.checked })}
            />
          </div>
          <div className="setting-row">
            <label className="setting-label">Volume</label>
            <input
              type="range" min={0} max={1} step={0.05}
              className="setting-range"
              value={settings.audio_volume}
              disabled={!settings.audio_enabled}
              onChange={(e) => setSettings({ ...settings, audio_volume: Number(e.target.value) })}
            />
            <span className="setting-range-val">{Math.round(settings.audio_volume * 100)}%</span>
          </div>
        </div>

        <div className="settings-section">
          <h3 className="settings-section-title">Display</h3>
          <div className="setting-row">
            <label className="setting-label">Show Scene Images</label>
            <input
              type="checkbox"
              checked={settings.images_enabled}
              onChange={(e) => setSettings({ ...settings, images_enabled: e.target.checked })}
            />
          </div>
        </div>

        <div className="settings-footer">
          {saved && <span className="saved-badge">Saved!</span>}
          <button className="save-settings-btn" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
