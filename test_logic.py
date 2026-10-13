"""Testes offline da lógica; não abrem a interface gráfica nem acessam a internet."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from main import QuestApp
from map_layout import REGION_ZONES, layout_positions


class FakeVar:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class ProgressionTests(unittest.TestCase):
    def setUp(self):
        self.app = QuestApp.__new__(QuestApp)
        self.app.level = FakeVar(100)
        self.app.filter_by_level = FakeVar(False)
        self.app.search = FakeVar("")
        self.app.status_filter = FakeVar("Todas")
        self.app.region_filter = FakeVar("Todas")
        self.app.category_filter = FakeVar("Todas")
        self.app.hide_completed = FakeVar(False)
        self.app.completed_quests = set()
        self.app.quest_data = [
            {"name": "Free pronta", "level": 50, "status": "Free confirmado", "access_verified": True, "category":"Principal", "region":"Kanto", "reward":"Pedra", "notes":"", "types":[], "pokemon_required":[], "abilities_required":[]},
            {"name": "Free futura", "level": 250, "status": "Free confirmado", "access_verified": True, "category":"Principal", "region":"Kanto", "reward":"Pedra", "notes":"", "types":[], "pokemon_required":[], "abilities_required":[]},
            {"name": "Pendente perto", "level": 75, "status": "Pendente", "access_verified": False, "category":"Side quest", "region":"Johto", "reward":"Chave", "notes":"", "types":[], "pokemon_required":[], "abilities_required":[], "prerequisites":"Ter Surf"},
            {"name": "Premium", "level": 20, "status": "Excluída — Premium", "access_verified": False, "category":"Principal", "region":"Kanto", "reward":"", "notes":"", "types":[], "pokemon_required":[], "abilities_required":[]},
            {"name": "Sem nível", "level": None, "status": "Pendente", "access_verified": False, "category":"Especial / evento", "region":"Evento", "reward":"", "notes":"", "types":[], "pokemon_required":[], "abilities_required":[]},
        ]

    def test_pending_never_appears_as_confirmed_recommendation(self):
        ready, upcoming, research = self.app._progress_candidates()
        self.assertEqual([q["name"] for q in ready], ["Free pronta"])
        self.assertEqual([q["name"] for q in upcoming], ["Free futura"])
        self.assertEqual([q["name"] for q in research], ["Pendente perto"])
        self.assertNotIn("Pendente perto", [q["name"] for q in ready + upcoming])
        self.assertNotIn("Premium", [q["name"] for q in ready + upcoming + research])

    def test_completed_quest_is_removed_from_all_progression_panels(self):
        self.app.completed_quests.add("Free pronta")
        ready, upcoming, research = self.app._progress_candidates()
        self.assertNotIn("Free pronta", [q["name"] for q in ready + upcoming + research])

    def test_catalog_shows_future_levels_by_default(self):
        names = [q["name"] for q in self.app._filtered()]
        self.assertIn("Free futura", names)

    def test_level_filter_is_explicit_and_hides_future_levels_only_when_enabled(self):
        self.app.filter_by_level.set(True)
        names = [q["name"] for q in self.app._filtered()]
        self.assertNotIn("Free futura", names)
        self.assertIn("Free pronta", names)

    def test_search_includes_prerequisites_and_abilities(self):
        self.app.search.set("surf")
        names = [q["name"] for q in self.app._filtered()]
        self.assertIn("Pendente perto", names)
        self.assertNotIn("Free pronta", names)

    def test_status_filter_excludes_premium_from_default_free_workflow(self):
        names = [q["name"] for q in self.app._filtered()]
        self.assertNotIn("Premium", names)
        self.app.status_filter.set("Excluída")
        self.assertEqual([q["name"] for q in self.app._filtered()], ["Premium"])


class ProgressStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "progress.json"
        self.app = QuestApp.__new__(QuestApp)
        self.app.quest_data = [{"name": "Boost Free"}, {"name": "Jungle"}]
        self.app.completed_quests = {"Jungle"}
        self.app.level = FakeVar(325)
        self.app.filter_by_level = FakeVar(True)
        self.app.progress_file = lambda: self.path

    def tearDown(self): self.temp.cleanup()

    def test_reads_legacy_list_format(self):
        self.path.write_text(json.dumps(["Jungle", "Missing Quest"]), encoding="utf-8")
        self.assertEqual(self.app.load_progress(), {"Jungle"})
        self.assertEqual(self.app.saved_level, 1)
        self.assertFalse(self.app.saved_filter_by_level)

    def test_reads_new_profile_format(self):
        self.path.write_text(json.dumps({"player_level": 325, "filter_catalog_by_level": True, "completed": ["Jungle"]}), encoding="utf-8")
        self.assertEqual(self.app.load_progress(), {"Jungle"})
        self.assertEqual(self.app.saved_level, 325)
        self.assertTrue(self.app.saved_filter_by_level)

    def test_saves_level_filter_and_completed_quests(self):
        self.assertTrue(self.app.save_progress())
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["player_level"], 325)
        self.assertTrue(data["filter_catalog_to_level"] if "filter_catalog_to_level" in data else data["filter_catalog_by_level"])
        self.assertEqual(data["completed"], ["Jungle"])


class WikiIndexAuditTests(unittest.TestCase):
    def test_current_index_levels_corrected(self):
        import json
        from pathlib import Path
        data=json.loads((Path(__file__).parent / "quests.json").read_text(encoding="utf-8"))
        by_name={q["name"]:q for q in data}
        self.assertEqual(by_name["A Lost Melody"]["level"],400)
        self.assertEqual(by_name["Boost Hell"]["level"],250)
        self.assertEqual(by_name["Milotic"]["level"],131)
    def test_index_only_does_not_promote_pending_access(self):
        import json
        from pathlib import Path
        data=json.loads((Path(__file__).parent / "quests.json").read_text(encoding="utf-8"))
        for q in data:
            if q["name"] != "Boost Free" and not str(q.get("status","")).startswith("Excluída"):
                self.assertFalse(q.get("access_verified") is True,q["name"])


class PremiumClassificationRegressionTests(unittest.TestCase):
    def test_999_requires_vip_and_is_not_free(self):
        import json
        from pathlib import Path
        data=json.loads((Path(__file__).parent / "quests.json").read_text(encoding="utf-8"))
        q=next(item for item in data if item["name"]=="999")
        self.assertEqual(q["status"], "Excluída — Premium")
        self.assertFalse(q["access_verified"])
        self.assertIn("Porta_999", q["source_detail"])

    def test_known_premium_entries_are_not_recommended_as_free(self):
        import json
        from pathlib import Path
        data=json.loads((Path(__file__).parent / "quests.json").read_text(encoding="utf-8"))
        by_name={q["name"]:q for q in data}
        for name in ("A Lost Melody","Boost Hell","Burned","Milotic","Remembrance","999"):
            self.assertEqual(by_name[name]["status"], "Excluída — Premium", name)


ROOT = Path(__file__).resolve().parent


def read_js_catalog(path):
    """Extrai o JSON de `window.QUEST_CATALOG = ...;` antes de `window.MAP_REGIONS`."""
    text = path.read_text(encoding="utf-8")
    start_token = "window.QUEST_CATALOG = "
    start = text.index(start_token) + len(start_token)
    end = text.index(";\nwindow.MAP_REGIONS", start)
    return json.loads(text[start:end])


class MapLayoutTests(unittest.TestCase):
    def load_catalog(self):
        return json.loads((ROOT / "quests.json").read_text(encoding="utf-8"))

    def test_quests_data_js_catalog_matches_quests_json(self):
        self.assertEqual(read_js_catalog(ROOT / "quests_data.js"), self.load_catalog())

    def test_every_quest_lies_inside_its_region_zone(self):
        for quest in self.load_catalog():
            with self.subTest(quest=quest["name"]):
                self.assertIsNotNone(quest.get("x"))
                self.assertIsNotNone(quest.get("y"))
                region = quest.get("region") if quest.get("region") in REGION_ZONES else "Não definida"
                zone = REGION_ZONES[region]
                value = ((quest["x"] - zone["cx"]) / zone["rx"]) ** 2 + ((quest["y"] - zone["cy"]) / zone["ry"]) ** 2
                self.assertLessEqual(value, 1, f"{quest['name']} fora da zona de {region}")

    def test_layout_positions_is_deterministic(self):
        stripped = [{k: v for k, v in q.items() if k not in ("x", "y")} for q in self.load_catalog()]
        first = layout_positions(copy.deepcopy(stripped))
        second = layout_positions(copy.deepcopy(stripped))
        self.assertEqual(
            [(q["name"], q["x"], q["y"]) for q in first],
            [(q["name"], q["x"], q["y"]) for q in second],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
