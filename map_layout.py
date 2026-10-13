"""Layout conceitual compartilhado pelo mapa 2D (Tkinter) e pelo mapa 3D (Three.js).

Cada região tem uma zona elíptica em coordenadas percentuais (0–100). As quests são
posicionadas dentro da zona da própria região em espiral (levels menores no centro).
Não são coordenadas oficiais do jogo.

Uso: python map_layout.py  → recalcula x/y em quests.json e regenera quests_data.js.
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# cx, cy = centro; rx, ry = raios da zona dos marcadores (em % da largura/altura do mapa).
REGION_ZONES = {
    "Kanto":        {"label": "KANTO",           "cx": 19, "cy": 47, "rx": 14, "ry": 33},
    "Johto":        {"label": "JOHTO",           "cx": 47, "cy": 35, "rx": 9,  "ry": 23},
    "Kalos":        {"label": "KALOS",           "cx": 74, "cy": 35, "rx": 12, "ry": 25},
    "Evento":       {"label": "ILHA DE EVENTOS", "cx": 51, "cy": 82, "rx": 10, "ry": 10},
    "Não definida": {"label": "NÃO DEFINIDA",    "cx": 82, "cy": 82, "rx": 10, "ry": 10},
}
MARKER_SPREAD = 0.85   # marcadores ocupam até 85% do raio da zona
ISLAND_SCALE = 1.12    # contorno da ilha um pouco maior que a zona
OUTLINE_POINTS = 18
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))


def zone_for(region):
    return REGION_ZONES.get(region, REGION_ZONES["Não definida"])


def island_outline(region):
    """Contorno determinístico (lista de [x, y] em %) com leve irregularidade."""
    zone = REGION_ZONES[region]
    rng = random.Random(region)
    jitter = [rng.uniform(-0.08, 0.08) for _ in range(OUTLINE_POINTS)]
    points = []
    for i in range(OUTLINE_POINTS):
        # Suaviza o ruído com os vizinhos para evitar pontas.
        j = (jitter[i - 1] + 2 * jitter[i] + jitter[(i + 1) % OUTLINE_POINTS]) / 4
        a = 2 * math.pi * i / OUTLINE_POINTS
        r = ISLAND_SCALE * (1 + j)
        x = zone["cx"] + zone["rx"] * r * math.cos(a)
        y = zone["cy"] + zone["ry"] * r * math.sin(a)
        points.append([round(min(99.0, max(1.0, x)), 2), round(min(99.0, max(1.0, y)), 2)])
    return points


def map_regions():
    return {name: dict(zone, outline=island_outline(name)) for name, zone in REGION_ZONES.items()}


def layout_positions(quests):
    """Atribui x/y (em %) a cada quest dentro da zona da sua região."""
    by_region = {}
    for q in quests:
        region = q.get("region") if q.get("region") in REGION_ZONES else "Não definida"
        by_region.setdefault(region, []).append(q)
    for region, items in by_region.items():
        zone = REGION_ZONES[region]
        items.sort(key=lambda q: (q.get("level") is None, q.get("level") or 0, q["name"].casefold()))
        n = len(items)
        for i, q in enumerate(items):
            r = MARKER_SPREAD * math.sqrt((i + 0.5) / n)
            a = i * GOLDEN_ANGLE
            q["x"] = round(zone["cx"] + zone["rx"] * r * math.cos(a), 1)
            q["y"] = round(zone["cy"] + zone["ry"] * r * math.sin(a), 1)
    return quests


def write_js(quests, path=ROOT / "quests_data.js"):
    path.write_text(
        "window.QUEST_CATALOG = " + json.dumps(quests, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "window.MAP_REGIONS = " + json.dumps(map_regions(), ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )


def main():
    catalog = ROOT / "quests.json"
    quests = json.loads(catalog.read_text(encoding="utf-8"))
    layout_positions(quests)
    catalog.write_text(json.dumps(quests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_js(quests)
    print(f"Layout aplicado a {len(quests)} quests; quests.json e quests_data.js atualizados.")


if __name__ == "__main__":
    main()
