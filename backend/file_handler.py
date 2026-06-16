"""
file_handler.py — Read/Write all JSON files + Backup/Restore

Handles persistence for donors, inventory, and blood requests.
Uses Python's built-in json module for serialization.
Supports backup and restore of all data files.
"""

import json
import os
import shutil

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backup")

DONORS_FILE = os.path.join(DATA_DIR, "donors.json")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")

# Default inventory — 10 units for each blood group
DEFAULT_INVENTORY = {
    "A+": 10, "A-": 10,
    "B+": 10, "B-": 10,
    "O+": 10, "O-": 10,
    "AB+": 10, "AB-": 10
}


def _ensure_dirs():
    """Create data and backup directories if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)


def _read_json(filepath, default):
    """Generic helper — read a JSON file or return *default* on failure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(filepath, data):
    """Generic helper — write data to a JSON file."""
    _ensure_dirs()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ── Donors ──────────────────────────────────────────────────────────

def load_donors():
    """Load the donors list from donors.json."""
    return _read_json(DONORS_FILE, [])


def save_donors(donors_list):
    """Save the donors list to donors.json."""
    _write_json(DONORS_FILE, donors_list)


# ── Inventory ───────────────────────────────────────────────────────

def load_inventory():
    """Load the blood stock HashMap from inventory.json."""
    data = _read_json(INVENTORY_FILE, None)
    if data is None or not isinstance(data, dict):
        # First run — initialise with defaults
        _write_json(INVENTORY_FILE, DEFAULT_INVENTORY)
        return dict(DEFAULT_INVENTORY)
    return data


def save_inventory(inventory_dict):
    """Save the blood stock HashMap to inventory.json."""
    _write_json(INVENTORY_FILE, inventory_dict)


# ── Blood Requests ──────────────────────────────────────────────────

def load_requests():
    """Load the blood requests list from requests.json."""
    return _read_json(REQUESTS_FILE, [])


def save_requests(requests_list):
    """Save the blood requests list to requests.json."""
    _write_json(REQUESTS_FILE, requests_list)


# ── Backup & Restore ───────────────────────────────────────────────

def backup_all():
    """
    Copy all three JSON files into data/backup/.
    Returns True on success, raises on failure.
    """
    _ensure_dirs()
    for filename in ("donors.json", "inventory.json", "requests.json"):
        src = os.path.join(DATA_DIR, filename)
        dst = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
    return True


def restore_all():
    """
    Restore all three JSON files from data/backup/.
    Returns True on success, raises if backup files are missing.
    """
    _ensure_dirs()
    restored = []
    for filename in ("donors.json", "inventory.json", "requests.json"):
        src = os.path.join(BACKUP_DIR, filename)
        dst = os.path.join(DATA_DIR, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            restored.append(filename)
        else:
            raise FileNotFoundError(
                f"Backup file not found: {filename}. "
                "Please create a backup first."
            )
    return True
