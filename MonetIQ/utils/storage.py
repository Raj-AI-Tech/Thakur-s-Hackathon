"""
utils/storage.py

Data persistence and state management layer for MonetIQ.
Handles all file I/O operations for state.json with safety and validation.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import shutil

# Constants
STATE_FILE = "state.json"
BACKUP_FILE = "state.backup.json"


def _get_default_state() -> Dict[str, Any]:
    """
    Get the default application state structure.

    Returns:
        Default state dictionary
    """
    return {
        "user": {
            "name": "",
            "currency": "INR"
        },
        "income": {
            "monthly": 0
        },
        "expenses": [],
        "budgets": {},
        "goals": [],
        "tax": {},
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
    }


def _validate_json_serializable(data: Any) -> bool:
    """
    Check if data is JSON serializable.

    Args:
        data: Data to validate

    Returns:
        True if serializable, False otherwise
    """
    try:
        json.dumps(data)
        return True
    except (TypeError, ValueError, OverflowError):
        return False


def _create_backup() -> None:
    """
    Create a backup of the current state file.
    Silently fails if state file doesn't exist.
    """
    try:
        if os.path.exists(STATE_FILE):
            shutil.copy2(STATE_FILE, BACKUP_FILE)
    except Exception:
        pass


def _restore_from_backup() -> Optional[Dict[str, Any]]:
    """
    Attempt to restore state from backup file.

    Returns:
        Restored state or None if restoration fails
    """
    try:
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                if isinstance(state, dict):
                    return state
    except Exception:
        pass

    return None


def load_state() -> Dict[str, Any]:
    """
    Load application state from state.json.

    Returns:
        State dictionary (always valid, never None)

    Behavior:
        - If file doesn't exist: creates default state
        - If file is corrupted: attempts backup recovery
        - If backup fails: returns default state
        - Always returns a valid dictionary
    """
    if not os.path.exists(STATE_FILE):
        default_state = _get_default_state()
        save_state(default_state)
        return default_state

    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)

            if not isinstance(state, dict):
                raise ValueError("State must be a dictionary")

            if 'metadata' not in state:
                state['metadata'] = {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }

            return state

    except (json.JSONDecodeError, ValueError, IOError):
        restored_state = _restore_from_backup()

        if restored_state:
            save_state(restored_state)
            return restored_state
        else:
            default_state = _get_default_state()
            save_state(default_state)
            return default_state


def save_state(state: Dict[str, Any]) -> bool:
    """
    Save application state to state.json.

    Args:
        state: State dictionary to save

    Returns:
        True if save successful, False otherwise

    Features:
        - Validates input type
        - Ensures JSON serializability
        - Updates last_updated timestamp
        - Creates backup before overwriting
        - Atomic write (temp file + rename)
    """
    if not isinstance(state, dict):
        return False

    if not _validate_json_serializable(state):
        return False

    if 'metadata' not in state:
        state['metadata'] = {}

    state['metadata']['last_updated'] = datetime.now().isoformat()

    _create_backup()

    temp_file = f"{STATE_FILE}.tmp"

    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        if os.path.exists(STATE_FILE):
            os.replace(temp_file, STATE_FILE)
        else:
            os.rename(temp_file, STATE_FILE)

        return True

    except (IOError, OSError):
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

        return False


def get_section(section: str, default: Any = None) -> Any:
    """
    Get a specific section from state.

    Args:
        section: Section key to retrieve
        default: Default value if section doesn't exist

    Returns:
        Section value or default

    Examples:
        >>> get_section('income')
        {'monthly': 50000}
        >>> get_section('expenses', [])
        [...]
    """
    state = load_state()
    return state.get(section, default)


def update_section(section: str, value: Any) -> bool:
    """
    Update a specific section in state.

    Args:
        section: Section key to update
        value: New value for section

    Returns:
        True if update successful, False otherwise

    Features:
        - Loads current state
        - Updates only specified section
        - Preserves all other sections
        - Automatically persists changes
    """
    if not _validate_json_serializable(value):
        return False

    state = load_state()
    state[section] = value

    return save_state(state)


def append_to_section(section: str, item: Any) -> bool:
    """
    Append an item to a list-based section.

    Args:
        section: Section key (must be a list)
        item: Item to append

    Returns:
        True if append successful, False otherwise

    Features:
        - Validates item is serializable
        - Creates section as list if doesn't exist
        - Validates section is a list
        - Appends item and persists

    Used for:
        - Adding expenses
        - Adding goals
        - Adding transaction logs
    """
    if not _validate_json_serializable(item):
        return False

    state = load_state()
    section_data = state.get(section, [])

    if not isinstance(section_data, list):
        section_data = []

    section_data.append(item)
    state[section] = section_data

    return save_state(state)


def remove_from_section(section: str, index: int) -> bool:
    """
    Remove an item from a list-based section by index.

    Args:
        section: Section key (must be a list)
        index: Index of item to remove

    Returns:
        True if removal successful, False otherwise
    """
    state = load_state()
    section_data = state.get(section, [])

    if not isinstance(section_data, list):
        return False

    if index < 0 or index >= len(section_data):
        return False

    section_data.pop(index)
    state[section] = section_data

    return save_state(state)


def update_in_section(section: str, index: int, updated_item: Any) -> bool:
    """
    Update an item in a list-based section by index.

    Args:
        section: Section key (must be a list)
        index: Index of item to update
        updated_item: New item value

    Returns:
        True if update successful, False otherwise
    """
    if not _validate_json_serializable(updated_item):
        return False

    state = load_state()
    section_data = state.get(section, [])

    if not isinstance(section_data, list):
        return False

    if index < 0 or index >= len(section_data):
        return False

    section_data[index] = updated_item
    state[section] = section_data

    return save_state(state)


def clear_section(section: str) -> bool:
    """
    Clear a section (set to empty list or dict based on current type).

    Args:
        section: Section key to clear

    Returns:
        True if clear successful, False otherwise
    """
    state = load_state()

    if section not in state:
        return False

    current_value = state[section]

    if isinstance(current_value, list):
        state[section] = []
    elif isinstance(current_value, dict):
        state[section] = {}
    else:
        return False

    return save_state(state)


def reset_state(confirm: bool = False) -> bool:
    """
    Reset state to default values.

    Args:
        confirm: Must be True to actually reset (safety mechanism)

    Returns:
        True if reset successful, False otherwise

    Safety:
        - Only executes if confirm=True
        - Creates backup before reset
        - Used for debugging, demos, testing
    """
    if not confirm:
        return False

    _create_backup()
    default_state = _get_default_state()

    return save_state(default_state)


def get_metadata() -> Dict[str, Any]:
    """
    Get metadata section from state.

    Returns:
        Metadata dictionary
    """
    state = load_state()
    return state.get('metadata', {
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "version": "1.0"
    })


def state_exists() -> bool:
    """
    Check if state file exists.

    Returns:
        True if state.json exists, False otherwise
    """
    return os.path.exists(STATE_FILE)


def get_state_size() -> int:
    """
    Get size of state file in bytes.

    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        if os.path.exists(STATE_FILE):
            return os.path.getsize(STATE_FILE)
    except:
        pass

    return 0


