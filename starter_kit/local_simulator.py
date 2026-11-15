#!/usr/bin/env python3
"""
PROXY BOT WARS - Local Match Simulator for Participants.
Allows participants to test their bots locally before submitting.

Usage:
    python local_simulator.py --blue starter_bot.py --red baseline_bot.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from match_runner.runner import main

if __name__ == "__main__":
    main()

