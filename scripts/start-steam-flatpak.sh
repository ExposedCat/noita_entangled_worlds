#!/usr/bin/env bash
# Join the running Steam sandbox so Steam IPC uses the same process namespace.
set -euo pipefail

script_dir="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
proxy="$(readlink -f -- "${NP_PROXY_PATH:-$script_dir/noita_proxy.x86_64}")"
if [[ ! -x "$proxy" ]]; then
    printf 'Proxy executable not found: %s\nExtract the Linux release beside this script, or set NP_PROXY_PATH.\n' "$proxy" >&2
    exit 1
fi

flatpak_cmd=(flatpak)
if [[ -f /run/.containerenv ]] && command -v distrobox-host-exec >/dev/null; then
    flatpak_cmd=(distrobox-host-exec flatpak)
fi

overrides=()
for key in "${!NP_@}" PROTON_LOG PROTON_LOG_DIR; do
    if [[ -v "$key" ]]; then
        overrides+=("$key=${!key}")
    fi
done

steam_pid_file="$HOME/.var/app/com.valvesoftware.Steam/.steam/steam.pid"
steam_pid="$(cat "$steam_pid_file" 2>/dev/null || true)"
if [[ ! "$steam_pid" =~ ^[0-9]+$ ]]; then
    printf 'Start Flatpak Steam first, then run this launcher.\n' >&2
    exit 1
fi

instances="$("${flatpak_cmd[@]}" ps --columns=instance,application)"
while read -r instance app; do
    [[ "$app" == com.valvesoftware.Steam ]] || continue
    probe="$("${flatpak_cmd[@]}" enter "$instance" /usr/bin/sh -c \
        'test -x /app/bin/steam && test -x /usr/bin/python3 && test "$(cat "/proc/$1/comm" 2>/dev/null)" = steam && printf steam-session-ready' sh "$steam_pid" 2>/dev/null || true)"
    if [[ "$probe" == steam-session-ready ]]; then
        exec "${flatpak_cmd[@]}" enter "$instance" \
            /usr/bin/env "${overrides[@]}" /usr/bin/python3 "$script_dir/steam-session.py" "$steam_pid" "$proxy" "$@"
    fi
done <<< "$instances"

printf 'No running Steam session found. Start Flatpak Steam first.\n' >&2
exit 1