def export_state(filepath: str) -> bool:
    """
    Export current state to a specified file.

    Args:
        filepath: Destination file path

    Returns:
        True if export successful, False otherwise
    """
    try:
        state = load_state()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        return True
    except:
        return False


def import_state(filepath: str) -> bool:
    """
    Import state from a specified file.

    Args:
        filepath: Source file path

    Returns:
        True if import successful, False otherwise

    Safety:
        - Validates file exists
        - Validates JSON format
        - Creates backup before importing
    """
    try:
        if not os.path.exists(filepath):
            return False

        with open(filepath, 'r', encoding='utf-8') as f:
            imported_state = json.load(f)

        if not isinstance(imported_state, dict):
            return False

        _create_backup()

        return save_state(imported_state)

    except:
        return False


def get_full_state() -> Dict[str, Any]:
    """
    Get the complete state object.

    Returns:
        Full state dictionary
    """
    return load_state()


def merge_section(section: str, updates: Dict[str, Any]) -> bool:
    """
    Merge updates into a dictionary-based section.

    Args:
        section: Section key (must be a dict)
        updates: Dictionary of updates to merge

    Returns:
        True if merge successful, False otherwise
    """
    if not isinstance(updates, dict):
        return False

    if not _validate_json_serializable(updates):
        return False

    state = load_state()
    section_data = state.get(section, {})

    if not isinstance(section_data, dict):
        section_data = {}

    section_data.update(updates)
    state[section] = section_data

    return save_state(state)


def delete_section(section: str) -> bool:
    """
    Delete a section from state.

    Args:
        section: Section key to delete

    Returns:
        True if deletion successful, False otherwise
    """
    state = load_state()

    if section not in state:
        return False

    if section == 'metadata':
        return False

    del state[section]

    return save_state(state)


def section_exists(section: str) -> bool:
    """
    Check if a section exists in state.

    Args:
        section: Section key to check

    Returns:
        True if section exists, False otherwise
    """
    state = load_state()
    return section in state


def get_section_keys() -> List[str]:
    """
    Get all top-level section keys.

    Returns:
        List of section keys
    """
    state = load_state()
    return list(state.keys())


def filter_section(section: str, filter_func) -> List[Any]:
    """
    Filter items in a list-based section.

    Args:
        section: Section key (must be a list)
        filter_func: Function to filter items (returns True to keep)

    Returns:
        Filtered list of items
    """
    section_data = get_section(section, [])

    if not isinstance(section_data, list):
        return []

    try:
        return [item for item in section_data if filter_func(item)]
    except:
        return []


def count_section_items(section: str) -> int:
    """
    Count items in a list-based section.

    Args:
        section: Section key

    Returns:
        Number of items, or 0 if section is not a list
    """
    section_data = get_section(section, [])

    if isinstance(section_data, list):
        return len(section_data)

    return 0