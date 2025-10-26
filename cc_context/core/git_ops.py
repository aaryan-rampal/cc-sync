"""
Git operations for managing the Claude sessions repository.

This module provides git operations for the parallel git repository
inside ~/.claude/projects/{encoded-path}/ that tracks session files.
"""

import subprocess
from pathlib import Path
from cc_context.utils.path import get_claude_storage_path


def get_claude_repo_path() -> Path:
    """Get the path to the Claude sessions directory (where the git repo lives)."""
    return get_claude_storage_path()


def is_claude_repo_initialized() -> bool:
    """Check if the Claude sessions directory has been initialized as a git repo."""
    claude_path = get_claude_repo_path()
    git_dir = claude_path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def init_claude_repo(skip_initial_commit: bool = False) -> bool:
    """
    Initialize a git repository in the Claude sessions directory.

    Args:
        skip_initial_commit: If True, skip creating the initial commit (default: False)

    Returns:
        bool: True if successful, False otherwise
    """
    claude_path = get_claude_repo_path()

    # Ensure the directory exists
    claude_path.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Skip initial commit if requested
        if skip_initial_commit:
            return True

        # Create an empty initial commit as the base state
        # This represents "no context" and serves as a fallback
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Empty initial state"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )

        # If there are existing session files, create a second commit with them
        session_files = list(claude_path.glob("*.jsonl"))

        if session_files:
            # Stage all .jsonl files
            subprocess.run(
                ["git", "add", "*.jsonl"],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Get the current commit SHA from the main repository
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                main_commit_sha = result.stdout.strip()
                commit_message = f"Initial Claude sessions\nContext for main repo commit {main_commit_sha}"
            except subprocess.CalledProcessError:
                # Fallback if we can't get the main repo SHA
                commit_message = "Initial Claude sessions"

            # Create commit with existing sessions
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error initializing Claude repo: {e.stderr}")
        return False


def add_session_files() -> bool:
    """
    Stage all .jsonl session files in the Claude directory.

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        print("Error: Claude repo not initialized. Run 'cc-init' first.")
        return False

    claude_path = get_claude_repo_path()

    # Check if there are any .jsonl files to add
    session_files = list(claude_path.glob("*.jsonl"))
    if not session_files:
        # No session files to add - this is fine, not an error
        return True

    try:
        subprocess.run(
            ["git", "add", "*.jsonl"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error adding session files: {e.stderr}")
        return False


def commit_sessions(main_commit_sha: str) -> bool:
    """
    Commit all staged session files with a message linking to main repo commit.

    Args:
        main_commit_sha: The commit SHA from the main repository

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        print("Error: Claude repo not initialized. Run 'cc-init' first.")
        return False

    claude_path = get_claude_repo_path()

    try:
        # Check if there are changes to commit
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )

        if not status_result.stdout.strip():
            # No changes to commit
            return True

        # Commit with message linking to main repo
        commit_message = f"Context for main repo commit {main_commit_sha}"
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error committing sessions: {e.stderr}")
        return False


def get_current_branch() -> str | None:
    """
    Get the current branch name in the Claude repo.

    Returns:
        str | None: Branch name or None if error
    """
    if not is_claude_repo_initialized():
        return None

    claude_path = get_claude_repo_path()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError:
        return None


def get_claude_commit_sha() -> str | None:
    """
    Get the current commit SHA in the Claude repo.

    Returns:
        str | None: Commit SHA or None if error
    """
    if not is_claude_repo_initialized():
        return None

    claude_path = get_claude_repo_path()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError:
        return None


def has_uncommitted_changes() -> bool:
    """
    Check if the Claude repo has uncommitted changes or untracked files.

    Returns:
        bool: True if there are uncommitted changes or untracked files, False otherwise
    """
    if not is_claude_repo_initialized():
        return False

    claude_path = get_claude_repo_path()

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())

    except subprocess.CalledProcessError:
        return False


