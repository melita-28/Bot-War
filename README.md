# PROXY BOT WARS ⚔️
### Flagship Autonomous Programming Battle Platform | PROXY '26
**Organized by the Department of Computer Science & Engineering**

---

## 🌟 Overview

**PROXY BOT WARS** is a full-featured autonomous programming strategy battle platform inspired by the MIT Battlecode model.

Competing teams write Python 3 controllers (autonomous bots) that receive real-time, fog-of-war restricted tactical observations and return JSON action commands each turn. The central deterministic game engine simulates battles, handles movement, simultaneous combat, resource mining, engineering construction, automated defenses, territory control, tournament brackets, and live 2D canvas visualization.

---

## ⚡ Core Features

- **🎮 Symmetrical 30×30 Tactical Grid:** Balanced starting positions, procedural seed-based generation, obstacles, contested resource nodes, and neutral control zones.
- **🛡️ 5 Baseline Unit Types:** Scout, Soldier, Tank, Miner, and Engineer with exact official specifications.
- **👁️ Real Fog of War:** True visibility calculations; bots receive only information their units can observe.
- **⚡ Deterministic 10-Step Turn Engine:** Simultaneous damage resolution, rebound collisions, and reproducible match seeds.
- **⏱️ Resource & Economy Management:** Base passive income, active miner harvesting, engineer fortifications (barricades & turrets), and unit training.
- **📡 Strategic Constraints:** 100-byte inter-turn communication budget and 1.0s computation limits per turn.
- **📊 5-Category Competition Scoring:**
  - 30% Combat & Objective Performance
  - 20% Resource & Territory Control
  - 20% Strategic Decision-Making
  - 15% Efficiency & Computation Speed
  - 15% Adaptability & Reconnaissance
- **🖥️ Live 2D Spectator Visualizer:** Polished dark sci-fi dashboard, Canvas rendering, unit inspector, turn scrubber, speed controls (0.5x to 10x), and Fog-of-War modes.
- **📁 Full Replay System:** JSON match recording and instant turn-by-turn playback.
- **🏆 Tournament Management:** SQLite database, team registration, AST submission validation, and single-elimination bracket generator.
- **🤖 Starter Kit & Baseline Strategies:** Beginner starter bot, balanced baseline bot, aggressive rusher, and defensive turtle.

---

## 🚀 Quick Start Guide

### 1. Installation
Clone the repository and install test dependencies (Python standard library handles the rest):
```bash
pip install -r requirements.txt
```

### 2. Run a Match from Command Line
```bash
python run_match.py --blue bots/starter_bot.py --red bots/baseline_bot.py --turns 100
```

### 3. Launch the Visualizer & Arena Web Server
```bash
python server.py
```
Open **`http://localhost:8080`** in any web browser to view the live dashboard, watch replays, simulate new matches, or manage the tournament!

### 4. Run Automated Test Suite
```bash
python -m pytest tests/ -v
```

---

## 📂 Project Architecture

```
proxy-bot-wars/
├── run_match.py                # Root command-line match simulator
├── server.py                   # Visualizer web server & REST API
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
├── INSTALLATION.md             # Detailed installation guide
├── ARCHITECTURE.md             # Engine design & subsystem flow
│
├── game_engine/                # Core simulation logic
│   ├── config.py               # Official rules, baseline stats, scoring weights
│   ├── engine.py               # Deterministic 10-step turn coordinator
│   ├── game_state.py           # Match state representation & observation masking
│   ├── map.py                  # Symmetrical procedural map generator
│   ├── units.py                # Unit and Structure data classes
│   ├── movement.py             # Collision and boundary resolution
│   ├── combat.py               # Simultaneous attack and automated defenses
│   ├── resources.py            # Miner gathering and base unit training
│   ├── construction.py         # Engineer builds, repairs, and control zones
│   ├── visibility.py           # Fog-of-war Euclidean vision calculation
│   ├── communication.py        # 100-byte communication bus
│   ├── scoring.py              # 5-factor weighted scoring calculation
│   └── victory.py              # Base destruction and tie-break victory checks
│
├── bot_api/                    # Bot interface & safety validation
│   ├── api.py                  # BotController base class and runner harness
│   ├── schemas.py              # Formal action specifications
│   ├── validator.py            # Turn action parser and error containment
│   └── submission_validator.py # AST security scanner and dry-run validator
│
├── bots/                       # Example bot implementations
│   ├── starter_bot.py          # Beginner-friendly starter strategy
│   ├── baseline_bot.py         # Tactical baseline benchmark strategy
│   └── example_strategies/
│       ├── rusher_bot.py       # Aggressive frontline assault
│       └── turtle_bot.py       # Fortified engineer & turret defense
│
├── match_runner/               # Execution orchestration
│   ├── runner.py               # CLI battle executor
│   ├── executor.py             # Subprocess client with timeout isolation
│   └── replay.py               # Replay serialization and inspection
│
├── tournament/                 # Tournament system
│   ├── database.py             # SQLite persistence for teams & matches
│   ├── manager.py              # Tournament registration and bracket match coordinator
│   └── bracket.py              # Single-elimination bracket generator
│
├── visualizer/                 # HTML5/Canvas spectator dashboard
│   ├── index.html              # Strategic command center UI
│   ├── style.css               # Modern dark sci-fi styling
│   └── script.js               # Canvas renderer and playback controls
│
├── starter_kit/                # Standalone package for participants
│   ├── README.md               # Participant quickstart
│   ├── starter_bot.py          # Clean starter template
│   ├── baseline_bot.py         # Benchmark opponent
│   ├── local_simulator.py      # Local battle runner
│   ├── game_api.md             # API reference
│   └── game_rules.md           # Tournament rules
│
├── tests/                      # Automated test suite (25 tests)
└── documentation/              # Complete documentation guides
```

---

## 🏆 Scoring Formula

When a match reaches the 150-turn limit without base destruction, the winner is determined by the official weighted formula:

$$\text{Final Score} = 0.30 \times S_{\text{combat}} + 0.20 \times S_{\text{resource}} + 0.20 \times S_{\text{strategic}} + 0.15 \times S_{\text{efficiency}} + 0.15 \times S_{\text{adaptability}}$$

---

## 📜 Documentation Index

- [Installation Guide](INSTALLATION.md)
- [System Architecture](ARCHITECTURE.md)
- [Game Rules](documentation/GAME_RULES.md)
- [Bot API Specification](documentation/BOT_API.md)
- [Participant Guide](documentation/PARTICIPANT_GUIDE.md)
- [Developer Guide](documentation/DEVELOPER_GUIDE.md)
- [Tournament Organizer Guide](documentation/TOURNAMENT_GUIDE.md)
- [Security & Sandbox Model](documentation/SECURITY.md)
- [Testing & Quality Verification](documentation/TESTING.md)

