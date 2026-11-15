# Developer & Contributor Guide - PROXY BOT WARS

This guide provides technical guidelines for CSE technical fest organizers, faculty coordinators, and student developers maintaining or extending PROXY BOT WARS.

---

## 1. Codebase Organization

The engine is built on object-oriented and modular functional programming paradigms:
- `game_engine/`: Independent core rules engine. Contains zero graphics or network dependencies.
- `bot_api/`: Input/output sanitization, schema definitions, and AST validation.
- `match_runner/`: Subprocess communication wrappers and replay JSON handling.
- `tournament/`: SQLite persistence, Swiss / knockout progression, and rankings.
- `visualizer/`: Pure HTML5/Canvas browser dashboard.
- `server.py`: Standard-library HTTP daemon providing static hosting and REST endpoints.

---

## 2. Adding a New Unit Type

To add a new unit type (e.g., `Medic` or `Sniper`):
1. Open `game_engine/config.py` and add the new unit configuration to `UNIT_SPECS`:
   ```python
   "sniper": {
       "hp": 50,
       "attack": 35,
       "speed": 1,
       "vision": 8,
       "attack_range": 4,
       "cost": 80,
       "description": "Long-range specialist."
   }
   ```
2. In `bot_api/schemas.py`, add the name to `LEGAL_UNIT_TYPES`.
3. In `visualizer/script.js`, add a visual icon representation in `drawUnit()` and the legend.
4. Add a unit test in `tests/test_engine.py`.

---

## 3. Modifying Official Scoring Weights

To customize competition scoring weights:
1. Open `game_engine/config.py`.
2. Adjust `SCORING_WEIGHTS`:
   ```python
   SCORING_WEIGHTS = {
       "combat": 0.30,
       "resource_territory": 0.20,
       "strategic": 0.20,
       "efficiency": 0.15,
       "adaptability": 0.15
   }
   ```
3. Ensure the sum equals `1.00`. The engine will normalize scores accordingly.

