/**
 * PROXY '26 BOT WARS - High-Fidelity RTS Arena & Replay Visualizer
 * Inspired by tactical RTS battlefields (Tempest Rising style):
 * - Fortified military base enclosures with sandbag/concrete bunker perimeters & blast gates
 * - Contested crimson "Tempest" alien creep & glowing crystalline resource clusters
 * - Bespoke, high-detail vector models for all 5 unit classes:
 *     Tank (dual caterpillar treads, turret, main cannon)
 *     Scout (light tactical buggy, twin whip antennas, headlights)
 *     Soldier (armored combat marine, rifle, tactical visor)
 *     Miner (heavy industrial harvester with drill/claw & crystal hopper)
 *     Engineer (support fabrication rig with articulated welding crane)
 * - Dynamic combat effects: muzzle flashes, flamethrower bursts, plasma arcs, welding sparks
 */

class BotWarsVisualizer {
  constructor() {
    this.canvas = document.getElementById("battlefield-canvas");
    this.ctx = this.canvas.getContext("2d");

    // Upgrade resolution to 840x840 (28px per cell on 30x30)
    this.canvas.width = 840;
    this.canvas.height = 840;

    this.gridWidth = 30;
    this.gridHeight = 30;
    this.cellSize = this.canvas.width / this.gridWidth; // 28px

    // Playback state
    this.replayData = null;
    this.currentTurn = 0;
    this.isPlaying = false;
    this.playbackTimer = null;
    this.playbackSpeed = 250;
    this.visionMode = "spectator";

    this.selectedUnit = null;
    this.hoveredCell = null;
    this.animTime = 0;

    // Start ambient animation loop for radar sweeps, glowing coils, and idle effects
    this.startAmbientLoop();

    this.initEventListeners();
    this.loadInitialReplay();
    this.fetchReplayList();
  }

