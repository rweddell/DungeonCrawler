import React, { useEffect, useRef, useState } from 'react'
import { audioApi } from '../../services/api'
import './AmbientAudio.css'

interface AmbientAudioProps {
  keywords: string  // comma-separated string, stable across renders
  enabled: boolean
  volume: number
}

export function AmbientAudio({ keywords, enabled, volume }: AmbientAudioProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [audioName, setAudioName] = useState<string | null>(null)
  const [muted, setMuted] = useState(false)

  useEffect(() => {
    if (!enabled || !keywords) {
      audioRef.current?.pause()
      return
    }

    audioApi.getScene(keywords).then((res) => {
      if (res.audio?.url) {
        if (!audioRef.current) {
          audioRef.current = new Audio()
          audioRef.current.loop = true
        }
        const audio = audioRef.current
        audio.src = res.audio.url
        audio.volume = muted ? 0 : volume
        audio.play().catch(() => {})
        setAudioName(res.audio.name)
      }
    }).catch(() => {})
  }, [keywords, enabled])

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = muted ? 0 : volume
    }
  }, [volume, muted])

  useEffect(() => {
    return () => {
      audioRef.current?.pause()
    }
  }, [])

  if (!enabled) return null

  return (
    <div className="ambient-audio">
      {audioName && (
        <span className="audio-name" title={`Now playing: ${audioName}`}>
          🎵 {audioName.slice(0, 28)}{audioName.length > 28 ? '…' : ''}
        </span>
      )}
      <button
        className="mute-btn"
        onClick={() => setMuted((m) => !m)}
        title={muted ? 'Unmute' : 'Mute'}
      >
        {muted ? '🔇' : '🔊'}
      </button>
    </div>
  )
}
