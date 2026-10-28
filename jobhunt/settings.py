#!/usr/bin/env python3
"""Shared paths and config loading for the job-hunt scripts.

Everything is relative to the repo, so the scripts work from any clone.

Lookup order
  config : $JOBHUNT_CONFIG, else jobhunt/config.json, else jobhunt/config.example.json
  profile: $JOBHUNT_PROFILE, else profile/profile.json, else profile/profile.template.json
  data   : $JOBHUNT_DATA, else jobhunt/data/   (gitignored, never commit it)
  drafts : outreach/ at the repo root           (gitignored)

Copy config.example.json to config.json and profile.template.json to profile.json,
then edit the copies. The copies are gitignored so your personal data stays local.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

JOBHUNT = Path(__file__).resolve().parent
REPO = JOBHUNT.parent
OUTREACH = REPO / "outreach"      # generated drafts and batch trackers (gitignored)
TRACKER_DIR = REPO / "tracker"    # applications.csv and outreach-log.csv live here


def _warn(msg: str) -> None:
    print(f"[settings] {msg}", file=sys.stderr)


def config_path() -> Path:
    env = os.environ.get("JOBHUNT_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    real = JOBHUNT / "config.json"
    if real.exists():
        return real
    _warn("jobhunt/config.json not found, using config.example.json "
          "(copy it to config.json and edit).")
    return JOBHUNT / "config.example.json"


def profile_path() -> Path:
    env = os.environ.get("JOBHUNT_PROFILE")
    if env:
        return Path(env).expanduser().resolve()
    real = REPO / "profile" / "profile.json"
    if real.exists():
        return real
    _warn("profile/profile.json not found, using profile.template.json "
          "(copy it to profile.json and fill it in).")
    return REPO / "profile" / "profile.template.json"


def data_dir() -> Path:
    env = os.environ.get("JOBHUNT_DATA")
    d = Path(env).expanduser().resolve() if env else JOBHUNT / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_config() -> dict:
    with open(config_path(), encoding="utf-8") as f:
        return json.load(f)


def load_profile() -> dict:
    with open(profile_path(), encoding="utf-8") as f:
        return json.load(f)
