"""Steam session environment tests."""
import importlib.util
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("steam_session", SCRIPTS / "steam-session.py")
steam_session = importlib.util.module_from_spec(spec)
spec.loader.exec_module(steam_session)


class EnvironmentTests(unittest.TestCase):
    def test_restores_session_and_removes_steam_library_injection(self):
        raw = (b"DISPLAY=:91\0DBUS_SESSION_BUS_ADDRESS=unix:path=/private/bus\0"
               b"HOME=/fixture/home\0LD_PRELOAD=steam-overlay.so\0LD_LIBRARY_PATH=/scout\0"
               b"LD_AUDIT=audit.so\0STEAM_RUNTIME=1\0STEAM_RUNTIME_LIBRARY_PATH=/scout\0"
               b"TOKEN_WITH_EQUALS=a=b\0")
        env = steam_session.session_environment(raw, {
            "DISPLAY": ":92", "LD_PRELOAD": "wrong.so", "NP_NOITA_ADDR": "127.0.0.1:21252",
            "PROTON_LOG": "1", "PROTON_LOG_DIR": "/fixture/logs",
        })
        self.assertEqual(env["DISPLAY"], ":91")
        self.assertEqual(env["DBUS_SESSION_BUS_ADDRESS"], "unix:path=/private/bus")
        self.assertEqual(env["NP_NOITA_ADDR"], "127.0.0.1:21252")
        self.assertEqual(env["TOKEN_WITH_EQUALS"], "a=b")
        self.assertEqual(env["PROTON_LOG_DIR"], "/fixture/logs")
        self.assertEqual(env["PROTON_LOG"], "1")
        self.assertEqual(env["SteamAppId"], "881100")
        self.assertEqual(env["SteamGameId"], "881100")
        for key in ("LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "STEAM_RUNTIME", "STEAM_RUNTIME_LIBRARY_PATH"):
            self.assertNotIn(key, env)


if __name__ == "__main__":
    unittest.main()