def clean_untracked_files() -> bool:
    """
    Remove all untracked files and directories from the Claude repo.

    This ensures a clean working directory when switching branches.

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        return False

    claude_path = get_claude_repo_path()

    try:
        subprocess.run(
            ["git", "clean", "-fd"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error cleaning untracked files: {e.stderr}")
        return False


def stash_sessions(message: str) -> bool:
    """
    Create a stash with the given message (only if there are changes).

    Includes both tracked changes and untracked files.

    Args:
        message: Stash message

    Returns:
        bool: True if stash created or no changes, False on error
    """
    if not is_claude_repo_initialized():
        return False

    # Only stash if there are changes or untracked files
    if not has_uncommitted_changes():
        return True

    claude_path = get_claude_repo_path()

    try:
        subprocess.run(
            ["git", "stash", "push", "-u", "-m", message],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error stashing sessions: {e.stderr}")
        return False


def find_commit_by_main_sha(main_sha: str) -> str | None:
    """
    Find a Claude repo commit that references the given main repo SHA.

    Args:
        main_sha: The main repository commit SHA to search for

    Returns:
        str | None: Claude repo commit SHA if found, None otherwise
    """
    if not is_claude_repo_initialized():
        return None

    claude_path = get_claude_repo_path()

    try:
        # Search for commit messages containing the main SHA across all branches
        result = subprocess.run(
            ["git", "log", "--all", "--grep", main_sha, "--format=%H", "-n", "1"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )

        commit_sha = result.stdout.strip()
        return commit_sha if commit_sha else None

    except subprocess.CalledProcessError:
        return None


def get_initial_commit() -> str | None:
    """
    Get the first (initial) commit SHA in the Claude repo.

    Returns:
        str | None: Initial commit SHA or None if error
    """
    if not is_claude_repo_initialized():
        return None

    claude_path = get_claude_repo_path()

    try:
        result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError:
        return None


def checkout_commit(commit_sha: str) -> bool:
    """
    Checkout a specific commit in the Claude repo.

    Args:
        commit_sha: The commit SHA to checkout

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        return False

    claude_path = get_claude_repo_path()

    try:
        subprocess.run(
            ["git", "checkout", commit_sha],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error checking out commit: {e.stderr}")
        return False


def find_stash_by_message(pattern: str) -> str | None:
    """
    Find a stash entry matching the given pattern.

    Args:
        pattern: Pattern to search for in stash messages

    Returns:
        str | None: Stash reference (e.g., "stash@{0}") or None if not found
    """
    if not is_claude_repo_initialized():
        return None

    claude_path = get_claude_repo_path()

    try:
        result = subprocess.run(
            ["git", "stash", "list"],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse stash list to find matching entry
        for line in result.stdout.strip().split('\n'):
            if pattern in line:
                # Extract stash reference (e.g., "stash@{0}")
                stash_ref = line.split(':')[0].strip()
                return stash_ref

        return None

    except subprocess.CalledProcessError:
        return None


def pop_stash(stash_ref: str) -> bool:
    """
    Pop a specific stash by reference.

    Args:
        stash_ref: Stash reference (e.g., "stash@{0}")

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        return False

    claude_path = get_claude_repo_path()

    try:
        subprocess.run(
            ["git", "stash", "pop", stash_ref],
            cwd=claude_path,
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error popping stash: {e.stderr}")
        return False


def get_main_repo_branch() -> str | None:
    """
    Get the current branch name from the main repository (CWD).

    Returns:
        str | None: Branch name, "HEAD" if detached, or None on error
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError:
        return None


def is_detached_head(branch_name: str | None) -> bool:
    """
    Check if the branch name indicates detached HEAD state.

    Args:
        branch_name: Branch name from git rev-parse

    Returns:
        bool: True if detached HEAD, False otherwise
    """
    return branch_name == "HEAD"


def create_or_checkout_branch(branch_name: str, commit_sha: str | None = None) -> bool:
    """
    Create or checkout a branch in the Claude repo.

    If commit_sha is provided, uses 'git checkout -B' to create/reset the branch
    to that commit. Otherwise, just checks out the branch if it exists or creates it.

    Args:
        branch_name: Name of the branch to create/checkout
        commit_sha: Optional commit SHA to reset the branch to

    Returns:
        bool: True if successful, False otherwise
    """
    if not is_claude_repo_initialized():
        return False

    claude_path = get_claude_repo_path()

    try:
        if commit_sha:
            # Create or reset branch to specific commit
            subprocess.run(
                ["git", "checkout", "-B", branch_name, commit_sha],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # Try to checkout existing branch first
            result = subprocess.run(
                ["git", "checkout", branch_name],
                cwd=claude_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Branch doesn't exist, create it
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=claude_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error creating/checking out branch: {e.stderr}")
        return False


def get_commit_parents(commit_sha: str, in_main_repo: bool = True) -> list[str]:
    """
    Get the parent commit SHAs for a given commit.

    Args:
        commit_sha: The commit SHA to get parents for
        in_main_repo: If True, query main repo (CWD), else query Claude repo

    Returns:
        list[str]: List of parent commit SHAs (empty if no parents or error)
    """
    if not in_main_repo and not is_claude_repo_initialized():
        return []

    cwd = None if in_main_repo else get_claude_repo_path()

    try:
        result = subprocess.run(
            ["git", "rev-list", "--parents", "-n", "1", commit_sha],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )

        # Output format: "commit_sha parent1 parent2 ..."
        # Split and return all but the first (which is the commit itself)
        parts = result.stdout.strip().split()
        return parts[1:] if len(parts) > 1 else []

    except subprocess.CalledProcessError:
        return []


def find_context_for_commit_or_ancestor(main_sha: str, max_depth: int = 100) -> str | None:
    """
    Find Claude context for a commit or its nearest ancestor.

    Walks up the git history to find the first commit that has associated
    Claude context. This allows new commits to inherit context from their
    parent commits.

    Args:
        main_sha: The main repository commit SHA to start searching from
        max_depth: Maximum number of ancestors to check (default: 100)

    Returns:
        str | None: Claude repo commit SHA if found, None otherwise
    """
    if not is_claude_repo_initialized():
        return None

    visited = set()
    to_check = [main_sha]
    depth = 0

    while to_check and depth < max_depth:
        current_sha = to_check.pop(0)

        # Avoid infinite loops in case of weird git history
        if current_sha in visited:
            continue
        visited.add(current_sha)

        # Check if this commit has Claude context
        claude_commit = find_commit_by_main_sha(current_sha)
        if claude_commit:
            return claude_commit

        # Get parents and add them to the queue
        parents = get_commit_parents(current_sha, in_main_repo=True)
        to_check.extend(parents)
        depth += 1

    return None
