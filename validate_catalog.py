"""Validador local do catálogo. Não confirma a exatidão dos dados no jogo.
Uso: python validate_catalog.py
Opcional: python validate_catalog.py --check-links (consulta URLs, pode depender da rede).
"""
import argparse
import concurrent.futures
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from map_layout import REGION_ZONES

CATALOG = Path(__file__).resolve().parent / "quests.json"
JS_CATALOG = CATALOG.with_name("quests_data.js")
REQUIRED = {"name", "category", "status", "reward", "url", "access_verified"}
ALLOWED_CATEGORIES = {"Principal", "Side quest", "Especial / evento"}
ALLOWED_STATUSES = {"Pendente", "Free confirmado", "Excluída — Premium"}
LIST_FIELDS = ("types", "pokemon_required", "abilities_required")
URL_FIELDS = ("url", "source_detail", "source_index")


def read_js_catalog(path):
    """Extrai o JSON de `window.QUEST_CATALOG = ...;` antes de `window.MAP_REGIONS`."""
    text = path.read_text(encoding="utf-8")
    start_token = "window.QUEST_CATALOG = "
    start = text.index(start_token) + len(start_token)
    end = text.index(";\nwindow.MAP_REGIONS", start)
    return json.loads(text[start:end])


def outside_region_zone(quest):
    """True se x/y estiver fora da elipse da região (regiões desconhecidas usam 'Não definida')."""
    region = quest.get("region")
    zone = REGION_ZONES[region if isinstance(region, str) and region in REGION_ZONES else "Não definida"]
    value = ((quest["x"] - zone["cx"]) / zone["rx"]) ** 2 + ((quest["y"] - zone["cy"]) / zone["ry"]) ** 2
    return value > 1


