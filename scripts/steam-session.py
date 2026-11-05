#!/usr/bin/env python3
"""Restore Steam's environment after `flatpak enter` (which does not do so)."""
import os
import sys
from pathlib import Path


def session_environment(raw, overrides):
    env = {}
    for entry in raw.split(b"\0"):
        if b"=" in entry:
            key, value = entry.split(b"=", 1)
            env[os.fsdecode(key)] = os.fsdecode(value)
    # Use the Flatpak runtime's libraries, not Steam's scout runtime libraries.
    for key in ("LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "STEAM_RUNTIME", "STEAM_RUNTIME_LIBRARY_PATH"):
        env.pop(key, None)
    # Keep explicit proxy settings and optional Proton diagnostics from the caller.
    env.update({key: value for key, value in overrides.items()
                if key.startswith("NP_") or key in ("PROTON_LOG", "PROTON_LOG_DIR")})
    env["PATH"] = "/app/bin:/app/utils/bin:/usr/bin:/bin"
    env["SteamAppId"] = "881100"
    env["SteamGameId"] = "881100"
    return env


def main():
    if len(sys.argv) < 3 or not sys.argv[1].isdigit():
        raise SystemExit("Usage: steam-session.py STEAM_PID /absolute/path/to/proxy [args...]")
    process = Path("/proc") / sys.argv[1]
    try:
        if (process / "comm").read_text().strip() != "steam":
            raise SystemExit("The selected Steam process is no longer running.")
        env = session_environment((process / "environ").read_bytes(), os.environ)
    except OSError as error:
        raise SystemExit(f"Cannot read Steam's session: {error}") from error
    command = sys.argv[2:]
    if not Path(command[0]).is_absolute():
        raise SystemExit("The proxy executable must have an absolute path.")
    try:
        os.execve(command[0], command, env)
    except OSError as error:
        raise SystemExit(f"Cannot start proxy inside Steam's sandbox: {error}. "
                         "Keep the proxy and launcher in a directory accessible to Flatpak Steam.") from error


if __name__ == "__main__":
    main()
