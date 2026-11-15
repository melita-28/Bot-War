"""
Lightweight Web Server and REST API for PROXY '26 BOT WARS Visualizer.
Zero external framework dependencies (uses standard library http.server).
"""
import http.server
import socketserver
import json
import os
import sys
import urllib.parse
from typing import Dict, Any

from match_runner.runner import run_match
from tournament.manager import TournamentManager

PORT = 8080
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VISUALIZER_DIR = os.path.join(BASE_DIR, "visualizer")
REPLAYS_DIR = os.path.join(BASE_DIR, "replays")
os.makedirs(REPLAYS_DIR, exist_ok=True)

tournament_manager = TournamentManager(os.path.join(BASE_DIR, "tournament.db"))

class BotWarsHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Static Visualizer routing
        if path == "/" or path == "/index.html":
            return self._serve_file(os.path.join(VISUALIZER_DIR, "index.html"), "text/html")
        elif path == "/style.css":
            return self._serve_file(os.path.join(VISUALIZER_DIR, "style.css"), "text/css")
        elif path == "/script.js":
            return self._serve_file(os.path.join(VISUALIZER_DIR, "script.js"), "application/javascript")
        elif path.startswith("/replays/"):
            filename = os.path.basename(path)
            file_path = os.path.join(REPLAYS_DIR, filename)
            return self._serve_file(file_path, "application/json")

        # REST API endpoints
        elif path == "/api/replays":
            return self._handle_get_replays()
        elif path.startswith("/api/replay/"):
            filename = os.path.basename(path)
            file_path = os.path.join(REPLAYS_DIR, filename)
            return self._serve_file(file_path, "application/json")
        elif path == "/api/tournament/leaderboard":
            lb = tournament_manager.get_leaderboard()
            return self._send_json(lb)
        elif path == "/api/tournament/bracket":
            bracket = tournament_manager.get_bracket()
            return self._send_json(bracket)
        elif path == "/api/tournament/teams":
            teams = tournament_manager.db.get_teams()
            return self._send_json(teams)

        # Fallback to visualizer dir
        candidate = os.path.join(VISUALIZER_DIR, path.lstrip("/"))
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return super().do_GET()

        self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        if path == "/api/run-match":
            blue_bot = body.get("blue", "bots/starter_bot.py")
            red_bot = body.get("red", "bots/baseline_bot.py")
            turns = int(body.get("turns", 150))
            seed = int(body.get("seed", 42))

            replay_filename = f"match_sim_{seed}_{turns}t.json"
            replay_path = os.path.join(REPLAYS_DIR, replay_filename)

            try:
                res = run_match(
                    blue_bot_path=blue_bot,
                    red_bot_path=red_bot,
                    max_turns=turns,
                    seed=seed,
                    output_replay=replay_path,
                    quiet=True
                )
                return self._send_json(res)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=500)

        elif path == "/api/tournament/teams":
            name = body.get("name")
            inst = body.get("institution", "")
            members = body.get("members", "")
            bot_path = body.get("bot_path", "")

            if not name:
                return self._send_json({"success": False, "error": "Team name is required"}, status=400)

            reg_res = tournament_manager.register_team(name=name, institution=inst, members=members, bot_path=bot_path)
            if reg_res.get("success") and bot_path and os.path.exists(bot_path):
                tournament_manager.submit_and_validate_bot(reg_res["team_id"], bot_path)

            return self._send_json(reg_res)

        elif path == "/api/tournament/run-match":
            blue_id = int(body.get("blue_team_id"))
            red_id = int(body.get("red_team_id"))
            round_name = body.get("round_name", "Knockout")
            seed = int(body.get("seed", 42))

            m_res = tournament_manager.execute_match(
                blue_team_id=blue_id,
                red_team_id=red_id,
                round_name=round_name,
                seed=seed
            )
            return self._send_json(m_res)

        self.send_error(404, "Endpoint Not Found")

    def _serve_file(self, file_path: str, content_type: str):
        if not os.path.exists(file_path):
            self.send_error(404, f"File Not Found: {os.path.basename(file_path)}")
            return
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")

    def _handle_get_replays(self):
        replays = []
        if os.path.exists(REPLAYS_DIR):
            for fname in os.listdir(REPLAYS_DIR):
                if fname.endswith(".json"):
                    fpath = os.path.join(REPLAYS_DIR, fname)
                    stat = os.stat(fpath)
                    import datetime
                    mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    replays.append({
                        "filename": fname,
                        "size": stat.st_size,
                        "modified": mod_time
                    })
        replays.sort(key=lambda x: x["modified"], reverse=True)
        return self._send_json(replays)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body_bytes = self.rfile.read(content_length)
            try:
                return json.loads(body_bytes.decode("utf-8"))
            except Exception:
                return {}
        return {}

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = PORT):
    handler = BotWarsHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"============================================================")
        print(f"  PROXY '26 BOT WARS Visualizer & Server Live")
        print(f"  URL: http://localhost:{port}")
        print(f"============================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)

