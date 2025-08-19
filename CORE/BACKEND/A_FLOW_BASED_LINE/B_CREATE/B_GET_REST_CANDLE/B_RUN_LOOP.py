#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========== SETTINGS (top) ==========
import os
import sys
import time
import subprocess
from typing import Optional

SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"
SETTINGS_KEY = "RUN_CHECK_SCRIPTS"
SETTINGS_ENABLE_VALUE = "ENABLE"

# Run these once, sequentially, before the main loop starts
BEFORE_SCRIPTS = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/A_RESET/CHECK_IF_NEED_RESET.py",
]

THE_MAIN_SCRIPTS = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/B_CREATE/B_GET_REST_CANDLE/BA_GET_REST_CANDLE.py",
    "CORE/BACKEND/A_FLOW_BASED_LINE/C_CHECK/RUN_LIST.py",
]

# Optional: print a small header before running each script
PRINT_BEFORE_RUN = True

# ========== INTERNAL STATE (implementation) ==========
_interrupt_requested = False  # Set to True once KeyboardInterrupt is received mid-iteration


def _read_run_flag(path: str) -> bool:
    """
    Lightweight parser to read RUN_CHECK_SCRIPTS from the YAML file without external deps.
    Returns True iff the value is exactly 'ENABLE'.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Remove inline comments (naive but adequate)
                if "#" in line:
                    line = line.split("#", 1)[0].strip()
                if line.startswith(SETTINGS_KEY):
                    # Expect "RUN_CHECK_SCRIPTS: VALUE"
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        value = parts[1].strip()
                        return value == SETTINGS_ENABLE_VALUE
        # If key not found, treat as disabled
        return False
    except FileNotFoundError:
        print(f"⚠️  Не найден файл настроек: {path}")
        return False
    except Exception as e:
        print(f"⚠️  Ошибка чтения настроек '{path}': {e}")
        return False


def _launch_process(script_path: str) -> Optional[subprocess.Popen]:
    """
    Launch a Python script as a child process with unbuffered stdout/stderr.
    Child is placed in its own process group/session so it won't receive Ctrl+C.
    """
    try:
        # Ensure forward slashes always (safe on all OSes for Python)
        script = script_path.replace("\\", "/")

        if not os.path.exists(script):
            print(f"⚠️  Скрипт не найден: {script}")
            return None

        env = os.environ.copy()
        # Force unbuffered output for Python subprocess
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        # Create new process group/session to isolate from Ctrl+C
        creationflags = 0
        preexec_fn = None
        if os.name != "nt":
            import os as _os  # POSIX: start a new session
            preexec_fn = _os.setsid
        else:
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        cmd = [sys.executable, "-u", script]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout
            bufsize=1,                  # line-buffered in text mode
            universal_newlines=True,    # text mode
            encoding="utf-8",
            errors="replace",
            env=env,
            creationflags=creationflags,
            preexec_fn=preexec_fn,
        )
        return p
    except Exception as e:
        print(f"⚠️  Не удалось запустить '{script_path}': {e}")
        return None


def _stream_output(proc: subprocess.Popen) -> None:
    """
    Stream child's output to console in real time with no accumulation.
    Skip empty lines. Handle KeyboardInterrupt by setting a global flag.
    """
    global _interrupt_requested

    if proc.stdout is None:
        try:
            proc.wait()
            return
        except KeyboardInterrupt:
            _interrupt_requested = True
            proc.wait()
            return

    # Read line-by-line without accumulating
    while True:
        try:
            line = proc.stdout.readline()
            if line == "":
                # EOF
                break
            # Skip empty or whitespace-only lines
            if not line.strip():
                continue
            # Print as-is, ensure flush for real-time
            print(line, end="", flush=True)
        except KeyboardInterrupt:
            _interrupt_requested = True
            # Keep draining to finish this child gracefully
            continue

    # Ensure the process fully exits
    try:
        proc.wait()
    except KeyboardInterrupt:
        _interrupt_requested = True
        proc.wait()


def _run_one_script(script_path: str) -> int:
    """
    Run a single script and stream its output. Returns exit code (0 if launched).
    """
    p = _launch_process(script_path)
    if p is None:
        return 127  # indicate launch error similar to shell

    _stream_output(p)
    return p.returncode if p.returncode is not None else 0


def _run_before_scripts_once() -> None:
    """
    Run BEFORE_SCRIPTS exactly once, sequentially, streaming output.
    Completes the list even if Ctrl+C is pressed mid-script; sets a global flag.
    """
    global _interrupt_requested
    for script in BEFORE_SCRIPTS:
        try:
            _run_one_script(script)
        except KeyboardInterrupt:
            _interrupt_requested = True
            # Continue to run the rest of the scripts
            continue


def _run_sequence_once() -> None:
    """
    Execute the full list of scripts sequentially and finally print elapsed time.
    Ensures that if KeyboardInterrupt occurs between scripts, we still finish the list.
    """
    global _interrupt_requested
    started = time.time()

    for script in THE_MAIN_SCRIPTS:
        try:
            _run_one_script(script)
        except KeyboardInterrupt:
            # Mark request to exit after finishing this iteration,
            # but DO NOT abort the remaining scripts in the list.
            _interrupt_requested = True
            # Continue to run the rest of the scripts
            continue

    print(f"📌 - {time.time() - started:.3f} СЕКУНД")


def main() -> None:
    """
    Main flow:
    - If RUN_CHECK_SCRIPTS != ENABLE -> exit immediately.
    - If ENABLE -> run BEFORE_SCRIPTS once.
    - If no Ctrl+C during BEFORE_SCRIPTS, enter main loop that runs THE_MAIN_SCRIPTS.
    - If Ctrl+C happened during any run, finish current list then exit.
    """
    global _interrupt_requested

    # Initial gate: only proceed if ENABLE
    if not _read_run_flag(SETTINGS_PATH):
        return

    # Run one-time "before" scripts
    _run_before_scripts_once()
    if _interrupt_requested:
        return

    # Main loop (unchanged behavior)
    while True:
        # Check if we should run at all
        if not _read_run_flag(SETTINGS_PATH):
            # Not ENABLE -> do nothing and exit
            break

        # Run full sequence (handles Ctrl+C internally and still finishes)
        _run_sequence_once()

        # If during the last run we received Ctrl+C, exit now
        if _interrupt_requested:
            break

        # Re-check the flag before looping again
        if not _read_run_flag(SETTINGS_PATH):
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Final safety net: exit cleanly if something bubbles up unexpectedly
        pass
