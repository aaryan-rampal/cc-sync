#!/usr/bin/env python3
"""
cc-sync: Sync Claude sessions with a remote Supabase bucket.

This command sets up and syncs the Claude sessions repo with a remote storage.
"""

import sys
import os
from cc_context.core.git_ops import (
    get_claude_repo_path,
    is_claude_repo_initialized,
    init_claude_repo
)
from cc_context.core.sync_ops import sync_with_remote, pull_from_remote, get_supabase_config
from cc_context.utils.path import get_repo_root


def sync():
    """
    Sync Claude sessions with a remote Supabase bucket.

    This handles two scenarios:
    1. If Claude repo exists: sync with remote (pull or push)
    2. If Claude repo doesn't exist: init without initial commit, then pull

    Requires environment variables:
        SUPABASE_URL: Supabase project URL
        SUPABASE_SERVICE_KEY: Service role key for authentication
        SUPABASE_BUCKET: Storage bucket name
    """
    # Validate Supabase configuration
    if not get_supabase_config():
        print("❌ Error: Missing Supabase configuration", file=sys.stderr)
        print("", file=sys.stderr)
        print("Required environment variables:", file=sys.stderr)
        print("  SUPABASE_URL=https://your-project.supabase.co", file=sys.stderr)
        print("  SUPABASE_SERVICE_KEY=your-service-role-key", file=sys.stderr)
        print("  SUPABASE_BUCKET=your-bucket-name", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example setup:", file=sys.stderr)
        print("  export SUPABASE_URL=https://roohevslraawtssekwie.supabase.co", file=sys.stderr)
        print("  export SUPABASE_SERVICE_KEY=eyJhbGci...", file=sys.stderr)
        print("  export SUPABASE_BUCKET=claude-sessions", file=sys.stderr)
        print("", file=sys.stderr)
        return 1

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
        if sync_with_remote(verbose=True):
            print("✓ Synced successfully")
            return 0
        else:
            print("❌ Sync failed", file=sys.stderr)
            return 1

    else:
        # Mode B: Init + pull (Claude repo doesn't exist)
        print("Initializing Claude sessions repo...")

        # Initialize without initial commit
        claude_path.mkdir(parents=True, exist_ok=True)
        if not init_claude_repo(skip_initial_commit=True):
            print("❌ Failed to initialize", file=sys.stderr)
            return 1

        # Pull from remote
        if not pull_from_remote(verbose=True):
            print("❌ Failed to pull from remote", file=sys.stderr)
            return 1

        print("✓ Initialized and synced successfully")
        return 0


def main():
    """Entry point for cc-sync command."""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print("Usage: cc-sync")
        print()
        print("Sync Claude sessions with a remote Supabase bucket.")
        print()
        print("Setup (one-time):")
        print("  1. Create a bucket in Supabase dashboard (e.g., 'claude-sessions')")
        print("  2. Set environment variables:")
        print()
        print("     export SUPABASE_URL=https://your-project.supabase.co")
        print("     export SUPABASE_SERVICE_KEY=your-service-role-key")
        print("     export SUPABASE_BUCKET=your-bucket-name")
        print()
        print("  3. Add to your shell profile (~/.bashrc, ~/.zshrc, etc.) to persist")
        print()
        print("Usage:")
        print("  cc-sync")
        print()
        print("The command will automatically sync with your configured Supabase bucket.")
        print()
        return 0

    sys.exit(sync())


if __name__ == "__main__":
    main()
