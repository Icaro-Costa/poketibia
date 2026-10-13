"""Abre o mapa Three.js em processo separado para não bloquear a interface Tkinter."""
import json
import sys
from pathlib import Path

import webview


def progress_path():
    return Path.home() / ".mapa_quests_free" / "progress.json"


class CatalogApi:
    def __init__(self, catalog_path):
        self.catalog_path = Path(catalog_path)

    def get_quests(self):
        try:
            return json.loads(self.catalog_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def get_progress(self):
        """Lê o progresso salvo pelo app principal; nunca levanta exceção."""
        empty = {"level": None, "completed": []}
        try:
            data = json.loads(progress_path().read_text(encoding="utf-8"))
            level = None
            if isinstance(data, dict):
                raw_level = data.get("player_level")
                if isinstance(raw_level, int) and not isinstance(raw_level, bool) and 1 <= raw_level <= 999:
                    level = raw_level
                completed = data.get("completed", [])
            elif isinstance(data, list):
                completed = data
            else:
                return empty
            if not isinstance(completed, list):
                completed = []
            return {"level": level, "completed": [n for n in completed if isinstance(n, str)]}
        except Exception:
            return empty


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    catalog_path = Path(args[0]) if args else base / "quests.json"
    html_path = (base / "mapa_3d.html").resolve().as_uri()
    api = CatalogApi(catalog_path)
    webview.create_window(
        "Mapa Quests Free · Mapa 3D",
        html_path,
        js_api=api,
        width=1280,
        height=850,
        min_size=(900, 600),
        background_color="#080d1b"
    )
    webview.start()


if __name__ == "__main__":
    main()
