#!/usr/bin/env python3
"""Process management utilities to prevent zombie processes."""

import atexit
import os
import signal
import subprocess
from pathlib import Path


def cleanup_streamlit_processes():
    """Kill all running Streamlit processes on exit."""
    try:
        # Kill all streamlit processes
        subprocess.run(["pkill", "-9", "-f", "streamlit"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "python.*app.py"], capture_output=True)
        print("✅ Cleaned up all Streamlit processes")
    except Exception as e:
        print(f"Warning: Could not clean up processes: {e}")


def register_cleanup():
    """Register cleanup function to run on exit."""
    atexit.register(cleanup_streamlit_processes)

    # Also handle signals
    signal.signal(signal.SIGINT, lambda s, f: cleanup_streamlit_processes())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup_streamlit_processes())


def check_existing_processes():
    """Check for existing Streamlit processes and warn user."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "streamlit"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            if len(pids) > 0:
                print(f"⚠️ Warning: {len(pids)} Streamlit processes already running")
                return True
    except:
        pass
    return False


def ensure_single_instance():
    """Ensure only one instance of Streamlit is running."""
    if check_existing_processes():
        print("Killing existing Streamlit processes...")
        cleanup_streamlit_processes()
        import time
        time.sleep(2)