  startAmbientLoop() {
    const loop = () => {
      this.animTime += 0.05;
      if (!this.isPlaying) {
        // Redraw current frame so radar dishes, plasma coils, and beacons stay alive
        this.render();
      }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  initEventListeners() {
    document.getElementById("btn-play-pause").addEventListener("click", () => this.togglePlay());
    document.getElementById("btn-prev-turn").addEventListener("click", () => this.stepTurn(-1));
    document.getElementById("btn-next-turn").addEventListener("click", () => this.stepTurn(1));
    document.getElementById("btn-restart").addEventListener("click", () => this.seekTurn(0));

    const slider = document.getElementById("turn-slider");
    slider.addEventListener("input", (e) => this.seekTurn(parseInt(e.target.value, 10)));

    document.getElementById("speed-select").addEventListener("change", (e) => {
      this.playbackSpeed = parseInt(e.target.value, 10);
      if (this.isPlaying) {
        this.pause();
        this.play();
      }
    });

    document.getElementById("vision-mode-select").addEventListener("change", (e) => {
      this.visionMode = e.target.value;
      this.render();
    });

    window.addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT") return;
      if (e.code === "Space") {
        e.preventDefault();
        this.togglePlay();
      } else if (e.code === "ArrowLeft") {
        this.stepTurn(-1);
      } else if (e.code === "ArrowRight") {
        this.stepTurn(1);
      }
    });

    this.canvas.addEventListener("mousemove", (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const scaleX = this.canvas.width / rect.width;
      const scaleY = this.canvas.height / rect.height;
      const x = Math.floor(((e.clientX - rect.left) * scaleX) / this.cellSize);
      const y = Math.floor(((e.clientY - rect.top) * scaleY) / this.cellSize);
      this.hoveredCell = { x, y };
      this.checkCellHover(x, y);
    });

    this.canvas.addEventListener("click", () => {
      if (this.hoveredCell) {
        this.selectUnitAt(this.hoveredCell.x, this.hoveredCell.y);
      }
    });

    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(btn.dataset.tab).classList.add("active");
      });
    });

    document.getElementById("btn-clear-events").addEventListener("click", () => {
      document.getElementById("event-feed-list").innerHTML = "";
    });

    const fileInput = document.getElementById("replay-file-input");
    document.getElementById("btn-upload-replay").addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          try {
            const data = JSON.parse(ev.target.result);
            this.loadReplay(data);
          } catch (err) {
            alert("Failed to parse replay JSON: " + err.message);
          }
        };
        reader.readAsText(file);
      }
    });

    document.getElementById("btn-refresh-replays").addEventListener("click", () => this.fetchReplayList());

    const runModal = document.getElementById("modal-run-match");
    document.getElementById("btn-open-match-modal").addEventListener("click", () => runModal.classList.remove("hidden"));
    document.getElementById("modal-close-run").addEventListener("click", () => runModal.classList.add("hidden"));
    document.getElementById("btn-cancel-run").addEventListener("click", () => runModal.classList.add("hidden"));

    const tourneyModal = document.getElementById("modal-tournament");
    document.getElementById("btn-open-tournament").addEventListener("click", () => {
      tourneyModal.classList.remove("hidden");
      this.loadTournamentData();
    });
    document.getElementById("modal-close-tourney").addEventListener("click", () => tourneyModal.classList.add("hidden"));

    document.querySelectorAll(".tourney-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tourney-tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tourney-subcontent").forEach((c) => c.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(btn.dataset.subtab).classList.add("active");
      });
    });

    document.getElementById("btn-start-simulation").addEventListener("click", () => this.runSimulationFromModal());

    const regForm = document.getElementById("team-reg-form");
    if (regForm) {
      regForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.submitTeamRegistration();
      });
    }

    document.getElementById("btn-overlay-replay").addEventListener("click", () => {
      document.getElementById("canvas-overlay").classList.add("hidden");
      this.seekTurn(0);
      this.play();
    });
  }

  async loadInitialReplay() {
    try {
      const res = await fetch("/replays/test_match.json");
      if (res.ok) {
        const data = await res.json();
        this.loadReplay(data);
      }
    } catch (e) {
      console.log("No default replay loaded");
    }
  }

  async fetchReplayList() {
    try {
      const res = await fetch("/api/replays");
      if (res.ok) {
        const list = await res.json();
        const container = document.getElementById("server-replay-list");
        container.innerHTML = "";
        list.forEach((r) => {
          const card = document.createElement("div");
          card.className = "replay-card";
          card.innerHTML = `
            <div class="title">🎮 ${r.filename}</div>
            <div class="meta">Size: ${(r.size / 1024).toFixed(1)} KB | Modified: ${r.modified}</div>
          `;
          card.addEventListener("click", async () => {
            const repRes = await fetch("/api/replay/" + encodeURIComponent(r.filename));
            if (repRes.ok) {
              const repData = await repRes.json();
              this.loadReplay(repData);
            }
          });
          container.appendChild(card);
        });
      }
    } catch (e) {
      console.log("Replay API list unavailable");
    }
  }

  loadReplay(replayData) {
    this.replayData = replayData;
    this.pause();

    const history = replayData.history || [];
    const slider = document.getElementById("turn-slider");
    slider.max = Math.max(0, history.length - 1);
    slider.value = 0;

    document.getElementById("max-turns").textContent = replayData.metadata?.total_turns || history.length - 1;
    document.getElementById("canvas-overlay").classList.add("hidden");

    this.seekTurn(0);
  }

  seekTurn(turn) {
    if (!this.replayData || !this.replayData.history) return;
    this.currentTurn = Math.max(0, Math.min(turn, this.replayData.history.length - 1));
    document.getElementById("turn-slider").value = this.currentTurn;
    document.getElementById("current-turn").textContent = this.currentTurn;

    this.updateHUD();
    this.render();
  }

  stepTurn(delta) {
    if (!this.replayData) return;
    const next = this.currentTurn + delta;
    if (next >= 0 && next < this.replayData.history.length) {
      this.seekTurn(next);
    } else if (next >= this.replayData.history.length) {
      this.pause();
      this.showGameOverOverlay();
    }
  }

  togglePlay() {
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }
  }

  play() {
    if (!this.replayData) return;
    this.isPlaying = true;
    document.getElementById("btn-play-pause").textContent = "⏸";
    document.getElementById("match-status-badge").textContent = "SIMULATING";
    document.getElementById("match-status-badge").style.color = "var(--color-blue)";

    if (this.currentTurn >= this.replayData.history.length - 1) {
      this.currentTurn = 0;
    }

    this.playbackTimer = setInterval(() => {
      if (this.currentTurn < this.replayData.history.length - 1) {
        this.stepTurn(1);
      } else {
        this.pause();
        this.showGameOverOverlay();
      }
    }, this.playbackSpeed);
  }

  pause() {
    this.isPlaying = false;
    clearInterval(this.playbackTimer);
    document.getElementById("btn-play-pause").textContent = "▶";
    document.getElementById("match-status-badge").textContent = "PAUSED";
    document.getElementById("match-status-badge").style.color = "var(--text-muted)";
  }

  showGameOverOverlay() {
    const meta = this.replayData?.metadata || {};
    const overlay = document.getElementById("canvas-overlay");
    const title = document.getElementById("victory-title");
    const reason = document.getElementById("victory-reason");

    title.textContent = (meta.winner ? meta.winner.toUpperCase() : "MATCH") + " VICTORY";
    title.style.color = meta.winner === "blue" ? "var(--color-blue)" : (meta.winner === "red" ? "var(--color-red)" : "var(--color-gold)");
    reason.textContent = meta.reason || "Turn limit concluded";
    overlay.classList.remove("hidden");
  }

  updateHUD() {
    if (!this.replayData) return;
    const frame = this.replayData.history[this.currentTurn];
    if (!frame) return;

    const snap = frame.snapshot;
    const res = snap.team_resources || {};

    document.getElementById("blue-res").textContent = res.blue ?? 0;
    document.getElementById("red-res").textContent = res.red ?? 0;

    const blueUnits = (snap.units || []).filter((u) => u.team === "blue").length;
    const redUnits = (snap.units || []).filter((u) => u.team === "red").length;
    document.getElementById("blue-units").textContent = blueUnits;
    document.getElementById("red-units").textContent = redUnits;

    const blueBase = (snap.structures || []).find((s) => s.id === "base_blue");
    const redBase = (snap.structures || []).find((s) => s.id === "base_red");
    document.getElementById("blue-base-hp").textContent = blueBase ? blueBase.hp : 0;
    document.getElementById("red-base-hp").textContent = redBase ? redBase.hp : 0;

    // Events
    if (frame.events && frame.events.length > 0) {
      const feed = document.getElementById("event-feed-list");
      frame.events.forEach((ev) => {
        const item = document.createElement("div");
        item.className = "event-item " + (ev.team || "");
        if (ev.type === "unit_destroyed") {
          item.classList.add("kill");
          item.textContent = `💀 [Turn ${frame.turn}] ${ev.team.toUpperCase()} Unit #${ev.unit_id} eliminated!`;
        } else if (ev.type === "unit_damaged") {
          item.textContent = `⚔️ [Turn ${frame.turn}] Unit #${ev.unit_id} took ${ev.damage} dmg (HP: ${ev.hp_remaining})`;
        } else if (ev.type === "resource_gathered") {
          item.textContent = `⛏️ [Turn ${frame.turn}] Miner #${ev.unit_id} gathered +${ev.amount} res`;
        } else if (ev.type === "unit_trained") {
          item.textContent = `⭐ [Turn ${frame.turn}] ${ev.team.toUpperCase()} deployed ${ev.unit_type.toUpperCase()} #${ev.unit_id}`;
        } else if (ev.type === "zone_captured") {
          item.textContent = `🚩 [Turn ${frame.turn}] ${ev.team.toUpperCase()} captured Control Zone #${ev.zone_id}!`;
        } else if (ev.type === "structure_built") {
          item.textContent = `🔨 [Turn ${frame.turn}] ${ev.team.toUpperCase()} constructed ${ev.structure_type.toUpperCase()}`;
        }
        if (item.textContent) {
          feed.insertBefore(item, feed.firstChild);
        }
      });
    }

    const meta = this.replayData.metadata;
    if (meta && meta.final_scores) {
      const bSc = meta.final_scores.blue;
      const rSc = meta.final_scores.red;
      document.getElementById("blue-score").textContent = bSc?.final_score?.toFixed(1) || "0.0";
      document.getElementById("red-score").textContent = rSc?.final_score?.toFixed(1) || "0.0";

      if (bSc && bSc.breakdown) {
        document.getElementById("score-val-combat").textContent = bSc.breakdown.combat;
        document.getElementById("fill-combat").style.width = Math.min(100, bSc.breakdown.combat) + "%";

        document.getElementById("score-val-resource").textContent = bSc.breakdown.resource_territory;
        document.getElementById("fill-resource").style.width = Math.min(100, bSc.breakdown.resource_territory) + "%";

        document.getElementById("score-val-strategic").textContent = bSc.breakdown.strategic;
        document.getElementById("fill-strategic").style.width = Math.min(100, bSc.breakdown.strategic) + "%";

        document.getElementById("score-val-efficiency").textContent = bSc.breakdown.efficiency;
        document.getElementById("fill-efficiency").style.width = Math.min(100, bSc.breakdown.efficiency) + "%";

        document.getElementById("score-val-adaptability").textContent = bSc.breakdown.adaptability;
        document.getElementById("fill-adaptability").style.width = Math.min(100, bSc.breakdown.adaptability) + "%";
      }
    }
  }

  checkCellHover(gx, gy) {
    if (!this.replayData) return;
    const snap = this.replayData.history[this.currentTurn]?.snapshot;
    if (!snap) return;

    const unit = (snap.units || []).find((u) => u.x === gx && u.y === gy && u.alive);
    if (unit) {
      this.displayInspector(unit, "unit");
    }
  }

  selectUnitAt(gx, gy) {
    if (!this.replayData) return;
    const snap = this.replayData.history[this.currentTurn]?.snapshot;
    if (!snap) return;

    const unit = (snap.units || []).find((u) => u.x === gx && u.y === gy && u.alive);
    if (unit) {
      this.selectedUnit = unit;
      this.displayInspector(unit, "unit");
      this.render();
      return;
    }

    const struct = (snap.structures || []).find((s) => s.x === gx && s.y === gy && s.alive);
    if (struct) {
      this.displayInspector(struct, "structure");
      this.render();
    }
  }

  displayInspector(entity, kind) {
    document.getElementById("inspector-placeholder").classList.add("hidden");
    const body = document.getElementById("inspector-body");
    body.classList.remove("hidden");

    const avatarMap = {
      scout: "🏎️", soldier: "⚔️", tank: "🛡️", miner: "⛏️", engineer: "🔧",
      base: "🏛️", turret: "🗼", barricade: "🚧"
    };

    const type = entity.type || entity.structure_type;
    document.getElementById("insp-avatar").textContent = avatarMap[type] || "🔹";
    document.getElementById("insp-name").textContent = `${type.toUpperCase()} #${entity.id}`;

    const badge = document.getElementById("insp-team-badge");
    badge.textContent = entity.team.toUpperCase();
    badge.style.background = entity.team === "blue" ? "var(--color-blue)" : "var(--color-red)";
    badge.style.color = entity.team === "blue" ? "#000" : "#fff";

    document.getElementById("insp-hp-text").textContent = `${entity.hp} / ${entity.max_hp}`;
    const hpPct = Math.max(0, Math.min(100, (entity.hp / entity.max_hp) * 100));
    document.getElementById("insp-hp-fill").style.width = hpPct + "%";

    document.getElementById("insp-attack").textContent = entity.attack ?? 0;
    document.getElementById("insp-range").textContent = entity.attack_range ?? 0;
    document.getElementById("insp-speed").textContent = entity.speed ?? 0;
    document.getElementById("insp-vision").textContent = entity.vision ?? 0;
    document.getElementById("insp-pos").textContent = `${entity.x}, ${entity.y}`;
    document.getElementById("insp-carry").textContent = entity.carried_resources ?? 0;

    let actDesc = "Holding position";
    if (entity.last_action) {
      actDesc = JSON.stringify(entity.last_action);
    }
    document.getElementById("insp-action").textContent = actDesc;
  }

  // =========================================================================
  // HIGH-FIDELITY BATTLEFIELD CANVAS RENDERING (Tempest Rising Style)
  // =========================================================================
  render() {
    if (!this.replayData) return;
    const snap = this.replayData.history[this.currentTurn]?.snapshot;
    const mapData = this.replayData.initial_map;
    if (!snap || !mapData) return;

    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const cs = this.cellSize;

    // 1. Gritty Rocky Terrain Background with Atmospheric Vignette
    ctx.fillStyle = "#0c101a";
    ctx.fillRect(0, 0, w, h);

    // Subtle tactical asphalt/dirt texture
    ctx.fillStyle = "#111724";
    for (let gx = 0; gx < this.gridWidth; gx += 2) {
      for (let gy = 0; gy < this.gridHeight; gy += 2) {
        if ((gx + gy) % 4 === 0) {
          ctx.fillRect(gx * cs, gy * cs, cs * 2, cs * 2);
        }
      }
    }

    // 2. Infested Crimson "Tempest" Creep Zones (from user reference image)
    this.renderInfestedCreepZones(ctx, cs);

    // 3. Subtle Tactical Grid Lines
    ctx.strokeStyle = "rgba(42, 60, 95, 0.25)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= this.gridWidth; x++) {
      ctx.beginPath();
      ctx.moveTo(x * cs, 0);
      ctx.lineTo(x * cs, h);
      ctx.stroke();
    }
    for (let y = 0; y <= this.gridHeight; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * cs);
      ctx.lineTo(w, y * cs);
      ctx.stroke();
    }

    // 4. Fortified Military Base Outpost Foundations (Tarmac & Hazard Lines)
    this.renderBaseOutpostGround(ctx, mapData, cs);

    // 5. Obstacles & Sandbag Perimeter Bunkers (as in reference image)
    this.renderObstaclesAndPerimeters(ctx, mapData.obstacles || [], cs);

    // 6. Neutral Control Zones / Energy Pylon Relays
    this.renderControlZones(ctx, snap.control_zones || mapData.control_zones || [], cs);

    // 7. Resource Crystals (Crimson Tempest nodes & Golden Ore)
    this.renderResourceDeposits(ctx, snap.resource_deposits || mapData.resource_deposits || [], cs);

    // 8. Structures (Command HQ, Automated Turrets, Barricades)
    this.renderStructures(ctx, snap.structures || [], cs);

    // 9. Autonomous Bots (Units with distinct vector structures)
    this.renderUnits(ctx, snap.units || [], cs);

    // 10. Turn Combat Animation Effects (Muzzle flashes, flame bursts, laser arcs)
    this.renderCombatEvents(ctx, snap, cs);

    // 11. Fog of War Mask
    if (this.visionMode !== "spectator") {
      this.renderFogOfWar(ctx, snap, this.visionMode);
    }
  }

  renderInfestedCreepZones(ctx, cs) {
    // Red glowing alien organic creep on left flank and midfield (Tempest Rising theme)
    const zones = [
      { cx: 7, cy: 15, r: 6 },
      { cx: 22, cy: 14, r: 6 }
    ];

    zones.forEach((z) => {
      const px = z.cx * cs;
      const py = z.cy * cs;
      const rad = z.r * cs;

      const grad = ctx.createRadialGradient(px, py, rad * 0.1, px, py, rad);
      grad.addColorStop(0, "rgba(180, 20, 40, 0.25)");
      grad.addColorStop(0.6, "rgba(120, 10, 30, 0.12)");
      grad.addColorStop(1, "rgba(12, 16, 26, 0)");

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(px, py, rad, 0, Math.PI * 2);
      ctx.fill();

      // Draw bioluminescent organic tendrils crawling across ground
      ctx.save();
      ctx.strokeStyle = "rgba(255, 40, 70, 0.35)";
      ctx.lineWidth = 1.5;
      for (let i = 0; i < 6; i++) {
        const ang = (i / 6) * Math.PI * 2 + this.animTime * 0.05;
        ctx.beginPath();
        ctx.moveTo(px, py);
        const cpX = px + Math.cos(ang + 0.3) * (rad * 0.5);
        const cpY = py + Math.sin(ang + 0.3) * (rad * 0.5);
        const epX = px + Math.cos(ang) * (rad * 0.85);
        const epY = py + Math.sin(ang) * (rad * 0.85);
        ctx.quadraticCurveTo(cpX, cpY, epX, epY);
        ctx.stroke();
      }
      ctx.restore();
    });
  }

  renderBaseOutpostGround(ctx, mapData, cs) {
    const bases = mapData.base_positions || { blue: [3, 3], red: [26, 26] };
    [
      { pos: bases.blue, color: "rgba(0, 180, 255, 0.06)", border: "rgba(0, 180, 255, 0.3)" },
      { pos: bases.red, color: "rgba(255, 40, 80, 0.06)", border: "rgba(255, 40, 80, 0.3)" }
    ].forEach(({ pos, color, border }) => {
      if (!pos) return;
      const [bx, by] = pos;
      const pad = 2;
      const ox = (bx - pad) * cs;
      const oy = (by - pad) * cs;
      const w = (pad * 2 + 1) * cs;

      // Dark reinforced tarmac slab
      ctx.fillStyle = "#151b29";
      ctx.fillRect(ox, oy, w, w);
      ctx.fillStyle = color;
      ctx.fillRect(ox, oy, w, w);

      ctx.strokeStyle = border;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(ox, oy, w, w);

      // Yellow/Black hazard caution markers on perimeter
      ctx.fillStyle = "rgba(255, 184, 0, 0.4)";
      ctx.fillRect(ox, oy, 8, 8);
      ctx.fillRect(ox + w - 8, oy, 8, 8);
      ctx.fillRect(ox, oy + w - 8, 8, 8);
      ctx.fillRect(ox + w - 8, oy + w - 8, 8, 8);
    });
  }

  renderObstaclesAndPerimeters(ctx, obstacles, cs) {
    obstacles.forEach(([ox, oy]) => {
      const px = ox * cs;
      const py = oy * cs;

      // Reinforced military bunker wall with sandbag texturing
      ctx.save();
      // Concrete base
      ctx.fillStyle = "#202838";
      ctx.fillRect(px + 2, py + 2, cs - 4, cs - 4);

      // Sandbag row highlights
      ctx.fillStyle = "#4a5a78";
      ctx.fillRect(px + 4, py + 4, cs - 8, 5);
      ctx.fillRect(px + 4, py + cs - 9, cs - 8, 5);

      // Metal reinforced cap
      ctx.strokeStyle = "#6b80a6";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(px + 2, py + 2, cs - 4, cs - 4);

      // Corner rivets
      ctx.fillStyle = "#8ba0c6";
      ctx.fillRect(px + 3, py + 3, 2, 2);
      ctx.fillRect(px + cs - 5, py + 3, 2, 2);
      ctx.fillRect(px + 3, py + cs - 5, 2, 2);
      ctx.fillRect(px + cs - 5, py + cs - 5, 2, 2);
      ctx.restore();
    });
  }

  renderControlZones(ctx, zones, cs) {
    zones.forEach((zone) => {
      const zx = zone.x * cs + cs / 2;
      const zy = zone.y * cs + cs / 2;
      const radius = (zone.radius + 0.5) * cs;

      ctx.save();
      // Outer capture circle with rotating radar tick marks
      ctx.beginPath();
      ctx.arc(zx, zy, radius, 0, Math.PI * 2);

      let teamColor = "rgba(255, 184, 0, 0.8)";
      let fillCol = "rgba(255, 184, 0, 0.08)";
      if (zone.owner === "blue") {
        teamColor = "rgba(0, 229, 255, 0.9)";
        fillCol = "rgba(0, 229, 255, 0.15)";
      } else if (zone.owner === "red") {
        teamColor = "rgba(255, 42, 95, 0.9)";
        fillCol = "rgba(255, 42, 95, 0.15)";
      }

      ctx.fillStyle = fillCol;
      ctx.fill();
      ctx.strokeStyle = teamColor;
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.stroke();

      // Rotating radar beam
      const radarAngle = this.animTime * 1.5;
      ctx.beginPath();
      ctx.moveTo(zx, zy);
      ctx.arc(zx, zy, radius, radarAngle, radarAngle + 0.4);
      ctx.closePath();
      ctx.fillStyle = zone.owner === "blue" ? "rgba(0, 229, 255, 0.2)" : (zone.owner === "red" ? "rgba(255, 42, 95, 0.2)" : "rgba(255, 184, 0, 0.15)");
      ctx.fill();

      // Central Radar Relay Dish
      ctx.setLineDash([]);
      ctx.fillStyle = "#1e2638";
      ctx.beginPath();
      ctx.arc(zx, zy, cs * 0.35, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = teamColor;
      ctx.stroke();

      ctx.fillStyle = "#fff";
      ctx.font = "bold 9px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("📡", zx, zy);
      ctx.restore();
    });
  }

  renderResourceDeposits(ctx, deposits, cs) {
    deposits.forEach((dep) => {
      if (dep.amount <= 0) return;
      const rx = dep.x * cs + cs / 2;
      const ry = dep.y * cs + cs / 2;
      const isTempest = dep.deposit_type === "tempest_crystal" || dep.max_amount > 500;

      ctx.save();
      if (isTempest) {
        // High-energy Crimson Tempest Crystal cluster (as seen in Tempest Rising image)
        const pulse = 1 + Math.sin(this.animTime * 3 + dep.id) * 0.12;
        ctx.shadowColor = "rgba(255, 30, 70, 0.85)";
        ctx.shadowBlur = 12 * pulse;

        // Draw faceted red crystals
        ctx.fillStyle = "#ff1e4b";
        ctx.beginPath();
        ctx.moveTo(rx, ry - cs * 0.45 * pulse);
        ctx.lineTo(rx + cs * 0.35 * pulse, ry);
        ctx.lineTo(rx, ry + cs * 0.4 * pulse);
        ctx.lineTo(rx - cs * 0.35 * pulse, ry);
        ctx.closePath();
        ctx.fill();

        // Crystal facet highlights
        ctx.fillStyle = "#ffa3b5";
        ctx.beginPath();
        ctx.moveTo(rx, ry - cs * 0.45 * pulse);
        ctx.lineTo(rx + cs * 0.15, ry - cs * 0.1);
        ctx.lineTo(rx, ry + cs * 0.2);
        ctx.closePath();
        ctx.fill();
      } else {
        // Golden Ore Node
        ctx.shadowColor = "rgba(255, 184, 0, 0.75)";
        ctx.shadowBlur = 8;
        ctx.fillStyle = "#ffb800";
        ctx.beginPath();
        ctx.arc(rx, ry, cs * 0.32, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.shadowBlur = 0;
      ctx.fillStyle = "#fff";
      ctx.font = "bold 9px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(dep.amount > 999 ? "1k" : dep.amount, rx, ry);
      ctx.restore();
    });
  }

  renderStructures(ctx, structures, cs) {
    structures.forEach((st) => {
      if (!st.alive) return;
      const sx = st.x * cs;
      const sy = st.y * cs;
      const isBlue = st.team === "blue";
      const teamColor = isBlue ? "#00e5ff" : "#ff2a5f";

      ctx.save();
      if (st.type === "base") {
        // Multi-level Military Command Center with twin Plasma Power Coils
        ctx.fillStyle = "#151e2e";
        ctx.fillRect(sx + 1, sy + 1, cs - 2, cs - 2);

        // Armored Roof Slab
        ctx.fillStyle = isBlue ? "#004766" : "#660f24";
        ctx.fillRect(sx + 3, sy + 3, cs - 6, cs - 6);
        ctx.strokeStyle = teamColor;
        ctx.lineWidth = 2;
        ctx.strokeRect(sx + 1, sy + 1, cs - 2, cs - 2);

        // Animated Rotating Radar Dish in center
        const radarAngle = this.animTime * 2;
        ctx.fillStyle = "#d0e4ff";
        ctx.beginPath();
        ctx.arc(sx + cs / 2, sy + cs / 2, cs * 0.22, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#111";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(sx + cs / 2, sy + cs / 2);
        ctx.lineTo(sx + cs / 2 + Math.cos(radarAngle) * cs * 0.3, sy + cs / 2 + Math.sin(radarAngle) * cs * 0.3);
        ctx.stroke();

        // Twin Tesla Power Coils with Electric Arcs (matching reference photo!)
        const coilY = sy + cs / 2;
        [-cs * 0.35, cs * 0.35].forEach((offset) => {
          ctx.fillStyle = teamColor;
          ctx.beginPath();
          ctx.arc(sx + cs / 2 + offset, coilY, 3, 0, Math.PI * 2);
          ctx.fill();
        });

        // Plasma spark arc between coils
        if (Math.sin(this.animTime * 8) > 0.3) {
          ctx.strokeStyle = isBlue ? "rgba(100, 230, 255, 0.9)" : "rgba(255, 120, 150, 0.9)";
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(sx + cs * 0.15, coilY);
          ctx.lineTo(sx + cs * 0.5, coilY + (Math.random() - 0.5) * 6);
          ctx.lineTo(sx + cs * 0.85, coilY);
          ctx.stroke();
        }

      } else if (st.type === "turret") {
        // Rotary Automated Autocannon Turret
        ctx.fillStyle = "#1e2638";
        ctx.beginPath();
        ctx.arc(sx + cs / 2, sy + cs / 2, cs * 0.42, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = isBlue ? "#0099cc" : "#cc1144";
        ctx.beginPath();
        ctx.arc(sx + cs / 2, sy + cs / 2, cs * 0.3, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = teamColor;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Dual heavy gun barrels pointing forward
        ctx.fillStyle = "#0a0d14";
        ctx.fillRect(sx + cs / 2 - 4, sy + 2, 3, cs * 0.4);
        ctx.fillRect(sx + cs / 2 + 1, sy + 2, 3, cs * 0.4);

      } else if (st.type === "barricade") {
        // Reinforced concrete dragon's teeth
        ctx.fillStyle = "#48566b";
        ctx.fillRect(sx + 3, sy + 3, cs - 6, cs - 6);
        ctx.strokeStyle = "#8092ab";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(sx + 3, sy + 3, cs - 6, cs - 6);
      }

      this.drawHealthBar(ctx, sx, sy - 5, cs, st.hp, st.max_hp);
      ctx.restore();
    });
  }

  // =========================================================================
  // BESPOKE BOT STRUCTURES (DISTINCT VECTOR SPRITES)
  // =========================================================================
  renderUnits(ctx, units, cs) {
    units.forEach((u) => {
      if (!u.alive) return;
      const cx = u.x * cs + cs / 2;
      const cy = u.y * cs + cs / 2;
      const isBlue = u.team === "blue";

      ctx.save();
      // Selection highlight ring
      if (this.selectedUnit && this.selectedUnit.id === u.id) {
        ctx.strokeStyle = "var(--color-gold)";
        ctx.lineWidth = 2.5;
        ctx.setLineDash([4, 2]);
        ctx.beginPath();
        ctx.arc(cx, cy, cs * 0.52, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Determine facing direction from last action
      let angle = isBlue ? Math.PI / 4 : (5 * Math.PI) / 4; // default facing towards opposite quadrant
      if (u.last_action && u.last_action.to && u.last_action.from) {
        const dx = u.last_action.to[0] - u.last_action.from[0];
        const dy = u.last_action.to[1] - u.last_action.from[1];
        if (dx !== 0 || dy !== 0) {
          angle = Math.atan2(dy, dx);
        }
      }

      // Render bespoke unit structure based on class
      ctx.translate(cx, cy);
      ctx.rotate(angle);

      if (u.type === "tank") {
        this.drawTank(ctx, cs, isBlue);
      } else if (u.type === "scout") {
        this.drawScout(ctx, cs, isBlue);
      } else if (u.type === "soldier") {
        this.drawSoldier(ctx, cs, isBlue);
      } else if (u.type === "miner") {
        this.drawMiner(ctx, cs, isBlue, u.carried_resources);
      } else if (u.type === "engineer") {
        this.drawEngineer(ctx, cs, isBlue);
      }

      ctx.restore();

      // Health bar above unit (unrotated in world space)
      this.drawHealthBar(ctx, u.x * cs, u.y * cs - 5, cs, u.hp, u.max_hp);
    });
  }

  /**
   * TANK: Dual Caterpillar Treads + Heavy Armor Chassis + Long Main Battle Cannon
   */
  drawTank(ctx, cs, isBlue) {
    const primary = isBlue ? "#00e5ff" : "#ff2a5f";
    const darkPrimary = isBlue ? "#007799" : "#991133";
    const treadColor = "#1a2130";

    // 1. Dual Caterpillar Treads on left and right sides
    ctx.fillStyle = treadColor;
    ctx.fillRect(-cs * 0.42, -cs * 0.38, cs * 0.84, cs * 0.18); // Left tread
    ctx.fillRect(-cs * 0.42, cs * 0.20, cs * 0.84, cs * 0.18);  // Right tread

    // Tread segment links
    ctx.strokeStyle = "#384761";
    ctx.lineWidth = 1;
    for (let tx = -cs * 0.4; tx <= cs * 0.4; tx += cs * 0.15) {
      ctx.beginPath();
      ctx.moveTo(tx, -cs * 0.38); ctx.lineTo(tx, -cs * 0.20);
      ctx.moveTo(tx, cs * 0.20); ctx.lineTo(tx, cs * 0.38);
      ctx.stroke();
    }

    // 2. Heavy Armored Hull Chassis
    ctx.fillStyle = darkPrimary;
    ctx.beginPath();
    ctx.moveTo(-cs * 0.32, -cs * 0.22);
    ctx.lineTo(cs * 0.34, -cs * 0.22);
    ctx.lineTo(cs * 0.38, 0);
    ctx.lineTo(cs * 0.34, cs * 0.22);
    ctx.lineTo(-cs * 0.32, cs * 0.22);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = primary;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 3. Rotating Turret with Hatch
    ctx.fillStyle = primary;
    ctx.beginPath();
    ctx.arc(-cs * 0.05, 0, cs * 0.22, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#0c121c";
    ctx.beginPath();
    ctx.arc(-cs * 0.08, 0, cs * 0.12, 0, Math.PI * 2);
    ctx.fill();

    // 4. Heavy Main Battle Cannon Barrel with Muzzle Brake
    ctx.fillStyle = "#222a38";
    ctx.fillRect(-cs * 0.05, -cs * 0.06, cs * 0.48, cs * 0.12);
    // Muzzle brake
    ctx.fillStyle = primary;
    ctx.fillRect(cs * 0.38, -cs * 0.08, cs * 0.08, cs * 0.16);
  }

  /**
   * SCOUT: Light Tactical Reconnaissance Buggy with Twin Whip Antennas & Headlights
   */
  drawScout(ctx, cs, isBlue) {
    const primary = isBlue ? "#00e5ff" : "#ff2a5f";

    // 1. Aerodynamic Wedge Hull
    ctx.fillStyle = isBlue ? "#006b8f" : "#8f112e";
    ctx.beginPath();
    ctx.moveTo(cs * 0.42, 0);                   // Nose tip
    ctx.lineTo(-cs * 0.35, -cs * 0.3);          // Rear left
    ctx.lineTo(-cs * 0.22, 0);                  // Engine notch
    ctx.lineTo(-cs * 0.35, cs * 0.3);           // Rear right
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = primary;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 2. Cockpit Windshield (Tinted glass)
    ctx.fillStyle = "#112233";
    ctx.beginPath();
    ctx.moveTo(cs * 0.15, 0);
    ctx.lineTo(-cs * 0.08, -cs * 0.14);
    ctx.lineTo(-cs * 0.08, cs * 0.14);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = "#80d4ff";
    ctx.lineWidth = 1;
    ctx.stroke();

    // 3. Twin Forward Headlights (Casting bright tactical light beams)
    ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
    ctx.beginPath();
    ctx.arc(cs * 0.28, -cs * 0.12, 2, 0, Math.PI * 2);
    ctx.arc(cs * 0.28, cs * 0.12, 2, 0, Math.PI * 2);
    ctx.fill();

    // 4. Twin Rear Whip Antennas with blinking sensor light
    ctx.strokeStyle = "#a0b4cc";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-cs * 0.28, -cs * 0.2); ctx.lineTo(-cs * 0.44, -cs * 0.28);
    ctx.moveTo(-cs * 0.28, cs * 0.2);  ctx.lineTo(-cs * 0.44, cs * 0.28);
    ctx.stroke();

    // Blinking antenna beacon
    ctx.fillStyle = Math.sin(this.animTime * 8) > 0 ? primary : "#fff";
    ctx.beginPath();
    ctx.arc(-cs * 0.44, -cs * 0.28, 2, 0, Math.PI * 2);
    ctx.arc(-cs * 0.44, cs * 0.28, 2, 0, Math.PI * 2);
    ctx.fill();
  }

  /**
   * SOLDIER: Mechanized Combat Marine with Armor Pauldrons and Assault Rifle
   */
  drawSoldier(ctx, cs, isBlue) {
    const primary = isBlue ? "#00e5ff" : "#ff2a5f";

    // 1. Armored Torso / Exoskeleton
    ctx.fillStyle = isBlue ? "#005577" : "#771126";
    ctx.beginPath();
    ctx.arc(0, 0, cs * 0.24, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = primary;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 2. Shoulder Pauldrons
    ctx.fillStyle = primary;
    ctx.fillRect(-cs * 0.1, -cs * 0.32, cs * 0.2, cs * 0.12);
    ctx.fillRect(-cs * 0.1, cs * 0.20, cs * 0.2, cs * 0.12);

    // 3. Combat Helmet & Glowing Visor
    ctx.fillStyle = "#151e29";
    ctx.beginPath();
    ctx.arc(0, 0, cs * 0.14, 0, Math.PI * 2);
    ctx.fill();

    // Visor HUD line
    ctx.strokeStyle = primary;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, cs * 0.12, -Math.PI / 4, Math.PI / 4);
    ctx.stroke();

    // 4. Two-Handed Combat Assault Rifle
    ctx.fillStyle = "#1e2838";
    ctx.fillRect(cs * 0.05, -cs * 0.05, cs * 0.35, cs * 0.1);
    ctx.strokeStyle = "#8099b8";
    ctx.strokeRect(cs * 0.05, -cs * 0.05, cs * 0.35, cs * 0.1);

    // Red/Cyan laser sight dot at muzzle
    ctx.fillStyle = primary;
    ctx.fillRect(cs * 0.4, -cs * 0.02, 3, 3);
  }

  /**
   * MINER: Heavy Industrial Harvester with Front Cutting Drill & Crystal Cargo Hopper
   */
  drawMiner(ctx, cs, isBlue, carriedRes = 0) {
    const primary = isBlue ? "#00e5ff" : "#ff2a5f";

    // 1. Heavy Industrial Harvester Body
    ctx.fillStyle = "#2c3340";
    ctx.fillRect(-cs * 0.32, -cs * 0.26, cs * 0.58, cs * 0.52);

    // Hazard Stripes (yellow & black industrial warning tape on chassis)
    ctx.fillStyle = "#ffb800";
    ctx.fillRect(-cs * 0.32, -cs * 0.26, cs * 0.58, 4);
    ctx.fillRect(-cs * 0.32, cs * 0.22, cs * 0.58, 4);

    // 2. Front Hydraulic Cutting Drill Rig / Claw
    const drillOffset = Math.sin(this.animTime * 12) * 2;
    ctx.fillStyle = "#708099";
    ctx.beginPath();
    ctx.moveTo(cs * 0.26 + drillOffset, -cs * 0.22);
    ctx.lineTo(cs * 0.44 + drillOffset, 0);
    ctx.lineTo(cs * 0.26 + drillOffset, cs * 0.22);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = primary;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Drill bit grooves
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cs * 0.32 + drillOffset, -cs * 0.12);
    ctx.lineTo(cs * 0.38 + drillOffset, 0);
    ctx.lineTo(cs * 0.32 + drillOffset, cs * 0.12);
    ctx.stroke();

    // 3. Rear Cargo Hopper (Loaded with Glowing Amber/Red Crystals)
    ctx.fillStyle = "#151b24";
    ctx.fillRect(-cs * 0.38, -cs * 0.20, cs * 0.16, cs * 0.4);
    ctx.strokeStyle = primary;
    ctx.strokeRect(-cs * 0.38, -cs * 0.20, cs * 0.16, cs * 0.4);

    // Glowing mineral gems inside hopper
    ctx.fillStyle = "#ffb800";
    ctx.beginPath();
    ctx.arc(-cs * 0.30, -cs * 0.08, 2.5, 0, Math.PI * 2);
    ctx.arc(-cs * 0.30, cs * 0.08, 2.5, 0, Math.PI * 2);
    ctx.fill();
  }

  /**
   * ENGINEER: Support Walker with Articulated Hydraulic Crane & Welding Torch
   */
  drawEngineer(ctx, cs, isBlue) {
    const primary = isBlue ? "#00e5ff" : "#ff2a5f";

    // 1. Support Exo-Chassis
    ctx.fillStyle = isBlue ? "#006080" : "#801228";
    ctx.beginPath();
    ctx.arc(0, 0, cs * 0.25, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = primary;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 2. Rotating Support Crane / Welder Arm
    const armAngle = Math.sin(this.animTime * 2) * 0.35;
    ctx.save();
    ctx.rotate(armAngle);
    ctx.strokeStyle = "#a0b3cc";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(cs * 0.35, 0);
    ctx.lineTo(cs * 0.45, cs * 0.12);
    ctx.stroke();

    // Welding Torch Tip & Glow
    ctx.fillStyle = "#00ffcc";
    ctx.beginPath();
    ctx.arc(cs * 0.45, cs * 0.12, 2.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // 3. Central Service Beacon
    ctx.fillStyle = Math.sin(this.animTime * 6) > 0 ? "#ffb800" : "#fff";
    ctx.beginPath();
    ctx.arc(0, 0, cs * 0.1, 0, Math.PI * 2);
    ctx.fill();
  }

  // =========================================================================
  // DYNAMIC COMBAT ANIMATION EFFECTS (Flamethrower, Plasma Arcs, Tracers)
  // =========================================================================
  renderCombatEvents(ctx, snap, cs) {
    const frameEvents = this.replayData.history[this.currentTurn]?.events || [];
    frameEvents.forEach((ev) => {
      if (ev.type === "attack_event") {
        const attacker = snap.units.find((u) => u.id === ev.attacker_id) || snap.structures.find((s) => s.id === ev.attacker_id);
        const target = snap.units.find((u) => u.id === ev.target_id) || snap.structures.find((s) => s.id === ev.target_id);

        if (attacker && target) {
          const ax = attacker.x * cs + cs / 2;
          const ay = attacker.y * cs + cs / 2;
          const tx = target.x * cs + cs / 2;
          const ty = target.y * cs + cs / 2;
          const isBlue = ev.attacker_team === "blue";

          ctx.save();
          if (attacker.type === "tank") {
            // Heavy Tank Cannon Blast & Tracer Round
            ctx.strokeStyle = isBlue ? "rgba(0, 229, 255, 0.9)" : "rgba(255, 60, 80, 0.9)";
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            // Muzzle flash at barrel
            ctx.fillStyle = "#ffcc00";
            ctx.beginPath();
            ctx.arc(ax, ay, 6, 0, Math.PI * 2);
            ctx.fill();

            // Heavy kinetic impact blast ring at target
            ctx.fillStyle = "rgba(255, 200, 50, 0.85)";
            ctx.beginPath();
            ctx.arc(tx, ty, cs * 0.45, 0, Math.PI * 2);
            ctx.fill();

          } else if (attacker.type === "soldier") {
            // Flamethrower / Assault Burst (just like the intense flamethrower in the image!)
            const ang = Math.atan2(ty - ay, tx - ax);
            const dist = Math.hypot(tx - ax, ty - ay);

            // Cone of fiery flame particles
            const grad = ctx.createLinearGradient(ax, ay, tx, ty);
            grad.addColorStop(0, "rgba(255, 255, 200, 0.9)");
            grad.addColorStop(0.3, "rgba(255, 160, 0, 0.85)");
            grad.addColorStop(0.8, "rgba(255, 50, 20, 0.7)");
            grad.addColorStop(1, "rgba(100, 10, 0, 0)");

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(ax + Math.cos(ang + 0.25) * dist, ay + Math.sin(ang + 0.25) * dist);
            ctx.lineTo(ax + Math.cos(ang - 0.25) * dist, ay + Math.sin(ang - 0.25) * dist);
            ctx.closePath();
            ctx.fill();

          } else {
            // Turret / Base Plasma Energy Beam
            ctx.strokeStyle = isBlue ? "rgba(0, 229, 255, 0.95)" : "rgba(255, 42, 95, 0.95)";
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            ctx.fillStyle = "#fff";
            ctx.beginPath();
            ctx.arc(tx, ty, 5, 0, Math.PI * 2);
            ctx.fill();
          }
          ctx.restore();
        }
      }
    });
  }

  drawHealthBar(ctx, x, y, width, hp, maxHp) {
    const barW = width - 4;
    const barH = 3.5;
    const bx = x + 2;
    const by = Math.max(0, y);

    ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
    ctx.fillRect(bx, by, barW, barH);

    const fillRatio = Math.max(0, Math.min(1, hp / maxHp));
    ctx.fillStyle = fillRatio > 0.5 ? "#00ff88" : (fillRatio > 0.25 ? "#ffb800" : "#ff3366");
    ctx.fillRect(bx, by, barW * fillRatio, barH);

    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 0.5;
    ctx.strokeRect(bx, by, barW, barH);
  }

  renderFogOfWar(ctx, snap, team) {
    const cs = this.cellSize;
    const visibleCoords = new Set();
    const teamUnits = (snap.units || []).filter((u) => u.alive && u.team === team);
    const teamStructs = (snap.structures || []).filter((s) => s.alive && s.team === team);

    [...teamUnits, ...teamStructs].forEach((source) => {
      const vr = source.vision || 5;
      const vrSq = vr * vr;
      for (let cy = Math.max(0, source.y - vr); cy <= Math.min(this.gridHeight - 1, source.y + vr); cy++) {
        for (let cx = Math.max(0, source.x - vr); cx <= Math.min(this.gridWidth - 1, source.x + vr); cx++) {
          const d2 = (cx - source.x) ** 2 + (cy - source.y) ** 2;
          if (d2 <= vrSq) {
            visibleCoords.add(`${cx},${cy}`);
          }
        }
      }
    });

    ctx.save();
    ctx.fillStyle = "rgba(8, 12, 20, 0.88)";
    for (let gy = 0; gy < this.gridHeight; gy++) {
      for (let gx = 0; gx < this.gridWidth; gx++) {
        if (!visibleCoords.has(`${gx},${gy}`)) {
          ctx.fillRect(gx * cs, gy * cs, cs, cs);
        }
      }
    }
    ctx.restore();
  }

  async runSimulationFromModal() {
    const blueBot = document.getElementById("run-blue-bot").value;
    const redBot = document.getElementById("run-red-bot").value;
    const turns = parseInt(document.getElementById("run-turns").value, 10);
    const seed = parseInt(document.getElementById("run-seed").value, 10);

    const btn = document.getElementById("btn-start-simulation");
    btn.disabled = true;
    btn.textContent = "Simulating Match...";

    try {
      const res = await fetch("/api/run-match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          blue: blueBot,
          red: redBot,
          turns: turns,
          seed: seed
        })
      });

      if (!res.ok) {
        throw new Error("HTTP error " + res.status);
      }

      const matchRes = await res.json();
      document.getElementById("modal-run-match").classList.add("hidden");
      this.loadReplay(matchRes.replay);
      this.play();
    } catch (e) {
      alert("Error executing match simulation: " + e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Simulate & Watch";
    }
  }

  async loadTournamentData() {
    try {
      const lbRes = await fetch("/api/tournament/leaderboard");
      if (lbRes.ok) {
        const lb = await lbRes.json();
        const tbody = document.getElementById("leaderboard-tbody");
        tbody.innerHTML = "";
        lb.forEach((row) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><b>#${row.rank}</b></td>
            <td><b>${row.name}</b></td>
            <td>${row.matches_played}</td>
            <td style="color:var(--color-green);">${row.wins}</td>
            <td style="color:var(--color-red);">${row.losses}</td>
            <td>${row.draws}</td>
            <td>${row.avg_score}</td>
            <td><b>${row.total_score}</b></td>
          `;
          tbody.appendChild(tr);
        });
      }

      const brRes = await fetch("/api/tournament/bracket");
      if (brRes.ok) {
        const br = await brRes.json();
        const bTree = document.getElementById("bracket-tree");
        bTree.innerHTML = "";
        (br.rounds || []).forEach((roundName) => {
          const rDiv = document.createElement("div");
          rDiv.className = "bracket-round";
          rDiv.innerHTML = `<h4 style="font-size:12px;color:var(--color-blue);">${roundName}</h4>`;
          const matches = (br.matches && br.matches[roundName]) || [];
          matches.forEach((m) => {
            const mDiv = document.createElement("div");
            mDiv.className = "bracket-match";
            mDiv.innerHTML = `
              <div class="bracket-team"><span>${m.blue_team?.name || "TBD"}</span></div>
              <div class="bracket-team"><span>${m.red_team?.name || "TBD"}</span></div>
            `;
            rDiv.appendChild(mDiv);
          });
          bTree.appendChild(rDiv);
        });
      }
    } catch (e) {
      console.log("Tournament data fetch failed");
    }
  }

  async submitTeamRegistration() {
    const name = document.getElementById("reg-team-name").value;
    const inst = document.getElementById("reg-institution").value;
    const members = document.getElementById("reg-members").value;
    const bot = document.getElementById("reg-bot-path").value;
    const statusMsg = document.getElementById("reg-status-msg");

    statusMsg.style.color = "var(--text-secondary)";
    statusMsg.textContent = "Validating submission...";

    try {
      const res = await fetch("/api/tournament/teams", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, institution: inst, members, bot_path: bot })
      });
      const data = await res.json();
      if (data.success) {
        statusMsg.style.color = "var(--color-green)";
        statusMsg.textContent = `Team registered successfully! ID: ${data.team_id}`;
        this.loadTournamentData();
      } else {
        statusMsg.style.color = "var(--color-red)";
        statusMsg.textContent = `Registration failed: ${data.error}`;
      }
    } catch (e) {
      statusMsg.style.color = "var(--color-red)";
      statusMsg.textContent = "Error: " + e.message;
    }
  }
}

window.addEventListener("DOMContentLoaded", () => {
  window.visualizer = new BotWarsVisualizer();
});
