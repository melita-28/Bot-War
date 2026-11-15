# Participant Guide - PROXY BOT WARS

Welcome to **BOT WARS**, the autonomous programming challenge at **PROXY '26**!

As a participant, your goal is to design a Python strategy that controls your army across a 30×30 battlefield, out-maneuvering and out-thinking your opponent's bot.

---

## 1. Getting Started in 5 Minutes

1. Download or copy the `starter_kit/` folder.
2. Ensure you have Python 3.9+ installed.
3. Test the provided starter bot against the baseline bot:
   ```bash
   python local_simulator.py --blue starter_bot.py --red baseline_bot.py
   ```
4. Open `starter_bot.py` and inspect the `decide(self, obs: dict)` method.

---

## 2. Decision Logic Architecture

Your bot receives an `obs` dictionary containing everything your team can currently see.
You should divide your strategy into three core modules:

### Module A: Economy & Production
- Train Miners early so your income grows.
- Train Soldiers and Tanks for defense and offense.
```python
miner_count = sum(1 for u in units if u["type"] == "miner")
if miner_count < 2 and resources >= 40:
    actions.append({"action": "train", "unit_type": "miner"})
elif resources >= 50:
    actions.append({"action": "train", "unit_type": "soldier"})
```

### Module B: Information & Reconnaissance
- Scouts move at speed 4 and see up to 10 cells away!
- Use them to discover enemy bases, control zones, and resource deposits.

### Module C: Tactical Combat
- Soldiers have attack range 2 and damage 20.
- Tanks have attack range 3 and damage 40.
- Focus fire: if two of your soldiers attack the same enemy unit, they deal 40 damage in a single turn!

---

## 3. Important Tips for Success

- **Respect the 1.0s timeout:** Don't write $O(N^4)$ pathfinding algorithms. Chebyshev distance and direct gradient steps execute in sub-millisecond time.
- **Fog of War:** Enemies you cannot see will not be in `obs["visible_enemies"]`. Don't hardcode enemy positions.
- **Submissions:** Your bot must be a single standalone Python script without unauthorized third-party libraries.

