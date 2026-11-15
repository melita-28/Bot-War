# PROXY '26 BOT WARS - Participant Starter Kit

Welcome to **BOT WARS**, the flagship autonomous programming competition organized by the Computer Science and Engineering Department for **PROXY '26**!

---

## 🚀 Quick Start in 3 Steps

### 1. Requirements
- Python 3.9+ (Python 3.10, 3.11, 3.12, 3.13 supported)
- Standard library only (no heavy third-party requirements)

Install test runner (optional):
```bash
pip install -r requirements.txt
```

### 2. Run Your First Battle
Run the starter bot against the baseline bot locally:
```bash
python local_simulator.py --blue starter_bot.py --red baseline_bot.py
```

You will see turn-by-turn combat progress and the final score breakdown!

### 3. Build Your Strategy
1. Open `starter_bot.py` in your favorite editor (e.g. VS Code).
2. Modify the `decide(self, obs: dict)` function.
3. Check `examples/` for aggressive (`rusher_bot.py`) and defensive (`turtle_bot.py`) strategy patterns.
4. Run matches against your modifications:
```bash
python local_simulator.py --blue starter_bot.py --red examples/rusher_bot.py
```

---

## 🎮 Game Rules Summary

- **Map:** 30 × 30 grid with symmetrical fair layout.
- **Teams:** BLUE starts in top-left, RED in bottom-right.
- **Victory:**
  1. Destroying enemy base HQ (500 HP) -> Immediate Victory!
  2. Eliminating enemy army and preventing unit training.
  3. Turn limit (150 turns) -> Highest official weighted score wins!
- **Fog of War:** You only receive data your units can see!

### Unit Baseline Stats

| Unit | HP | Attack | Speed | Vision | Range | Cost | Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Scout** | 40 | 5 | 4 | 10 | 1 | 30 | Exploration & Vision |
| **Soldier** | 100 | 20 | 2 | 5 | 2 | 50 | Tactical Combat |
| **Tank** | 250 | 40 | 1 | 4 | 3 | 100 | Heavy Frontline Combat |
| **Miner** | 60 | 0 | 2 | 5 | 0 | 40 | Resource Collection |
| **Engineer** | 70 | 5 | 2 | 6 | 1 | 60 | Construction & Repair |

---

## 🏆 Scoring Categories (Weights)

Matches reaching turn 150 are decided by:
- **Combat / Objective Performance:** 30%
- **Resource and Territory Control:** 20%
- **Strategic Decision-Making:** 20%
- **Efficiency / Computation Speed:** 15%
- **Adaptability / Reconnaissance:** 15%

---

## 📦 Submission

Submit your single `.py` bot file to the tournament organizers through the web dashboard or USB desk.
Before submitting, ensure your bot:
- Never exceeds 1.0 second per turn.
- Imports only standard permitted libraries.
- Returns valid JSON actions dictionary.

