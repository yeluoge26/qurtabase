# OBS Studio Setup Guide — AI Football Quant Terminal

## Prerequisites
- OBS Studio 30+ (obs-websocket 5.x built-in)
- Browser Source plugin
- Terminal running at http://localhost:5173

---

## Scene Collection: Football Quant Terminal

### Scene 1: PRE-MATCH (赛前预热)
- **When**: Before kickoff, showing countdown
- **Sources**:
  - Color Source (#0E1117, 1920x1080) — background
  - Browser Source (http://localhost:5173, 1920x1080) — main terminal
  - Text (GDI+): "KICKOFF IN XX:XX" (IBM Plex Mono, 36px, #F4C430)
- **Transition**: Cut, 0ms

### Scene 2: LIVE TRADING (主场景)
- **When**: During match, 90% of stream time
- **Sources**:
  - Color Source (#0E1117) — background
  - Browser Source (http://localhost:5173, 1920x1080) — main terminal
  - Browser Source (overlay, http://localhost:5173/signal-overlay, 400x200) — signal focus overlay (hidden by default)
- **Transition**: Fade, 300ms

### Scene 3: SIGNAL FOCUS (信号放大)
- **When**: On signal confirm, 5-10 seconds
- **Sources**:
  - Same as LIVE TRADING but with signal overlay browser source visible
  - Stinger transition: 6s zoom effect on signal area
- **Hotkey**: F1

### Scene 4: POST-MATCH SUMMARY (赛后总结)
- **When**: After full time
- **Sources**:
  - Color Source (#0E1117) — background
  - Browser Source (http://localhost:5173, 1920x1080) — terminal showing PostMatchSummary
- **Transition**: Fade, 500ms

---

## Layer Structure (Scene 2 — LIVE TRADING)

| Layer | Source Type     | Details                                                              |
|-------|----------------|----------------------------------------------------------------------|
| 6     | Text (GDI+)    | Disclaimer "DATA VISUALIZATION ONLY" (bottom 20px, 10px, #3D4654)   |
| 5     | Browser Source  | TrackRecord overlay (fixed bottom-right, 300x150)                    |
| 4     | Browser Source  | AI voice status ("AI SPEAKING...", top-right)                        |
| 3     | Browser Source  | Signal overlay (hidden, toggle on F1)                                |
| 2     | Browser Source  | Main terminal (1920x1080)                                           |
| 1     | Color Source    | Background #0E1117                                                   |

---

## Hotkey Mapping

| Key | Action                            |
|-----|-----------------------------------|
| F1  | Switch to SIGNAL FOCUS scene      |
| F2  | Switch to LIVE TRADING scene      |
| F3  | Switch to POST-MATCH SUMMARY scene|
| F4  | Toggle TTS mute/unmute            |

---

## Output Settings
- **Resolution**: 1920x1080 (canvas & output)
- **FPS**: 30
- **Encoder**: x264 or NVENC
- **Bitrate**: 6000 kbps
- **Keyframe interval**: 2 seconds
- **Audio**: TTS at -3dB, ambient at -28dB

---

## Browser Source Settings
- **URL**: http://localhost:5173
- **Width**: 1920, **Height**: 1080
- **FPS**: 30
- **CSS**: (leave empty, terminal has its own styles)
- **[x]** Shutdown source when not visible
- **[x]** Refresh browser when scene becomes active
- **[x]** Use custom frame rate

---

## YouTube RTMPS Streaming
1. Go to YouTube Studio → Live → Stream
2. Copy Stream Key
3. OBS → Settings → Stream → Service: YouTube RTMPS
4. Paste Stream Key
5. Start Streaming

---

## obs-websocket Integration (for automated scene switching)
- Port: 4455 (default)
- Protocol: obs-websocket 5.x
- Use the terminal's event system to trigger scene changes:
  - Signal Confirm → Switch to SIGNAL FOCUS for 8s → back to LIVE
  - Full Time → Switch to POST-MATCH SUMMARY
