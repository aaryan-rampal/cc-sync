#!/usr/bin/env python3
"""
cc-sync: Sync Claude sessions with a remote Supabase bucket.

This command sets up and syncs the Claude sessions repo with a remote storage.
"""

import sys
from cc_context.core.git_ops import (
    get_claude_repo_path,
    is_claude_repo_initialized,
    init_claude_repo
)
from cc_context.core.sync_ops import sync_with_remote, pull_from_remote, add_remote
from cc_context.utils.path import get_repo_root


def sync(supabase_url: str):
    """
    Sync Claude sessions with a remote Supabase bucket.

    This handles two scenarios:
    1. If Claude repo exists: sync with remote (pull or push)
    2. If Claude repo doesn't exist: init without initial commit, then pull

    Args:
        supabase_url: The Supabase bucket URL to use as remote
    """
    try:
        # Verify we're in a git repository
        repo_root = get_repo_root()
    except Exception as e:
        print("❌ Error: Not in a git repository", file=sys.stderr)
        print("   Run this command from inside a git repository", file=sys.stderr)
        return 1

    claude_path = get_claude_repo_path()

    # Check if Claude repo is initialized
    if is_claude_repo_initialized():
        # Mode A: Normal sync (Claude repo exists)
        print(f"Main repository: {repo_root}")
        print(f"Claude sessions directory: {claude_path}")
        print()
        print("Syncing with remote...")
        print()

        if sync_with_remote(supabase_url):
            print()
            print("=" * 60)
            print("🎉 Successfully synced with remote!")
            print("=" * 60)
            return 0
        else:
            print()
            print("❌ Failed to sync with remote", file=sys.stderr)
            return 1

    else:
        # Mode B: Init + pull (Claude repo doesn't exist)
        print(f"Main repository: {repo_root}")
        print(f"Claude sessions directory: {claude_path}")
        print()
        print("Claude sessions repo not initialized. Initializing and pulling from remote...")
        print()

        # Initialize without initial commit
        claude_path.mkdir(parents=True, exist_ok=True)
        if not init_claude_repo(skip_initial_commit=True):
            print("❌ Failed to initialize Claude sessions repo", file=sys.stderr)
            return 1

        print("✓ Initialized Claude sessions repo")

        # Add remote
        if not add_remote(supabase_url):
            print("❌ Failed to add remote", file=sys.stderr)
            return 1

        # Pull from remote
        if not pull_from_remote():
            print("❌ Failed to pull from remote. Is the remote empty?", file=sys.stderr)
            return 1

        print()
        print("=" * 60)
        print("🎉 Successfully initialized and pulled from remote!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  • Install git hooks: cc-install-hook")
        print("    This will automatically sync after each commit")
        print()
        return 0


def main():
    """Entry point for cc-sync command."""
    if len(sys.argv) < 2:
        print("Usage: cc-sync <supabase_url>", file=sys.stderr)
        print()
        print("Example:")
        print("  cc-sync https://your-project.supabase.co/storage/v1/...")
        print()
        return 1

    supabase_url = sys.argv[1]
    sys.exit(sync(supabase_url))


if __name__ == "__main__":
    main()
