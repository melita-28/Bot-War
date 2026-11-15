"""
Command-line Match Runner and Simulator for PROXY BOT WARS.
Orchestrates autonomous bot matches, prints live summaries, and records replay data.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

from game_engine.engine import GameEngine
from game_engine.map import MapGenerator, GameMap
from match_runner.executor import BotProcessClient
from match_runner.replay import ReplayManager

def run_match(
    blue_bot_path: str,
    red_bot_path: str,
    map_path: Optional[str] = None,
    max_turns: int = 150,
    seed: int = 42,
    timeout: float = 1.0,
    output_replay: Optional[str] = None,
    quiet: bool = False
) -> Dict[str, Any]:
    """
    Executes a complete match between two bot programs.
    """
    if map_path and os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            game_map = GameMap.from_dict(json.load(f))
    else:
        game_map = MapGenerator.generate(seed=seed)

    engine = GameEngine(game_map=game_map, max_turns=max_turns)

    # Launch bot clients
    blue_client = BotProcessClient(blue_bot_path, team="blue", timeout_seconds=timeout)
    red_client = BotProcessClient(red_bot_path, team="red", timeout_seconds=timeout)

    blue_ok = blue_client.start()
    red_ok = red_client.start()

    if not blue_ok and not quiet:
        print(f"[ERROR] Failed to start Blue Bot: {blue_client.last_error_message}")
    if not red_ok and not quiet:
        print(f"[ERROR] Failed to start Red Bot: {red_client.last_error_message}")

    if not quiet:
        print(f"============================================================")
        print(f"  PROXY BOT WARS - MATCH COMMENCING")
        print(f"  BLUE: {os.path.basename(blue_bot_path)}  vs  RED: {os.path.basename(red_bot_path)}")
        print(f"  Map: {game_map.width}x{game_map.height} | Seed: {game_map.seed} | Max Turns: {max_turns}")
        print(f"============================================================")

    try:
        while engine.match_result is None and engine.state.current_turn < max_turns:
            current_turn = engine.state.current_turn + 1

            # 1. Fetch observations
            blue_obs = engine.get_observation("blue")
            red_obs = engine.get_observation("red")

            # 2. Query bots
            blue_out, blue_time, blue_err = blue_client.query(blue_obs)
            red_out, red_time, red_err = red_client.query(red_obs)

            # 3. Engine step
            step_res = engine.step(
                blue_output=blue_out,
                red_output=red_out,
                blue_time_ms=blue_time,
                red_time_ms=red_time
            )

            if not quiet and (current_turn % 10 == 0 or current_turn == 1 or step_res.get("game_over")):
                blue_res = engine.state.team_resources["blue"]
                red_res = engine.state.team_resources["red"]
                blue_units = len([u for u in engine.state.units.values() if u.alive and u.team == "blue"])
                red_units = len([u for u in engine.state.units.values() if u.alive and u.team == "red"])
                blue_base_hp = engine.state.structures["base_blue"].hp if "base_blue" in engine.state.structures else 0
                red_base_hp = engine.state.structures["base_red"].hp if "base_red" in engine.state.structures else 0

                print(f"[Turn {current_turn:3d}] "
                      f"BLUE (Units: {blue_units:2d}, Res: {blue_res:3d}, BaseHP: {blue_base_hp:3d}) | "
                      f"RED (Units: {red_units:2d}, Res: {red_res:3d}, BaseHP: {red_base_hp:3d})")

                if blue_err:
                    print(f"   [WARN Blue]: {blue_err}")
                if red_err:
                    print(f"   [WARN Red]: {red_err}")

    finally:
        blue_client.kill()
        red_client.kill()

    replay_data = engine.get_full_replay_data()

    if output_replay:
        saved_path = ReplayManager.save_replay(replay_data, output_replay)
        if not quiet:
            print(f"[REPLAY] Saved replay file to: {saved_path}")

    result = engine.match_result or {
        "is_game_over": True,
        "winner": "draw",
        "reason": "Turn limit reached",
        "final_turn": engine.state.current_turn,
        "scores": {}
    }

    if not quiet:
        print(f"============================================================")
        print(f"  MATCH CONCLUDED: Turn {result.get('final_turn', 0)}")
        print(f"  WINNER: {result.get('winner', 'None').upper()}")
        print(f"  Reason: {result.get('reason')}")
        scores = result.get("scores", {})
        if scores:
            b_sc = scores.get("blue", {}).get("final_score", 0)
            r_sc = scores.get("red", {}).get("final_score", 0)
            print(f"  Final Scores: BLUE: {b_sc:.2f} | RED: {r_sc:.2f}")
        print(f"============================================================")

    return {
        "result": result,
        "replay": replay_data
    }


def main():
    parser = argparse.ArgumentParser(description="PROXY BOT WARS - Local Simulator")
    parser.add_argument("--blue", required=True, help="Path to Blue bot Python script")
    parser.add_argument("--red", required=True, help="Path to Red bot Python script")
    parser.add_argument("--map", default=None, help="Path to map JSON file (optional)")
    parser.add_argument("--turns", type=int, default=150, help="Maximum turns (default: 150)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for map generator")
    parser.add_argument("--timeout", type=float, default=1.0, help="Per-turn bot timeout in seconds")
    parser.add_argument("--output-replay", default="replays/latest_match.json", help="Replay output JSON path")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (suppress verbose logs)")

    args = parser.parse_args()

    run_match(
        blue_bot_path=args.blue,
        red_bot_path=args.red,
        map_path=args.map,
        max_turns=args.turns,
        seed=args.seed,
        timeout=args.timeout,
        output_replay=args.output_replay,
        quiet=args.quiet
    )

if __name__ == "__main__":
    main()

