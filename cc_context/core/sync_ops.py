"""
Git remote sync operations for the Claude sessions repository.

This module handles syncing the sessions repo with a remote (Supabase) storage
using Git bundles for compatibility with object storage services.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path
from cc_context.core.git_ops import get_claude_repo_path, is_claude_repo_initialized
import requests


def get_supabase_config() -> tuple[str, str, str] | None:
    """
    Get Supabase configuration from environment variables.

    Returns:
        tuple[str, str, str] | None: (url, service_key, bucket) or None if any are missing
    """
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    bucket = os.environ.get("SUPABASE_BUCKET")

    if not all([url, service_key, bucket]):
        return None

    return (url.rstrip('/'), service_key, bucket)


def get_storage_url(bucket: str, filename: str = "repo.bundle") -> str:
    """
    Construct Supabase Storage API URL.

    Args:
        bucket: Bucket name
        filename: File name (default: "repo.bundle")

    Returns:
        str: Full Storage API URL
    """
    config = get_supabase_config()
    if not config:
        raise ValueError("Supabase configuration not found in environment variables")

    url, _, bucket_name = config
    return f"{url}/storage/v1/object/public/{bucket_name}/{filename}"


def get_auth_headers() -> dict[str, str]:
    """
    Get authorization headers for Supabase Storage API.

    Returns:
        dict[str, str]: Headers with Authorization and Content-Type
    """
    config = get_supabase_config()
    if not config:
        raise ValueError("Supabase configuration not found in environment variables")

    _, service_key, _ = config
    return {
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/octet-stream"
    }


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
    Pull from the remote using Git bundles.

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

    # Get Supabase configuration
    config = get_supabase_config()
    if not config:
        print("Error: Missing Supabase configuration in environment variables", file=sys.stderr)
        print("Required: SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET", file=sys.stderr)
        return False

    url, _, bucket = config
    download_url = f"{url}/storage/v1/object/public/{bucket}/repo.bundle"

    try:
        # Download the bundle from Supabase
        print(f"Downloading bundle from remote...")
        response = requests.get(download_url, timeout=30)

        if response.status_code == 404:
            print("No existing data in remote")
            return False

        response.raise_for_status()

        # Save bundle to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bundle") as tmp:
            tmp.write(response.content)
            bundle_path = tmp.name

        try:
            # Fetch from bundle
            subprocess.run(
                ["git", "fetch", bundle_path, f"{branch}:{branch}"],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Merge with strategy to prefer remote changes on conflict
            subprocess.run(
                ["git", "merge", branch, "-X", "theirs", "--allow-unrelated-histories"],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )

            print(f"✓ Pulled changes from '{remote_name}/{branch}'")
            return True

        finally:
            # Clean up temp file
            Path(bundle_path).unlink(missing_ok=True)

    except requests.RequestException as e:
        print(f"Error downloading bundle: {e}", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error applying bundle: {e.stderr}", file=sys.stderr)
        return False


def push_to_remote(remote_name: str = "supabase", branch: str = "main") -> bool:
    """
    Push to the remote using Git bundles.

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

    # Get Supabase configuration
    config = get_supabase_config()
    if not config:
        print("Error: Missing Supabase configuration in environment variables", file=sys.stderr)
        print("Required: SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET", file=sys.stderr)
        return False

    url, service_key, bucket = config

    try:
        # Create a bundle with all refs
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bundle") as tmp:
            bundle_path = tmp.name

        try:
            # Create bundle
            print(f"Creating bundle...")
            subprocess.run(
                ["git", "bundle", "create", bundle_path, "--all"],
                cwd=claude_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Upload bundle to Supabase Storage
            print(f"Uploading bundle to remote...")
            upload_url = f"{url}/storage/v1/object/{bucket}/repo.bundle"

            with open(bundle_path, 'rb') as bundle_file:
                # Try POST first (for new files)
                response = requests.post(
                    upload_url,
                    files={'file': bundle_file},
                    headers={"Authorization": f"Bearer {service_key}"},
                    timeout=60
                )

                # If file exists, use PUT to update
                if response.status_code == 409:
                    bundle_file.seek(0)
                    update_url = f"{url}/storage/v1/object/{bucket}/repo.bundle"
                    response = requests.put(
                        update_url,
                        data=bundle_file,
                        headers={
                            "Authorization": f"Bearer {service_key}",
                            "Content-Type": "application/octet-stream"
                        },
                        timeout=60
                    )

                response.raise_for_status()

            print(f"✓ Pushed changes to '{remote_name}/{branch}'")
            return True

        finally:
            # Clean up temp file
            Path(bundle_path).unlink(missing_ok=True)

    except subprocess.CalledProcessError as e:
        print(f"Error creating bundle: {e.stderr}", file=sys.stderr)
        return False
    except requests.RequestException as e:
        print(f"Error uploading bundle: {e}", file=sys.stderr)
        return False


def sync_with_remote(remote_name: str = "supabase", branch: str = "main") -> bool:
    """
    Sync the Claude sessions repo with a remote using Supabase Storage.

    This function:
    1. Validates Supabase configuration from environment variables
    2. Tries to pull from remote
    3. If pull fails (empty remote), pushes local changes

    Args:
        remote_name: Name of the remote (default: "supabase")
        branch: Branch name (default: "main")

    Returns:
        bool: True if successful, False otherwise

    Required environment variables:
        SUPABASE_URL: Supabase project URL
        SUPABASE_SERVICE_KEY: Service role key for authentication
        SUPABASE_BUCKET: Storage bucket name
    """
    # Validate Supabase configuration
    config = get_supabase_config()
    if not config:
        print("Error: Missing Supabase configuration in environment variables", file=sys.stderr)
        print("", file=sys.stderr)
        print("Required environment variables:", file=sys.stderr)
        print("  SUPABASE_URL=https://your-project.supabase.co", file=sys.stderr)
        print("  SUPABASE_SERVICE_KEY=your-service-role-key", file=sys.stderr)
        print("  SUPABASE_BUCKET=your-bucket-name", file=sys.stderr)
        print("", file=sys.stderr)
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
