# Tournament Operations Guide - PROXY BOT WARS

This guide explains how fest coordinators and judges operate the tournament during an 8-hour competition.

---

## 1. Tournament Format

The recommended tournament structure for PROXY '26 is:
1. **Qualification / Seeding Round:**
   - Each registered bot plays 2 qualification matches against the official `baseline_bot.py` or randomly paired opponents.
   - Teams are ranked on the Leaderboard by Wins and Average 5-Category Competition Score.
2. **Top-8 Knockout Stage:**
   - Single-elimination bracket: Quarterfinals (4 matches) -> Semifinals (2 matches) -> Grand Finals (1 match).
   - In knockout stages, head-to-head match victory rules apply.

---

## 2. Running Matches via the Visualizer Dashboard

1. Start the server on the display projector machine:
   ```bash
   python server.py 8080
   ```
2. Open `http://localhost:8080` in full screen on the auditorium projector.
3. Click **"Tournament"** in the top navigation bar.
4. Register the participating teams and upload their submitted `.py` files.
5. Click **"Run Live Match"** to select competing bots, configure turns, and project the battle with full spectator visuals!

---

## 3. Running Matches via CLI for Fast Batch Processing

To run matches rapidly in the background:
```bash
python run_match.py --blue submissions/team_alpha.py --red submissions/team_beta.py --turns 150 --output-replay replays/match_alpha_beta.json
```
The result and final scores will be printed immediately to the terminal and saved to SQLite.