def check_url(url):
    """Return an informational result; HEAD/HTTP restrictions are not treated as catalog errors."""
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "MapaQuestsFree/1.8 (catalog validator)"})
        with urlopen(req, timeout=5) as response:
            return url, response.status, "HEAD"
    except HTTPError as exc:
        if exc.code not in (403, 405, 501):
            return url, exc.code, "HTTP"
    except (URLError, TimeoutError, ValueError):
        return url, None, "REDE"
    try:
        req = Request(url, headers={"User-Agent": "MapaQuestsFree/1.8 (catalog validator)"})
        with urlopen(req, timeout=5) as response:
            return url, response.status, "GET"
    except HTTPError as exc:
        return url, exc.code, "HTTP"
    except (URLError, TimeoutError, ValueError):
        return url, None, "REDE"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-links", action="store_true", help="Verifica URLs na internet (não valida conteúdo).")
    args = parser.parse_args()
    try:
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERRO: não foi possível ler quests.json: {exc}")
    if not isinstance(data, list):
        raise SystemExit("ERRO: o catálogo precisa ser uma lista JSON.")

    errors, warnings, names, urls = [], [], [], set()
    for index, quest in enumerate(data, start=1):
        prefix = f"Registro {index}"
        if not isinstance(quest, dict):
            errors.append(f"{prefix}: precisa ser um objeto.")
            continue
        missing = REQUIRED - quest.keys()
        if missing:
            errors.append(f"{prefix}: campos ausentes: {', '.join(sorted(missing))}.")
        name = quest.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{prefix}: nome vazio ou inválido.")
            name = f"registro {index}"
        names.append(name.strip().casefold())
        if quest.get("category") not in ALLOWED_CATEGORIES:
            errors.append(f"{prefix} ({name}): categoria desconhecida.")
        status = quest.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix} ({name}): status desconhecido.")
        access = quest.get("access_verified")
        if not isinstance(access, bool):
            errors.append(f"{prefix} ({name}): access_verified deve ser booleano.")
        if access is True and status != "Free confirmado":
            errors.append(f"{prefix} ({name}): access_verified=true exige status Free confirmado.")
        if status == "Free confirmado" and access is not True:
            errors.append(f"{prefix} ({name}): status Free confirmado exige access_verified=true.")
        level = quest.get("level")
        if level is not None and (not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 999):
            errors.append(f"{prefix} ({name}): level deve ser inteiro entre 1 e 999 ou null.")
        for key in LIST_FIELDS:
            if key in quest and (not isinstance(quest[key], list) or any(not isinstance(v, str) for v in quest[key])):
                errors.append(f"{prefix} ({name}): {key} deve ser uma lista de textos.")
        for key in URL_FIELDS:
            value = quest.get(key)
            if not value:
                if key == "source_detail":
                    warnings.append(f"{prefix} ({name}): sem página individual declarada.")
                continue
            parsed = urlparse(value) if isinstance(value, str) else None
            if not parsed or parsed.scheme != "https" or parsed.netloc != "wiki.otponline.com":
                warnings.append(f"{prefix} ({name}): {key} não aponta para wiki.otponline.com.")
            elif key == "source_detail" and parsed.path.rstrip("/").casefold() in ("", "/quests"):
                warnings.append(f"{prefix} ({name}): source_detail aponta para o índice, não para uma página individual.")
            else:
                urls.add(value)
        for coord in ("x", "y"):
            value = quest.get(coord)
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100):
                errors.append(f"{prefix} ({name}): coordenada ilustrativa {coord} deve estar entre 0 e 100.")
        coords_ok = all(isinstance(quest.get(c), (int, float)) and not isinstance(quest.get(c), bool) for c in ("x", "y"))
        if coords_ok and outside_region_zone(quest):
            warnings.append(
                f"{prefix} ({name}): posição ({quest['x']}, {quest['y']}) fora da zona da região {quest.get('region')}. "
                "Rode: python map_layout.py"
            )
        if status == "Excluída — Premium" and access is True:
            errors.append(f"{prefix} ({name}): quest excluída Premium não pode estar marcada como Free verificada.")
        if status == "Pendente":
            source_note = quest.get("source_note", "")
            if not isinstance(source_note, str) or not source_note.strip():
                warnings.append(f"{prefix} ({name}): falta nota de verificação da fonte.")

    try:
        js_catalog = read_js_catalog(JS_CATALOG)
    except (OSError, ValueError) as exc:
        warnings.append(f"quests_data.js ausente ou ilegível ({exc}). Rode: python map_layout.py")
    else:
        if js_catalog != data:
            warnings.append("quests_data.js difere de quests.json. Rode: python map_layout.py")

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        errors.append("Nomes duplicados (ignorando maiúsculas/minúsculas): " + ", ".join(duplicates))

    counts = {}
    for quest in data:
        if isinstance(quest, dict):
            key = quest.get("status", "(sem status)")
            counts[key] = counts.get(key, 0) + 1
    print(f"Catálogo: {len(data)} registros")
    print("Categorias:")
    for category in sorted(ALLOWED_CATEGORIES):
        print(f"  - {category}: {sum(q.get('category') == category for q in data if isinstance(q, dict))}")
    print("Status:")
    for status, amount in sorted(counts.items()):
        print(f"  - {status}: {amount}")
    print(f"Nomes únicos: {len(set(names))}")
    print(f"URLs distintas para auditoria: {len(urls)}")
    for warning in warnings:
        print("AVISO:", warning)
    if args.check_links:
        print("\nVerificação de URLs (respostas HTTP não confirmam que o conteúdo é correto):")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(check_url, sorted(urls)))
        for url, status_code, method in results:
            if status_code is None or status_code >= 400:
                print(f"  AVISO [{method} {status_code or 'sem resposta'}] {url}")
        print(f"URLs consultadas: {len(results)}")
    if errors:
        for error in errors:
            print("ERRO:", error)
        raise SystemExit(1)
    print("OK: estrutura e regras internas do catálogo válidas.")
    print("Nota: a validação estrutural não confirma a exatidão dos dados no jogo ou na Wiki.")


if __name__ == "__main__":
    main()
