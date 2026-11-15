# System Architecture - PROXY BOT WARS

PROXY BOT WARS is engineered with a modular, decoupled architecture where the central simulation engine is completely independent of participant bot scripts, subprocess runners, databases, and front-end visualizers.

---

## 1. High-Level Architectural Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      PARTICIPANT BOTS                       │
│  [StarterBot.py]   [BaselineBot.py]   [CustomBot.py]         │
└───────────────────────────┬─────────────────────────────────┘
                            │ (JSON lines over STDIN / STDOUT)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   MATCH RUNNER / EXECUTOR                   │
│  • Process Isolation      • Turn Timeout (1.0s)             │
│  • Memory & Crash Safety  • AST Submission Validator        │
└───────────────────────────┬─────────────────────────────────┘
                            │ (Validated Action Dictionaries)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CENTRAL GAME ENGINE                      │
│                                                             │
│  1. Generate Restricted Observations (Fog of War)           │
│  2. Execute Bots & Parse JSON                               │
│  3. Validate Actions & Deduplicate                          │
│  4. Resolve Movement (Chebyshev Distance & Rebound Checks)  │
│  5. Resolve Simultaneous Combat & Base / Turret Defenses     │
│  6. Resolve Resource Mining & Base Passive Income           │
│  7. Resolve Engineer Construction, Repairs & Control Zones  │
│  8. Resolve Unit Training                                   │
│  9. Update Visibility & Explored Maps                       │
│ 10. Check Victory Conditions & Record Replay Frame          │
└───────────────────────┬─────────────────────────┬───────────┘
                        │                         │
                        ▼                         ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│     SQLITE TOURNAMENT DB      │ │   LIVE VISUALIZER ARENA   │
│  • Teams & Submissions        │ │   • HTML5 Canvas 2D       │
│  • Match Records & Scores     │ │   • Unit Telemetry & HUD  │
│  • Leaderboard & Brackets     │ │   • Full Turn Scrubber    │
└───────────────────────────────┘ └───────────────────────────┘
```

---

## 2. Deterministic Turn Sequence

Every turn executes the following 10 steps in deterministic order:

1. **Fog of War Observation Generation:**
   The `VisibilitySystem` computes the Euclidean visibility radius for all alive units, base, and turrets. Any enemy units or unrevealed terrain outside this radius are omitted from the observation JSON.
2. **Bot Invocation:**
   `BotProcessClient` pipes the JSON observation to the bot's `stdin` and awaits a single-line JSON response on `stdout`. A strict 1.0s timeout is enforced.
3. **Action Validation:**
   `BotOutputValidator` parses the output, validates fields against formal schemas, checks unit action uniqueness, and catches crashes.
4. **Movement Resolution:**
   Units move up to their `speed` stat. Out-of-bounds moves, obstacle collisions, and blocked cells are caught. If two units move to the same destination on the same turn, both bounce back safely.
5. **Simultaneous Combat Resolution:**
   All attacks declared in the turn are validated against range. Damage is applied simultaneously at the conclusion of the combat step so neither player gains an arbitrary first-mover advantage. Base and turret defensive attacks trigger automatically.
6. **Resource Gathering & Passive Income:**
   Miners adjacent to resource deposits harvest 10 units. Both team bases generate +5 passive income.
7. **Construction, Repair & Control Zones:**
   Engineers place barricades or turrets, or repair friendly units. Uncontested presence in control zones advances capture counters; captured zones award +2 points per turn.
8. **Unit Production:**
   Base trains requested units if sufficient treasury resources exist, spawning the unit on an empty adjacent cell.
9. **Visibility Update:**
   Explored cell history is updated for scoring and visualizer telemetry.
10. **Victory Evaluation & History Recording:**
    Base destruction, bankruptcy elimination, or 150-turn scoring calculation is checked. The turn frame is saved to match history.

