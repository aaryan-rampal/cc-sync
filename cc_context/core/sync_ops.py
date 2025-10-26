"""
Git remote sync operations for the Claude sessions repository.

This module handles syncing the sessions repo with a remote (Supabase) storage.
"""

import subprocess
import sys
from pathlib import Path
from cc_context.core.git_ops import get_claude_repo_path, is_claude_repo_initialized


def get_remote_url(remote_name: str = "supabase") -> str | None:
    """
    Get the URL of a remote in the Claude repo.

    Args:
        remote_name: Name of the remote (default: "supabase")

    Returns:
        str | None: Remote URL or None if not found
    """
    if not is_claude_repo_initialized():
        return None

    claude_path = get_claude_repo_path()

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", remote_name],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError:
        return None


def add_remote(url: str, remote_name: str = "supabase") -> bool:
    """
    Add or update a remote in the Claude sessions repo.

    Args:
        url: The remote URL (Supabase bucket URL)
        remote_name: Name of the remote (default: "supabase")

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        print("Error: Claude repo not initialized", file=sys.stderr)
        return False

    claude_path = get_claude_repo_path()

    # Check if remote already exists
    existing_url = get_remote_url(remote_name)

    try:
        if existing_url:
            # Update existing remote
            subprocess.run(
                ["git", "remote", "set-url", remote_name, url],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Updated remote '{remote_name}' to: {url}")
        else:
            # Add new remote
            subprocess.run(
                ["git", "remote", "add", remote_name, url],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Added remote '{remote_name}': {url}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error managing remote: {e.stderr}", file=sys.stderr)
        return False


def pull_from_remote(remote_name: str = "supabase", branch: str = "main") -> bool:
    """
    Pull from the remote, preferring remote changes on conflict.

    Args:
        remote_name: Name of the remote (default: "supabase")
        branch: Branch name (default: "main")

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        print("Error: Claude repo not initialized", file=sys.stderr)
        return False

    claude_path = get_claude_repo_path()

    try:
        # Pull with strategy to prefer remote changes on conflict
        subprocess.run(
            ["git", "pull", remote_name, branch, "-X", "theirs"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Pulled changes from '{remote_name}/{branch}'")
        return True

    except subprocess.CalledProcessError as e:
        # Pull failed - could be because remote is empty
        return False


def push_to_remote(remote_name: str = "supabase", branch: str = "main") -> bool:
    """
    Push to the remote.

    Args:
        remote_name: Name of the remote (default: "supabase")
        branch: Branch name (default: "main")

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        print("Error: Claude repo not initialized", file=sys.stderr)
        return False

    claude_path = get_claude_repo_path()

    try:
        subprocess.run(
            ["git", "push", "-u", remote_name, branch],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Pushed changes to '{remote_name}/{branch}'")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error pushing to remote: {e.stderr}", file=sys.stderr)
        return False


def sync_with_remote(url: str, remote_name: str = "supabase", branch: str = "main") -> bool:
    """
    Sync the Claude sessions repo with a remote.

    This function:
    1. Adds/updates the remote
    2. Tries to pull from remote
    3. If pull fails (empty remote), pushes local changes

    Args:
        url: The remote URL
        remote_name: Name of the remote (default: "supabase")
        branch: Branch name (default: "main")

    Returns:
        bool: True if successful, False otherwise
    """
    # Add/update remote
    if not add_remote(url, remote_name):
        return False

    # Try to pull
    if pull_from_remote(remote_name, branch):
        # Pull succeeded
        return True
    else:
        # Pull failed, try to push
        print(f"No existing data in remote, pushing local changes...")
        return push_to_remote(remote_name, branch)


def has_remote(remote_name: str = "supabase") -> bool:
    """
    Check if a remote exists in the Claude repo.

    Args:
        remote_name: Name of the remote (default: "supabase")

    Returns:
        bool: True if remote exists, False otherwise
    """
    return get_remote_url(remote_name) is not None
