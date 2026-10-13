import json
import math
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import subprocess
import csv
import random
from tkinter import filedialog
from pathlib import Path
from map_layout import map_regions

APP_NAME = "Mapa Quests Free"
APP_VERSION = "1.8"

# --- Tema Pokédex (compartilhado com o mapa 3D) ---
RED = "#DC0A2D"          # vermelho Pokédex
RED_DARK = "#A00A22"
YELLOW = "#FFCB05"       # amarelo Pokémon
BLUE = "#2A75BB"
NAVY = "#1D2C5E"
CREAM = "#FFF8E7"
BG = "#F8F3E4"
SURFACE = "#FFFFFF"
SOFT = "#FDFAF1"
INK = "#1D2C5E"
TEXT = "#3C4767"
MUTED = "#6F7893"
LINE = "#E6DCC0"
SIDEBAR = NAVY
SIDEBAR_FIELD = "#2B3C7A"
BALL_LINE = "#15151F"

# Cores de status
GREEN = "#3BB273"        # Free confirmada
AMBER = "#F2A900"        # Pendente
PURPLE = "#8E5CD9"       # Premium / Excluída (Master Ball)
DONE = "#8A97B0"         # Concluída
GREEN_LIGHT = "#E1F5EA"
AMBER_LIGHT = "#FFF1CC"
PURPLE_LIGHT = "#EFE6FB"
DONE_LIGHT = "#E8ECF3"
RED_LIGHT = "#FDE3E8"
BLUE_LIGHT = "#E3EEF9"
GREEN_INK = "#1F8A57"    # variantes escuras para texto sobre fundo claro
AMBER_INK = "#9A6700"
PURPLE_INK = "#6A3FB5"
DONE_INK = "#5F6C87"

FONT = "Segoe UI" if sys.platform.startswith("win") else ("Helvetica Neue" if sys.platform == "darwin" else "DejaVu Sans")

# Mapa 2D
SEA = "#74CCD9"
FOAM = "#A9E5EB"
WAVE = "#C6F1F4"
SAND = "#F7EBC6"
SAND_EDGE = "#D8C58F"
LAND_COLORS = {
    "Kanto": ("#8FD27A", "#4E9A45"), "Johto": ("#C9BF63", "#8A7E2A"), "Kalos": ("#A9C2DA", "#6D7DB3"),
    "Evento": ("#EDC57E", "#B98A3E"), "Não definida": ("#D9DDE2", "#8F98A3"),
}

def resource_path(filename):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / filename

def status_color(status):
    if status.startswith("Free confirmado"):
        return GREEN
    if status.startswith("Excluída"):
        return PURPLE
    return AMBER

def status_bg(status):
    if status.startswith("Free confirmado"):
        return GREEN_LIGHT
    if status.startswith("Excluída"):
        return PURPLE_LIGHT
    return AMBER_LIGHT

def status_ink(status):
    if status.startswith("Free confirmado"):
        return GREEN_INK
    if status.startswith("Excluída"):
        return PURPLE_INK
    return AMBER_INK

def _rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

def mix(c1, c2, t):
    a, b = _rgb(c1), _rgb(c2)
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def darken(color, t=0.1):
    return mix(color, "#000000", t)

def lighten(color, t=0.1):
    return mix(color, "#FFFFFF", t)

def luminance(color):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in _rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def pill_button(parent, text, command, bg, fg, hover_bg=None, font=None, padx=12, pady=6, **kw):
    """Botão arredondado visualmente (tk.Label): no macOS tk.Button ignora as cores de fundo."""
    hover = hover_bg or darken(bg, 0.08)
    pressed = darken(bg, 0.16)
    btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=font or (FONT, 9, "bold"),
                   padx=padx, pady=pady, cursor="hand2", **kw)

    def paint(color):
        try:
            btn.configure(bg=color)
        except tk.TclError:
            pass

    def release(event):
        inside = 0 <= event.x < btn.winfo_width() and 0 <= event.y < btn.winfo_height()
        paint(hover if inside else bg)
        if inside and command:
            command()

    btn.bind("<Enter>", lambda _e: paint(hover))
    btn.bind("<Leave>", lambda _e: paint(bg))
    btn.bind("<ButtonPress-1>", lambda _e: paint(pressed))
    btn.bind("<ButtonRelease-1>", release)
    return btn

def round_rect(canvas, x1, y1, x2, y2, r=8, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
           x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(*pts, smooth=True, **kw)

def draw_pokeball(c, x, y, r, top, bottom="#FFFFFF", line=BALL_LINE, line_w=1.2, tags=(), button=True, lock=False):
    """Poké Ball: metade de cima na cor do status, de baixo branca, linha preta e botão central."""
    ids = [
        c.create_arc(x - r, y - r, x + r, y + r, start=180, extent=180, style="chord",
                     fill=bottom, outline=line, width=line_w, tags=tags),
        c.create_arc(x - r, y - r, x + r, y + r, start=0, extent=180, style="chord",
                     fill=top, outline=line, width=line_w, tags=tags),
        c.create_line(x - r, y, x + r, y, fill=line, width=line_w + 0.6, tags=tags),
    ]
    if button:
        b = max(1.8, r * 0.38)
        ids.append(c.create_oval(x - b, y - b, x + b, y + b, fill="#FFFFFF", outline=line, width=max(1, line_w), tags=tags))
        if lock:
            ids.append(c.create_rectangle(x - 2, y - 0.8, x + 2, y + 2, fill=line, outline="", tags=tags))
            ids.append(c.create_arc(x - 1.6, y - 3.2, x + 1.6, y + 0.4, start=0, extent=180, style="arc",
                                    outline=line, width=1, tags=tags))
    return ids

def draw_check(c, x, y, r, color="#FFFFFF", tags=()):
    """Pequeno ✓ desenhado na metade de cima da bola."""
    k = r / 8.0
    return c.create_line(x - 3.4 * k, y - 5.4 * k, x - 1.4 * k, y - 3.7 * k, x + 3.2 * k, y - 6.9 * k,
                         fill=color, width=1.6, capstyle="round", joinstyle="round", tags=tags)

def draw_star(c, x, y, r, fill=YELLOW, outline="#B58900", tags=()):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.extend([x + rr * math.cos(ang), y + rr * math.sin(ang)])
    return c.create_polygon(*pts, fill=fill, outline=outline, width=1, tags=tags)

def ball_icon(parent, size, top, bg):
    cv = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
    draw_pokeball(cv, size / 2.0, size / 2.0, size / 2.0 - 1.5, top, line_w=1.2 if size < 30 else 1.6)
    return cv

def draw_landmark(c, region, x, y, tags=()):
    """Marcos procedurais pequenos, só para dar vida às ilhas."""
    if region == "Kanto":  # Centro Pokémon
        c.create_polygon(x - 11, y - 2, x - 8, y - 9, x + 8, y - 9, x + 11, y - 2, fill=RED, outline=RED_DARK, tags=tags)
        c.create_rectangle(x - 9, y - 2, x + 9, y + 8, fill="white", outline=NAVY, width=1.2, tags=tags)
        c.create_rectangle(x - 2.2, y + 2, x + 2.2, y + 8, fill=BLUE, outline=NAVY, tags=tags)
        c.create_line(x, y - 7.5, x, y - 3.5, fill="white", width=2, tags=tags)
        c.create_line(x - 2, y - 5.5, x + 2, y - 5.5, fill="white", width=2, tags=tags)
    elif region == "Johto":  # pagode
        c.create_rectangle(x - 4.5, y - 2, x + 4.5, y + 9, fill="#F4E4B8", outline="#6B2A1F", tags=tags)
        for dy, half, col in ((7, 10, "#B8402C"), (1, 8, "#C94E36"), (-5, 6, "#D95F43")):
            c.create_polygon(x - half, y + dy, x, y + dy - 7, x + half, y + dy, fill=col, outline="#6B2A1F", width=1, tags=tags)
        c.create_line(x, y - 12, x, y - 16, fill="#6B2A1F", width=1.5, tags=tags)
    elif region == "Kalos":  # Torre Prisma
        c.create_polygon(x - 5, y + 11, x, y - 15, x + 5, y + 11, fill="#EAF3FB", outline=NAVY, width=1.2, tags=tags)
        c.create_line(x - 3.2, y + 1, x + 3.2, y + 1, fill=BLUE, width=1.2, tags=tags)
        c.create_line(x - 4.1, y + 6, x + 4.1, y + 6, fill=BLUE, width=1.2, tags=tags)
        c.create_line(x, y - 14, x, y + 11, fill="#9CB9D8", tags=tags)
        c.create_oval(x - 2, y - 17, x + 2, y - 13, fill=YELLOW, outline="#B58900", tags=tags)
    elif region == "Evento":  # árvore com estrela
        c.create_rectangle(x - 1.8, y + 3, x + 1.8, y + 10, fill="#8A5A2B", outline="", tags=tags)
        c.create_polygon(x - 9, y + 5, x, y - 6, x + 9, y + 5, fill="#2F9A55", outline="#1E6B3A", tags=tags)
        c.create_polygon(x - 7, y - 1, x, y - 11, x + 7, y - 1, fill="#3FB468", outline="#1E6B3A", tags=tags)
        draw_star(c, x, y - 13, 4.5, tags=tags)
    else:  # Não definida
        c.create_oval(x - 10, y - 10, x + 10, y + 10, fill="white", outline="#7B8696", width=1.5, tags=tags)
        c.create_text(x, y, text="?", fill="#4A5568", font=(FONT, 13, "bold"), tags=tags)

class QuestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mapa Quests Free · otPokémon · v1.8")
        self.root.geometry("1380x900")
        self.root.minsize(1020, 700)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.quest_data = self.load_quests()
        self.completed_quests = self.load_progress()
        self.hide_completed = tk.BooleanVar(value=False)
        self.level = tk.IntVar(value=getattr(self, "saved_level", 1))
        self.filter_by_level = tk.BooleanVar(value=getattr(self, "saved_filter_by_level", False))
        self.search = tk.StringVar()
        self.status_filter = tk.StringVar(value="Todas")
        self.region_filter = tk.StringVar(value="Todas")
        self.category_filter = tk.StringVar(value="Todas")
        self.panel_frames = {}
        self._refresh_after_id = None
        self.map_regions = map_regions()
        self._build_styles()
        self._build_layout()
        self._bind_events()
        self.refresh()

    def load_quests(self):
        try:
            with open(resource_path("quests.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("O catálogo precisa ser uma lista de quests.")
            seen = set()
            cleaned = []
            for raw_item in data:
                if not isinstance(raw_item, dict) or not isinstance(raw_item.get("name"), str) or not raw_item["name"].strip():
                    continue
                item = dict(raw_item)
                item["name"] = item["name"].strip()
                normalized_name = item["name"].casefold()
                if normalized_name in seen:
                    continue
                seen.add(normalized_name)
                item.setdefault("category", "Principal")
                item.setdefault("status", "Pendente")
                item.setdefault("region", "Não definida")
                item.setdefault("types", [])
                item.setdefault("abilities_required", [])
                item.setdefault("pokemon_required", [])
                item.setdefault("notes", "Requisitos pendentes de verificação.")
                item.setdefault("reward", "Não informada")
                item.setdefault("url", "https://wiki.otponline.com/Quests")
                # Keep display code resilient if a hand-edited catalog has malformed list fields.
                for list_key in ("types", "abilities_required", "pokemon_required"):
                    if not isinstance(item.get(list_key), list):
                        item[list_key] = []
                    item[list_key] = [str(value) for value in item[list_key] if isinstance(value, (str, int, float))]
                for text_key in ("category", "status", "region", "notes", "reward", "prerequisites", "location_detail", "difficulty", "source_note"):
                    if item.get(text_key) is not None and not isinstance(item.get(text_key), str):
                        item[text_key] = str(item[text_key])
                item["access_verified"] = item.get("access_verified") is True
                cleaned.append(item)
            return cleaned
        except Exception as exc:
            messagebox.showerror("Erro ao carregar catálogo", f"Não foi possível carregar quests.json.\n\n{exc}")
            return []

    def progress_file(self):
        # Keep user progress outside the source folder and PyInstaller temporary directory.
        base = Path.home() / ".mapa_quests_free"
        base.mkdir(parents=True, exist_ok=True)
        return base / "progress.json"

    def load_progress(self):
        # Compatível com o formato antigo (lista de nomes) e o novo formato de perfil.
        self.saved_level = 1
        self.saved_filter_by_level = False
        try:
            path = self.progress_file()
            if not path.exists():
                return set()
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                level = data.get("player_level", 1)
                if isinstance(level, int) and not isinstance(level, bool) and 1 <= level <= 999:
                    self.saved_level = level
                saved_filter = data.get("filter_catalog_by_level", False)
                self.saved_filter_by_level = saved_filter if isinstance(saved_filter, bool) else False
                completed = data.get("completed", [])
            elif isinstance(data, list):
                completed = data
            else:
                return set()
            if not isinstance(completed, list):
                completed = []
            valid_names = {q.get("name") for q in self.quest_data}
            return {name for name in completed if isinstance(name, str) and name in valid_names}
        except (OSError, ValueError, TypeError):
            return set()

    def save_progress(self):
        try:
            current_level = self.level.get() if hasattr(self, "level") else getattr(self, "saved_level", 1)
            filter_by_level = self.filter_by_level.get() if hasattr(self, "filter_by_level") else getattr(self, "saved_filter_by_level", False)
            self.progress_file().write_text(
                json.dumps({"player_level": int(current_level),
                            "filter_catalog_by_level": bool(filter_by_level),
                            "completed": sorted(self.completed_quests)},
                           ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            return True
        except (OSError, ValueError, tk.TclError) as exc:
            messagebox.showerror("Falha ao salvar progresso", f"Não foi possível salvar seu progresso.\n\n{exc}")
            return False

    def toggle_completed(self, name, completed):
        if completed:
            self.completed_quests.add(name)
        else:
            self.completed_quests.discard(name)
        if self.save_progress():
            self.refresh()
            root = getattr(self, "root", None)
            if root is not None and name in getattr(self, "panel_frames", {}):
                root.after_idle(lambda: self._rebuild_panel(name))

    def _build_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=INK,
                        rowheight=30, borderwidth=0, font=(FONT, 9))
        style.configure("Treeview.Heading", background=NAVY, foreground="white",
                        relief="flat", font=(FONT, 8, "bold"), padding=(6, 7))
        style.map("Treeview.Heading", background=[("active", BLUE)], foreground=[("active", "white")])
        style.map("Treeview", background=[("selected", "#FFE89A")], foreground=[("selected", NAVY)])
        style.configure("TCombobox", padding=6, fieldbackground=SIDEBAR_FIELD, background=SIDEBAR_FIELD,
                        foreground="#F4F6FC", arrowcolor=YELLOW, bordercolor=SIDEBAR_FIELD,
                        lightcolor=SIDEBAR_FIELD, darkcolor=SIDEBAR_FIELD, selectbackground=SIDEBAR_FIELD,
                        selectforeground="#F4F6FC")
        style.map("TCombobox", fieldbackground=[("readonly", SIDEBAR_FIELD)],
                  foreground=[("readonly", "#F4F6FC")], selectbackground=[("readonly", SIDEBAR_FIELD)],
                  selectforeground=[("readonly", "#F4F6FC")])
        self.root.option_add("*TCombobox*Listbox.background", SIDEBAR_FIELD)
        self.root.option_add("*TCombobox*Listbox.foreground", "#F4F6FC")
        self.root.option_add("*TCombobox*Listbox.selectBackground", YELLOW)
        self.root.option_add("*TCombobox*Listbox.selectForeground", NAVY)
        style.configure("TNotebook", background=SURFACE, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(10, 7), background=SOFT, foreground=MUTED, font=(FONT, 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#FFE89A")], foreground=[("selected", NAVY)])

    def _build_brand(self):
        """Topo do menu lateral: faixa vermelha de Pokédex com lente azul e três luzes."""
        cv = tk.Canvas(self.sidebar, width=238, height=98, bg=RED, highlightthickness=0, bd=0)
        cv.pack(fill="x")
        cv.create_rectangle(0, 88, 238, 98, fill=RED_DARK, outline="")
        cv.create_line(0, 88, 238, 88, fill="#7A0618", width=2)
        # lente azul grande
        cv.create_oval(14, 12, 78, 76, fill="white", outline=BALL_LINE, width=3)
        cv.create_oval(21, 19, 71, 69, fill=BLUE, outline=BALL_LINE, width=2)
        cv.create_oval(28, 26, 64, 62, fill="#4C9BE0", outline="")
        cv.create_oval(32, 29, 44, 40, fill="#D9EEFF", outline="")
        # três luzes
        for i, color in enumerate(("#FF4D5E", YELLOW, "#46D17F")):
            lx = 96 + i * 20
            cv.create_oval(lx - 6, 12, lx + 6, 24, fill=color, outline=BALL_LINE, width=1.5)
            cv.create_oval(lx - 3.5, 14, lx - 0.5, 17, fill=lighten(color, 0.6), outline="")
        cv.create_text(94, 49, anchor="w", text="QUESTS FREE", fill="white", font=(FONT, 12, "bold"))
        cv.create_text(94, 68, anchor="w", text="otPokémon companion", fill="#FFD3DA", font=(FONT, 8))
        tk.Frame(self.sidebar, bg=YELLOW, height=3).pack(fill="x")

    def _build_layout(self):
        self.shell = tk.Frame(self.root, bg=BG)
        self.shell.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(self.shell, bg=SIDEBAR, width=238)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_brand()

        self._side_label("FILTROS")
        tk.Label(self.sidebar, text="Buscar quest", bg=SIDEBAR, fg="#C9D2EA", font=(FONT, 9)).pack(anchor="w", padx=16, pady=(0, 5))
        self.search_entry = tk.Entry(self.sidebar, textvariable=self.search, bg=SIDEBAR_FIELD, fg="#F4F6FC",
                                     insertbackground="white", relief="flat", font=(FONT, 10))
        self.search_entry.pack(fill="x", padx=14, ipady=7)
        self._side_label("PROGRESSÃO")
        lh = tk.Frame(self.sidebar, bg=SIDEBAR); lh.pack(fill="x", padx=16)
        tk.Label(lh, text="Level do jogador", bg=SIDEBAR, fg="#C9D2EA", font=(FONT, 9)).pack(side="left")
        self.level_entry = tk.Spinbox(lh, from_=1, to=999, width=5, textvariable=self.level,
                                      command=self._on_level_spinbox, relief="flat", bd=0,
                                      bg=SIDEBAR_FIELD, fg="#F4F6FC", buttonbackground=SIDEBAR_FIELD,
                                      insertbackground="white", font=(FONT, 10))
        self.level_entry.pack(side="right", padx=(6, 0))
        self.level_value = tk.Label(lh, text=str(self.level.get()), bg=SIDEBAR, fg=YELLOW, font=(FONT, 10, "bold")); self.level_value.pack(side="right")
        self.level_scale = tk.Scale(self.sidebar, from_=1, to=999, orient="horizontal", variable=self.level,
                                    bg=SIDEBAR, fg="#C9D2EA", troughcolor="#142050", activebackground=YELLOW,
                                    highlightthickness=0, showvalue=False, command=self._on_level)
        self.level_scale.pack(fill="x", padx=12, pady=(3, 0))
        self.level_scale.bind("<ButtonRelease-1>", lambda _event: self.save_progress())
        self.level_entry.bind("<Return>", lambda _event: self._commit_level())
        self.level_entry.bind("<FocusOut>", lambda _event: self._commit_level())
        tk.Label(self.sidebar, text="1                                      999", bg=SIDEBAR, fg="#8D9BC4", font=(FONT, 8)).pack(anchor="w", padx=16)
        tk.Checkbutton(self.sidebar, text="Limitar catálogo ao meu level", variable=self.filter_by_level,
                       command=self._on_level_filter_toggle, bg=SIDEBAR, fg="#DDE3F3",
                       activebackground=SIDEBAR, activeforeground="white", selectcolor=SIDEBAR_FIELD,
                       relief="flat", font=(FONT, 8)).pack(anchor="w", padx=12, pady=(5, 0))
        tk.Label(self.sidebar, text="Desmarcado: mostra todos os níveis.", bg=SIDEBAR, fg="#8D9BC4",
                 font=(FONT, 8)).pack(anchor="w", padx=16, pady=(2, 0))
        self._side_label("STATUS DE ACESSO")
        self.status_combo = ttk.Combobox(self.sidebar, textvariable=self.status_filter, state="readonly",
                                         values=("Todas", "Free confirmado", "Pendente", "Excluída"))
        self.status_combo.pack(fill="x", padx=14)
        self._side_label("REGIÃO")
        self.region_combo = ttk.Combobox(self.sidebar, textvariable=self.region_filter, state="readonly",
                                         values=("Todas", "Kanto", "Johto", "Kalos", "Evento", "Não definida"))
        self.region_combo.pack(fill="x", padx=14)
        tk.Checkbutton(self.sidebar, text="Ocultar quests concluídas", variable=self.hide_completed,
                       command=self.refresh, bg=SIDEBAR, fg="#DDE3F3", activebackground=SIDEBAR,
                       activeforeground="white", selectcolor=SIDEBAR_FIELD, relief="flat",
                       font=(FONT, 8)).pack(anchor="w", padx=12, pady=(10, 0))
        self._side_label("CATEGORIA")
        self.category_combo = ttk.Combobox(self.sidebar, textvariable=self.category_filter, state="readonly",
                                           values=("Todas", "Principal", "Side quest", "Especial / evento"))
        self.category_combo.pack(fill="x", padx=14)
        pill_button(self.sidebar, "↺  Limpar filtros", self.reset_filters, bg=YELLOW, fg=NAVY,
                    hover_bg="#FFD93D", font=(FONT, 9, "bold"), pady=8).pack(fill="x", padx=14, pady=16)
        bottom = tk.Frame(self.sidebar, bg=SIDEBAR); bottom.pack(side="bottom", fill="x", padx=16, pady=15)
        tk.Label(bottom, text="●  CATÁLOGO LOCAL     v" + APP_VERSION, bg=SIDEBAR, fg="#5FD39A", font=(FONT, 8, "bold")).pack(anchor="w")
        tk.Label(bottom, text="Pendentes não são Free confirmadas.\nMapa e marcadores são ilustrativos.",
                 bg=SIDEBAR, fg="#8D9BC4", font=(FONT, 8), justify="left").pack(anchor="w", pady=(7,0))

        # Scrollable main content: avoids lower cards being clipped on smaller screens.
        self.main_canvas = tk.Canvas(self.shell, bg=BG, highlightthickness=0)
        self.main_scroll = ttk.Scrollbar(self.shell, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scroll.set)
        self.main_scroll.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main = tk.Frame(self.main_canvas, bg=BG)
        self.main_window = self.main_canvas.create_window((0,0), window=self.main, anchor="nw")
        self.main.bind("<Configure>", self._on_main_configure)
        self.main_canvas.bind("<Configure>", self._on_canvas_configure)
        self._build_header()
        self._build_stats()
        self._build_progression_card()
        self._build_map_card()
        self._build_catalog_card()
        self._build_workspace()
        self._build_footer()
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.main_canvas.bind_all(seq, self._on_mousewheel)

    def _side_label(self, text):
        tk.Label(self.sidebar, text=text, bg=SIDEBAR, fg=YELLOW, font=(FONT, 8, "bold")).pack(anchor="w", padx=16, pady=(16, 8))

    def _section_title(self, parent, title, subtitle, bg=SURFACE):
        """Título de seção em vermelho Pokédex com mini Poké Ball."""
        box = tk.Frame(parent, bg=bg)
        top = tk.Frame(box, bg=bg); top.pack(anchor="w")
        ball_icon(top, 15, RED, bg).pack(side="left", padx=(0, 6))
        tk.Label(top, text=title, bg=bg, fg=RED, font=(FONT, 8, "bold")).pack(side="left")
        tk.Label(box, text=subtitle, bg=bg, fg=MUTED, font=(FONT, 9)).pack(anchor="w", pady=(3, 0))
        return box

    def _build_header(self):
        top = tk.Frame(self.main, bg=BG); top.pack(fill="x", padx=23, pady=(15, 12))
        tk.Label(top, text="POKÉDEX   /   MAPA DE QUESTS", bg=BG, fg=MUTED, font=(FONT, 9, "bold")).pack(side="left")
        pill_button(top, "Abrir Wiki ↗", lambda: webbrowser.open("https://wiki.otponline.com/Quests"),
                    bg=BLUE, fg="white", hover_bg=darken(BLUE, 0.12), padx=14, pady=6).pack(side="right")
        heading = tk.Frame(self.main, bg=BG); heading.pack(fill="x", padx=23, pady=(0, 14))
        tk.Label(heading, text="Mapa de quests.", bg=BG, fg=NAVY, font=(FONT, 23, "bold")).pack(anchor="w")
        tk.Label(heading, text="Progressão Free, recompensas e requisitos pendentes.", bg=BG, fg=MUTED, font=(FONT, 10)).pack(anchor="w", pady=(4,0))
        bar = tk.Frame(heading, bg=BG); bar.pack(anchor="w", pady=(9, 0))
        for color, width in ((RED, 54), (YELLOW, 28), (BLUE, 14)):
            tk.Frame(bar, bg=color, width=width, height=4).pack(side="left", padx=(0, 3))

    def _build_stats(self):
        row = tk.Frame(self.main, bg=BG); row.pack(fill="x", padx=23, pady=(0, 14))
        self.stat_values = {}
        specs = [("RESULTADOS", "total", BLUE, BLUE), ("FREE CONFIRMADO", "confirmed", GREEN, GREEN_INK),
                 ("PENDENTES", "pending", AMBER, AMBER_INK), ("CONCLUÍDAS · TOTAL", "completed", DONE, DONE_INK),
                 ("EXCLUÍDAS · TOTAL", "excluded", PURPLE, PURPLE_INK)]
        for title, key, color, ink in specs:
            card = tk.Frame(row, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            tk.Frame(card, bg=color, height=5).pack(fill="x")
            head = tk.Frame(card, bg=SURFACE); head.pack(fill="x", padx=11, pady=(9, 0))
            tk.Label(head, text=title, bg=SURFACE, fg=MUTED, font=(FONT, 8, "bold")).pack(side="left")
            ball_icon(head, 22, color, SURFACE).pack(side="right")
            val = tk.Label(card, text="0", bg=SURFACE, fg=ink, font=(FONT, 19, "bold")); val.pack(anchor="w", padx=11, pady=(0,9))
            self.stat_values[key] = val

    def _build_progression_card(self):
        """Show level-relevant quests without disguising unverified access."""
        self.progress_card = tk.Frame(self.main, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        self.progress_card.pack(fill="x", padx=23, pady=(0, 13))
        head = tk.Frame(self.progress_card, bg=SURFACE)
        head.pack(fill="x", padx=15, pady=(12, 4))
        self._section_title(head, "PLANO DE PROGRESSÃO",
                            "Sugestões por faixa de level · acesso não confirmado fica sinalizado").pack(side="left")
        pill_button(head, "Exportar catálogo CSV", self.export_csv, bg=BLUE_LIGHT, fg=NAVY,
                    hover_bg="#D3E4F6", font=(FONT, 8, "bold"), padx=10, pady=5).pack(side="right")
        self.progress_body = tk.Frame(self.progress_card, bg=SURFACE)
        self.progress_body.pack(fill="x", padx=15, pady=(4, 13))
        self._update_progression()

    def _progress_candidates(self):
        level = self.level.get()
        unfinished = [q for q in self.quest_data if q.get("name") not in self.completed_quests]
        # Only individually verified Free quests may be framed as actionable milestones.
        confirmed = [q for q in unfinished if q.get("status") == "Free confirmado"
                     and q.get("access_verified") is True and isinstance(q.get("level"), int)]
        ready = sorted([q for q in confirmed if q["level"] <= level],
                       key=lambda q: (-q["level"], q["name"].casefold()))[:5]
        upcoming = sorted([q for q in confirmed if q["level"] > level],
                          key=lambda q: (q["level"], q["name"].casefold()))[:3]
        # Pending quests are shown only as a research queue, never as recommendations.
        pending = [q for q in unfinished if q.get("status") == "Pendente"
                   and isinstance(q.get("level"), int)]
        near = [q for q in pending if q["level"] <= level and q["level"] >= max(1, level - 50)]
        if not near:
            near = [q for q in pending if q["level"] > level]
        research = sorted(near, key=lambda q: (abs(q["level"] - level), q["level"], q["name"].casefold()))[:5]
        return ready, upcoming, research

    def _update_progression(self):
        if not hasattr(self, "progress_body") or not self.progress_body.winfo_exists():
            return
        for child in self.progress_body.winfo_children(): child.destroy()
        ready, upcoming, research = self._progress_candidates()
        cols = tk.Frame(self.progress_body, bg=SURFACE); cols.pack(fill="x")
        left = tk.Frame(cols, bg=SURFACE); left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(cols, bg=SURFACE); right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(left, text=f"FREE CONFIRMADAS · ATÉ LEVEL {self.level.get()}", bg=SURFACE, fg=NAVY,
                 font=(FONT, 9, "bold")).pack(anchor="w", pady=(0, 6))
        tk.Label(right, text="PRÓXIMOS MARCOS FREE CONFIRMADOS", bg=SURFACE, fg=NAVY,
                 font=(FONT, 9, "bold")).pack(anchor="w", pady=(0, 6))
        self._render_progress_rows(left, ready, empty="Nenhuma quest encontrada nesta rota: não há Free confirmada no catálogo para este level.")
        self._render_progress_rows(right, upcoming, empty="Nenhum próximo marco Free confirmado cadastrado por enquanto.")
        research_box = tk.Frame(self.progress_body, bg=SURFACE)
        research_box.pack(fill="x", pady=(10, 0))
        tk.Label(research_box, text="FILA DE PESQUISA · NÃO SÃO RECOMENDAÇÕES CONFIRMADAS",
                 bg=SURFACE, fg=AMBER_INK, font=(FONT, 9, "bold")).pack(anchor="w", pady=(0, 4))
        self._render_progress_rows(research_box, research,
                                   empty="Nenhuma quest pendente com level conhecido para priorizar agora.")
        tk.Label(self.progress_body,
                 text="Uma quest só entra como marco Free quando status = ‘Free confirmado’ e access_verified = true. A fila de pesquisa contém dados pendentes e precisa de conferência na Wiki.",
                 bg=SURFACE, fg=MUTED, font=(FONT, 8), wraplength=1000, justify="left").pack(anchor="w", pady=(8, 0))

    def _render_progress_rows(self, parent, quests, empty):
        if not quests:
            tk.Label(parent, text=empty, bg=SURFACE, fg=MUTED, font=(FONT, 9),
                     wraplength=430, justify="left").pack(anchor="w", pady=5)
            return
        for q in quests:
            status = q.get("status", "Pendente")
            row = tk.Frame(parent, bg=SOFT, highlightbackground=LINE, highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Frame(row, bg=status_color(status), width=4).pack(side="left", fill="y")
            inner = tk.Frame(row, bg=SOFT); inner.pack(side="left", fill="x", expand=True)
            top = tk.Frame(inner, bg=SOFT); top.pack(fill="x", padx=8, pady=(6, 1))
            tk.Label(top, text=f"LVL {q['level']}  ·  {q['name']}", bg=SOFT, fg=INK,
                     font=(FONT, 9, "bold")).pack(side="left", anchor="w")
            tk.Label(top, text="FREE OK" if q.get("access_verified") else "VALIDAR",
                     bg=status_bg(status), fg=status_ink(status), font=(FONT, 7, "bold"),
                     padx=6, pady=2).pack(side="right")
            tk.Label(inner, text=q.get("reward", "Recompensa não informada"), bg=SOFT, fg=MUTED,
                     font=(FONT, 8), wraplength=420, justify="left").pack(anchor="w", padx=8, pady=(1, 5))
            pill_button(inner, "Abrir ficha →", lambda name=q["name"]: self.open_quest_tab(name),
                        bg=BLUE_LIGHT, fg=NAVY, hover_bg="#D3E4F6", font=(FONT, 8, "bold"),
                        padx=9, pady=3).pack(anchor="e", padx=6, pady=(0, 6))

    def export_csv(self):
        path = filedialog.asksaveasfilename(title="Exportar catálogo de quests", defaultextension=".csv",
                 filetypes=(("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")),
                 initialfile="mapa_quests_catalogo.csv")
        if not path: return
        fields = ["name", "level", "category", "status", "access_verified", "completed_by_player", "difficulty", "region",
                  "location_detail", "types", "pokemon_required", "abilities_required", "prerequisites", "reward", "notes",
                  "url", "source_index", "source_detail", "source_note"]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for q in self.quest_data:
                    row = dict(q)
                    row["completed_by_player"] = q["name"] in self.completed_quests
                    for key in ("types", "pokemon_required", "abilities_required"):
                        row[key] = ", ".join(row.get(key, [])) if isinstance(row.get(key), list) else row.get(key, "")
                    writer.writerow(row)
            messagebox.showinfo("Exportação concluída", f"Catálogo exportado para:\n{path}")
        except OSError as exc:
            messagebox.showerror("Falha na exportação", f"Não foi possível salvar o CSV.\n\n{exc}")

    def _build_map_card(self):
        self.map_card = tk.Frame(self.main, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        self.map_card.pack(fill="x", padx=23, pady=(0, 13))
        header = tk.Frame(self.map_card, bg=SURFACE); header.pack(fill="x", padx=15, pady=(12, 8))
        self._section_title(header, "MAPA DE EXPLORAÇÃO",
                            "Selecione uma Poké Ball para abrir a ficha · clique numa ilha para filtrar a região").pack(side="left")
        pill_button(header, "Abrir mapa 3D ↗", self.open_3d_map, bg=RED, fg="white",
                    hover_bg=RED_DARK, padx=12, pady=6).pack(side="right", padx=(8, 0))
        self.map_canvas = tk.Canvas(self.map_card, height=330, bg=SEA, highlightthickness=0)
        self.map_canvas.pack(fill="x", expand=False, padx=9, pady=(0, 8))
        self.map_canvas.bind("<Configure>", lambda _e: self._update_map())
        tk.Label(self.map_card, text="MAPA CONCEITUAL · MARCADORES SEM COORDENADAS OFICIAIS", bg=SURFACE,
                 fg=MUTED, font=(FONT, 8, "bold")).pack(anchor="w", padx=15, pady=(0, 10))

    def open_3d_map(self):
        """Abre o visualizador 3D em processo separado, sem bloquear a interface Tk."""
        try:
            import importlib.util
            if importlib.util.find_spec("webview") is None:
                messagebox.showinfo(
                    "Mapa 3D",
                    "O visualizador 3D usa pywebview + Three.js.\n\n"
                    "No terminal do VS Code execute:\n"
                    "python -m pip install pywebview\n\n"
                    "A renderização precisa de internet para carregar Three.js. "
                    "O app principal continua funcionando sem essa dependência."
                )
                return
            catalog = resource_path("quests.json")
            if not catalog.exists() or (not getattr(sys, "frozen", False) and not resource_path("mapa_3d_launcher.py").exists()):
                messagebox.showerror("Mapa 3D", "Arquivos do visualizador não encontrados. Reextraia o pacote completo.")
                return
            # Reentra neste mesmo programa com --mapa-3d (no EXE congelado, sys.executable já é o app).
            cmd = [sys.executable] + ([] if getattr(sys, "frozen", False) else [str(Path(__file__).resolve())]) + ["--mapa-3d", str(catalog)]
            subprocess.Popen(
                cmd,
                cwd=str(resource_path(".").resolve()),
                close_fds=True
            )
        except Exception as exc:
            messagebox.showerror(
                "Mapa 3D",
                f"Não foi possível iniciar o visualizador:\n{exc}\n\n"
                "Confira a instalação do pywebview e do WebView2 Runtime no Windows."
            )

    def _build_catalog_card(self):
        card = tk.Frame(self.main, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        card.pack(fill="x", padx=23, pady=(0, 13))
        head = tk.Frame(card, bg=SURFACE); head.pack(fill="x", padx=15, pady=(11, 6))
        self._section_title(head, "CATÁLOGO DE QUESTS", "Duplo clique em uma quest para abrir a ficha").pack(anchor="w")
        wrap = tk.Frame(card, bg=SURFACE); wrap.pack(fill="x")
        columns = ("level", "name", "category", "reward", "region", "status")
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", selectmode="browse", height=10)
        specs = [("level","LVL",48),("name","QUEST",165),("category","CATEGORIA",115),("reward","RECOMPENSA",260),("region","REGIÃO",90),("status","STATUS",140)]
        for col, title, width in specs:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, minwidth=45, anchor="w", stretch=(col=="reward"))
        # Zebra + cor do texto por status (o ● do STATUS herda a cor da linha).
        self.tree.tag_configure("odd", background=SURFACE)
        self.tree.tag_configure("even", background="#FBF6E6")
        for tag, color in [("confirmed", GREEN_INK), ("pending", AMBER_INK), ("excluded", PURPLE_INK), ("done", DONE_INK)]:
            self.tree.tag_configure(tag, foreground=color)
        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="x", expand=True, padx=(9,0), pady=(0,9))
        yscroll.pack(side="right", fill="y", padx=(0,9), pady=(0,9))
        self.tree.bind("<Double-1>", self._on_tree_double)
        self.catalog_empty = tk.Label(card, text="Nenhuma quest encontrada nesta rota.\nAjuste os filtros ou use ↺ Limpar filtros para voltar ao mapa completo.",
                                      bg=SURFACE, fg=MUTED, font=(FONT, 10), justify="center", pady=14)

    def _empty_workspace_frame(self):
        frame = tk.Frame(self.notebook, bg=SOFT)
        tk.Label(frame, text="Nenhuma ficha aberta ainda.\nEscolha uma Poké Ball no mapa ou dê duplo clique no catálogo.",
                 bg=SOFT, fg=MUTED, font=(FONT, 9), padx=12, pady=13, justify="center").pack()
        return frame

    def _build_workspace(self):
        self.workspace_card = tk.Frame(self.main, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        self.workspace_card.pack(fill="x", padx=23, pady=(0, 13))
        top = tk.Frame(self.workspace_card, bg=SURFACE); top.pack(fill="x", padx=15, pady=10)
        self._section_title(top, "FICHAS ABERTAS", "Sua Pokédex de quests em andamento").pack(side="left")
        pill_button(top, "Fechar todas ×", self.close_all_tabs, bg=SOFT, fg=MUTED, hover_bg="#F1EAD3",
                    font=(FONT, 8, "bold"), padx=10, pady=5).pack(side="right")
        self.notebook = ttk.Notebook(self.workspace_card); self.notebook.pack(fill="x", padx=9, pady=(0,9))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.empty_workspace = self._empty_workspace_frame()
        self.notebook.add(self.empty_workspace, text="Início")

    def _build_footer(self):
        foot = tk.Frame(self.main, bg=BG); foot.pack(fill="x", padx=23, pady=(0, 12))
        tk.Label(foot, text="MAPA QUESTS FREE · PROJETO COMUNITÁRIO NÃO OFICIAL", bg=BG, fg=MUTED, font=(FONT, 8)).pack(side="left")
        tk.Label(foot, text="Dados sujeitos a revisão", bg=BG, fg=MUTED, font=(FONT, 8)).pack(side="right")

    def _bind_events(self):
        for var in (self.search, self.status_filter, self.region_filter, self.category_filter):
            var.trace_add("write", lambda *_: self.schedule_refresh())

    def schedule_refresh(self):
        # Debounce: agrupa mudanças rápidas (digitação, slider) em um único refresh.
        if self._refresh_after_id:
            try: self.root.after_cancel(self._refresh_after_id)
            except tk.TclError: pass
        self._refresh_after_id = self.root.after(120, self._run_scheduled_refresh)

    def _run_scheduled_refresh(self):
        self._refresh_after_id = None
        self.refresh()

    def _on_main_configure(self, _event=None):
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.main_canvas.itemconfigure(self.main_window, width=event.width)

    def _on_mousewheel(self, event):
        # Only scroll when the pointer is over the main canvas; avoid hijacking sidebar scrolling.
        try:
            x, y = self.root.winfo_pointerxy()
            widget = self.root.winfo_containing(x, y)
            while widget is not None:
                if widget == self.main_canvas or widget == self.main:
                    num = getattr(event, "num", None)
                    delta = getattr(event, "delta", 0) or 0
                    if num in (4, 5): step = -1 if num == 4 else 1
                    elif abs(delta) >= 120: step = int(-delta / 120)
                    else: step = -1 if delta > 0 else 1 if delta < 0 else 0
                    self.main_canvas.yview_scroll(step, "units")
                    break
                widget = getattr(widget, "master", None)
        except tk.TclError:
            pass

    def _on_level(self, value):
        try:
            current = max(1, min(999, int(float(value))))
            self.level_value.config(text=str(current))
            self.schedule_refresh()
        except (ValueError, tk.TclError):
            pass

    def _on_level_spinbox(self):
        self._commit_level()

    def _on_level_filter_toggle(self):
        self.refresh()
        self.save_progress()

    def _commit_level(self):
        try:
            current = max(1, min(999, int(self.level.get())))
        except (ValueError, tk.TclError):
            current = 1
        self.level.set(current)
        self.level_value.config(text=str(current))
        self.refresh()
        self.save_progress()

    def _filtered(self):
        term = self.search.get().strip().casefold()
        status = self.status_filter.get()
        region = self.region_filter.get()
        category = self.category_filter.get()
        result = []
        for q in self.quest_data:
            level = q.get("level")
            # The catalog shows every level by default. Level-based narrowing is explicit opt-in.
            if self.filter_by_level.get() and isinstance(level, int) and not isinstance(level, bool) and level > self.level.get():
                continue
            searchable = [q.get("name", ""), q.get("reward", ""), q.get("region", ""),
                          q.get("notes", ""), q.get("category", ""), q.get("prerequisites", ""),
                          q.get("location_detail", ""), q.get("source_note", "")]
            for key in ("types", "pokemon_required", "abilities_required"):
                value = q.get(key, [])
                searchable.extend(value if isinstance(value, list) else [str(value)])
            text = " ".join(str(part) for part in searchable if part is not None).casefold()
            if term and term not in text:
                continue
            if self.hide_completed.get() and q.get("name") in self.completed_quests:
                continue
            qstatus = q.get("status", "Pendente")
            # Premium quests are excluded from the default Free workflow. They remain available
            # only when the user explicitly selects the "Excluída" audit filter.
            if status == "Todas" and qstatus.startswith("Excluída"):
                continue
            if status == "Free confirmado" and qstatus != "Free confirmado":
                continue
            if status == "Pendente" and qstatus != "Pendente":
                continue
            if status == "Excluída" and not qstatus.startswith("Excluída"):
                continue
            if region != "Todas" and q.get("region") != region:
                continue
            if category != "Todas" and q.get("category") != category:
                continue
            result.append(q)
        return sorted(result, key=lambda q: (q.get("level") is None, q.get("level") or 0, q.get("name","").casefold()))

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        filtered = self._filtered()
        self.tree.delete(*self.tree.get_children())
        for i, q in enumerate(filtered):
            status = q.get("status","Pendente")
            done = q.get("name") in self.completed_quests
            tag = "confirmed" if status.startswith("Free confirmado") else "excluded" if status.startswith("Excluída") else "pending"
            if done:
                tag = "done"
            mark = "✓" if done else "●"
            self.tree.insert("", "end", iid=q["name"], values=(q.get("level") if q.get("level") is not None else "—",
                              q["name"], q.get("category","Principal"), q.get("reward",""), q.get("region","—"),
                              f"{mark} {status}"), tags=(tag, "even" if i % 2 else "odd"))
        if hasattr(self, "catalog_empty"):
            if filtered:
                self.catalog_empty.pack_forget()
            else:
                self.catalog_empty.pack(fill="x")
        self.stat_values["total"].config(text=str(len(filtered)))
        self.stat_values["confirmed"].config(text=str(sum(q.get("status")=="Free confirmado" for q in filtered)))
        self.stat_values["pending"].config(text=str(sum(q.get("status")=="Pendente" for q in filtered)))
        self.stat_values["completed"].config(text=str(sum(q.get("name") in self.completed_quests for q in self.quest_data)))
        self.stat_values["excluded"].config(text=str(sum(q.get("status","").startswith("Excluída") for q in self.quest_data)))
        self._update_progression()
        self._update_map()

    def _toggle_region(self, region):
        self.region_filter.set("Todas" if self.region_filter.get() == region else region)

    def _show_tip(self, q, x, y, w, h):
        c = self.map_canvas; c.delete("tip")
        reward = q.get("reward", "") or ""
        reward = reward if len(reward) <= 40 else reward[:39] + "…"
        lvl = q.get("level") if q.get("level") is not None else "—"
        t = c.create_text(x + 14, y + 14, anchor="nw", text=f"{q['name']} · LVL {lvl}\n{reward}", fill="white",
                          font=(FONT, 8, "bold"), tags="tip")
        x1, y1, x2, y2 = c.bbox(t)
        dx = -(x2 - x1) - 28 if x2 + 8 > w else 0
        dy = -(y2 - y1) - 28 if y2 + 8 > h else 0
        c.move(t, dx, dy)
        x1, y1, x2, y2 = c.bbox(t)
        r = round_rect(c, x1 - 7, y1 - 4, x2 + 7, y2 + 4, r=6, fill=NAVY, outline=YELLOW, width=2, tags="tip")
        c.tag_lower(r, t)

    # ---- mapa 2D -------------------------------------------------------------------------
    @staticmethod
    def _scaled_outline(info, scale, w, h):
        cx, cy = info["cx"], info["cy"]
        pts = []
        for px, py in info["outline"]:
            pts.extend([(cx + (px - cx) * scale) / 100 * w, (cy + (py - cy) * scale) / 100 * h])
        return pts

    @staticmethod
    def _inside(poly, x, y):
        inside = False
        n = len(poly) // 2
        j = n - 1
        for i in range(n):
            xi, yi, xj, yj = poly[2 * i], poly[2 * i + 1], poly[2 * j], poly[2 * j + 1]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
                inside = not inside
            j = i
        return inside

    # (meia-largura, altura acima, altura abaixo) da área ocupada por cada marco
    LANDMARK_BOX = {"Kanto": (12, 11, 10), "Johto": (11, 18, 11), "Kalos": (7, 18, 12),
                    "Evento": (10, 16, 11), "Não definida": (11, 11, 11)}

    def _landmark_spot(self, info, region, w, h, markers, avoid, min_gap=19):
        """Escolhe, na borda da ilha, o ponto mais distante dos marcadores e do rótulo."""
        hw, up, down = self.LANDMARK_BOX.get(region, (11, 12, 11))
        poly = self._scaled_outline(info, 0.97, w, h)
        best, best_score = None, -1.0
        for f in (0.97, 0.9, 0.82, 0.7):
            for k in range(48):
                ang = 2 * math.pi * k / 48
                x = (info["cx"] + info["rx"] * f * math.cos(ang)) / 100 * w
                y = (info["cy"] + info["ry"] * f * math.sin(ang)) / 100 * h
                if x < hw + 6 or x > w - hw - 6 or y < up + 6 or y > h - down - 34:
                    continue
                if not all(self._inside(poly, x + dx, y + dy)
                           for dx, dy in ((-hw, -up), (hw, -up), (-hw, down), (hw, down))):
                    continue
                if any(bx1 - hw <= x <= bx2 + hw and by1 - down <= y <= by2 + up for bx1, by1, bx2, by2 in avoid):
                    continue
                score = min([math.hypot(x - mx, y - my) for mx, my in markers] or [999.0])
                if f >= 0.9:
                    score += 4          # prefere pontos na borda da ilha
                if score > best_score:
                    best, best_score = (x, y), score
        return best if best_score >= min_gap else None

    def _draw_marker(self, c, x, y, r, tag, color, done, locked, selected, is_open):
        if selected:
            c.create_oval(x - r - 7, y - r - 7, x + r + 7, y + r + 7, fill="", outline=NAVY, width=1.5, tags=tag)
            c.create_oval(x - r - 5, y - r - 5, x + r + 5, y + r + 5, fill="", outline=YELLOW, width=3, tags=tag)
        elif is_open:
            c.create_oval(x - r - 4, y - r - 4, x + r + 4, y + r + 4, fill="", outline=YELLOW, width=2, tags=tag)
        if done:
            draw_pokeball(c, x, y, r, DONE, tags=tag)
            draw_check(c, x, y, r, tags=tag)
        elif locked:
            draw_pokeball(c, x, y, r, "#FFFFFF", line=color, line_w=2, tags=tag, lock=r >= 7)
        else:
            draw_pokeball(c, x, y, r, color, tags=tag)

    def _update_map(self):
        if not hasattr(self, "map_canvas") or not self.map_canvas.winfo_exists():
            return
        c = self.map_canvas; c.delete("all")
        w = max(c.winfo_width(), 500); h = max(c.winfo_height(), 180)
        # Mar turquesa com marcas de onda.
        rng = random.Random(7)
        for _ in range(58):
            wx = rng.uniform(0.02, 0.98) * w; wy = rng.uniform(0.04, 0.96) * h
            c.create_line(wx - 9, wy, wx - 4.5, wy - 3, wx, wy, wx + 4.5, wy + 3, wx + 9, wy,
                          smooth=True, fill=WAVE, width=2, capstyle="round")
        filtered = self._filtered()
        counts = {}
        for q in filtered: counts[q.get("region")] = counts.get(q.get("region"), 0) + 1
        # Águas rasas + faixa de areia.
        for region, info in self.map_regions.items():
            c.create_polygon(*self._scaled_outline(info, 1.15, w, h), fill=FOAM, outline="", smooth=True)
        for region, info in self.map_regions.items():
            c.create_polygon(*self._scaled_outline(info, 1.06, w, h), fill=SAND, outline=SAND_EDGE, width=1, smooth=True)
        # Posições (px) de todos os marcadores por região, para posicionar os marcos sem colidir.
        marker_px = {}
        for q in self.quest_data:
            reg = q.get("region") if q.get("region") in self.map_regions else "Não definida"
            marker_px.setdefault(reg, []).append((max(12, min(w - 12, q.get("x", 50) / 100 * w)),
                                                  max(12, min(h - 12, q.get("y", 50) / 100 * h))))
        active_region = getattr(self, "region_filter", None)
        active_region = active_region.get() if active_region is not None else "Todas"
        for index, (region, info) in enumerate(self.map_regions.items()):
            rtag = f"region{index}"
            cx = info["cx"]
            fill, edge = LAND_COLORS.get(region, LAND_COLORS["Não definida"])
            opts = {"dash": (5, 3)} if region == "Não definida" else {}
            c.create_polygon(*self._scaled_outline(info, 1.0, w, h), fill=fill, outline=edge, width=2,
                             smooth=True, tags=rtag, **opts)
            # Rótulo em forma de placa (pill + poste).
            top = min(py for _px, py in info["outline"]) / 100 * h
            lx = max(60, min(w - 60, cx / 100 * w)); ly = max(30, top - 1)
            selected_region = active_region == region
            t = c.create_text(lx, ly - 14, anchor="center", text=f"{info['label']} · {counts.get(region, 0)}",
                              fill=NAVY, font=(FONT, 9, "bold"), tags=rtag)
            x1, y1, x2, y2 = c.bbox(t)
            c.create_line(lx, y2 + 2, lx, ly + 3, fill=NAVY, width=2, tags=rtag)
            pill = round_rect(c, x1 - 9, y1 - 3, x2 + 9, y2 + 3, r=9, fill=YELLOW if selected_region else CREAM,
                              outline=RED if selected_region else NAVY, width=2, tags=rtag)
            c.tag_lower(pill, t)
            spot = self._landmark_spot(info, region, w, h, marker_px.get(region, []), [(x1 - 9, y1 - 3, x2 + 9, ly + 3)])
            if spot:
                draw_landmark(c, region, spot[0], spot[1], tags=rtag)
            c.tag_bind(rtag, "<Button-1>", lambda _e, r=region: self._toggle_region(r))
            c.tag_bind(rtag, "<Enter>", lambda _e: c.config(cursor="hand2"))
            c.tag_bind(rtag, "<Leave>", lambda _e: c.config(cursor=""))
        selected = self._selected_quest_name()
        opened = set(getattr(self, "panel_frames", None) or ())
        for idx, q in enumerate(filtered):
            x = max(12, min(w-12, q.get("x",50)/100*w)); y = max(12, min(h-12, q.get("y",50)/100*h))
            status = q.get("status","Pendente"); color = status_color(status); r = 8
            level = q.get("level")
            locked = isinstance(level, int) and not isinstance(level, bool) and level > self.level.get()
            done = q.get("name") in self.completed_quests
            # Todas as partes da Poké Ball compartilham uma tag única: o clique/hover é ligado a ela
            # (e não à tag dinâmica "current", que pertenceria a qualquer marcador sob o ponteiro).
            tag = f"quest{idx}"
            self._draw_marker(c, x, y, r, tag, color, done, locked, q.get("name") == selected, q.get("name") in opened)
            c.tag_bind(tag, "<Button-1>", lambda _e, name=q["name"]: self.open_quest_tab(name))
            c.tag_bind(tag, "<Enter>", lambda _e, q=q, x=x, y=y: (c.config(cursor="hand2"), self._show_tip(q, x, y, w, h)))
            c.tag_bind(tag, "<Leave>", lambda _e: (c.config(cursor=""), c.delete("tip")))
        if not filtered:
            t = c.create_text(w / 2, h / 2 - 8, text="Nenhuma quest encontrada nesta rota.", fill=NAVY, font=(FONT, 12, "bold"))
            t2 = c.create_text(w / 2, h / 2 + 12, text="Ajuste os filtros ou use ↺ Limpar filtros.", fill=TEXT, font=(FONT, 9))
            x1, y1, x2, y2 = c.bbox(t); x3, y3, x4, y4 = c.bbox(t2)
            box = round_rect(c, min(x1, x3) - 16, y1 - 10, max(x2, x4) + 16, y4 + 10, r=12, fill=CREAM, outline=NAVY, width=2)
            c.tag_lower(box, t)
        c.create_text(w-12,h-10,text="MARCADORES ILUSTRATIVOS",anchor="se",fill="#2F6E86",font=(FONT,7,"bold"))
        # Legenda com mini Poké Balls.
        lx = 18; ly = h - 16
        legend = [("Free", "ball", GREEN), ("Pendente", "ball", AMBER), ("Premium", "ball", PURPLE),
                  ("Concluída", "done", DONE), ("Acima do level", "locked", MUTED)]
        items = []
        for text, kind, color in legend:
            if kind == "done":
                items += draw_pokeball(c, lx, ly, 6, DONE, tags="legend")
                items.append(draw_check(c, lx, ly, 6, tags="legend"))
            elif kind == "locked":
                items += draw_pokeball(c, lx, ly, 6, "#FFFFFF", line=color, line_w=1.8, tags="legend")
            else:
                items += draw_pokeball(c, lx, ly, 6, color, tags="legend")
            t = c.create_text(lx + 11, ly, anchor="w", text=text, fill=NAVY, font=(FONT, 8, "bold"), tags="legend")
            items.append(t); lx = c.bbox(t)[2] + 16
        bg = round_rect(c, 8, h - 30, lx - 6, h - 3, r=10, fill=CREAM, outline=NAVY, width=1.5)
        c.tag_lower(bg, items[0])

    def _on_tree_double(self, _event=None):
        selected = self.tree.selection()
        if selected: self.open_quest_tab(selected[0])

    def _dex_number(self, name):
        """Número estilo Pokédex: posição da quest na ordem de level (1 = primeira)."""
        ordered = sorted(self.quest_data, key=lambda q: (q.get("level") is None, q.get("level") or 0, q.get("name", "").casefold()))
        for i, q in enumerate(ordered, 1):
            if q.get("name") == name:
                return i
        return 0

    def open_quest_tab(self, name):
        q = next((item for item in self.quest_data if item.get("name") == name), None)
        if not q: return
        existing = self.panel_frames.get(name)
        if existing and existing.winfo_exists():
            self.notebook.select(existing); return
        if self.empty_workspace.winfo_exists():
            try: self.notebook.forget(self.empty_workspace); self.empty_workspace.destroy()
            except tk.TclError: pass
        frame = tk.Frame(self.notebook, bg=SURFACE)
        self.panel_frames[name] = frame
        # Tkinter's Notebook has no native per-tab close buttons; explicit close action is always visible inside each tab.
        self.notebook.add(frame, text=name)
        self.notebook.select(frame)
        self._populate_panel(frame, q)

    def _rebuild_panel(self, name):
        """Redesenha a ficha aberta (ex.: depois de marcar como concluída)."""
        frame = self.panel_frames.get(name)
        q = next((item for item in self.quest_data if item.get("name") == name), None)
        if frame is None or q is None:
            return
        try:
            if not frame.winfo_exists():
                return
            for child in frame.winfo_children():
                child.destroy()
            self._populate_panel(frame, q)
        except tk.TclError:
            pass

    def _populate_panel(self, frame, q):
        name = q["name"]
        done = name in self.completed_quests
        body = tk.Frame(frame, bg=SURFACE); body.pack(fill="both", expand=True, padx=12, pady=10)
        status = q.get("status","Pendente")
        # Faixa de cabeçalho na cor do status, com Poké Ball, nº estilo Pokédex e selo de captura.
        sc = DONE if done else status_color(status)
        fg = NAVY if luminance(sc) > 0.2 else "white"
        strip = tk.Frame(body, bg=sc); strip.pack(fill="x", pady=(0, 10))
        icon = tk.Canvas(strip, width=54, height=54, bg=sc, highlightthickness=0, bd=0)
        icon.pack(side="left", padx=(12, 10), pady=8)
        icon.create_oval(2, 2, 52, 52, fill="white", outline=darken(sc, 0.25), width=2)
        draw_pokeball(icon, 27, 27, 20, sc, line_w=1.8)
        texts = tk.Frame(strip, bg=sc); texts.pack(side="left", pady=8)
        tk.Label(texts, text=f"#{self._dex_number(name):03d}   ●  {status.upper()}", bg=sc, fg=fg,
                 font=(FONT, 8, "bold")).pack(anchor="w")
        tk.Label(texts, text=name, bg=sc, fg=fg, font=(FONT, 15, "bold"), wraplength=620, justify="left").pack(anchor="w", pady=(2, 0))
        if done:
            tk.Label(strip, text="Capturada ✓", bg="white", fg=DONE_INK, font=(FONT, 9, "bold"),
                     padx=12, pady=5).pack(side="right", padx=14)
        facts = tk.Frame(body, bg=SOFT, highlightbackground=LINE, highlightthickness=1); facts.pack(fill="x", pady=10)
        fact_items = (("LEVEL", str(q.get("level") if q.get("level") is not None else "Não informado")),
                      ("REGIÃO", q.get("region","—")), ("CATEGORIA", q.get("category","Principal")),
                      ("TIPOS", ", ".join(q.get("types", [])) or "Não informados"))
        for label, value in fact_items:
            cell = tk.Frame(facts, bg=SOFT); cell.pack(side="left", fill="x", expand=True, padx=8, pady=8)
            tk.Label(cell, text=label, bg=SOFT, fg=RED, font=(FONT, 8, "bold")).pack(anchor="w")
            tk.Label(cell, text=value, bg=SOFT, fg=INK, font=(FONT, 9), wraplength=180).pack(anchor="w", pady=(4,0))
        self._detail_block(body, "RECOMPENSA PRINCIPAL", q.get("reward","Não informada"))
        self._detail_block(body, "POKÉMON NECESSÁRIOS", ", ".join(q.get("pokemon_required", [])) or "Não verificados")
        self._detail_block(body, "HABILIDADES NECESSÁRIAS", ", ".join(q.get("abilities_required", [])) or "Não verificadas")
        self._detail_block(body, "DIFICULDADE", q.get("difficulty", "Não verificada"))
        self._detail_block(body, "PRÉ-REQUISITOS", q.get("prerequisites", "Não verificados"))
        self._detail_block(body, "LOCALIZAÇÃO", q.get("location_detail", "Não verificada individualmente"))
        self._detail_block(body, "NOTAS DE VALIDAÇÃO", q.get("notes","Ainda não verificadas"))
        completed_var = tk.BooleanVar(value=done)
        tk.Checkbutton(body, text="Já concluí esta quest", variable=completed_var,
                       command=lambda n=name, v=completed_var: self.toggle_completed(n, v.get()),
                       bg=SURFACE, fg=GREEN_INK, activebackground=SURFACE, activeforeground=GREEN_INK,
                       selectcolor=GREEN_LIGHT, font=(FONT, 9, "bold")).pack(anchor="w", pady=(2, 8))
        tk.Label(body, text="Seu progresso fica salvo neste computador e não altera a validação Free/Premium.",
                 bg=SURFACE, fg=MUTED, font=(FONT, 8), wraplength=900,
                 justify="left").pack(anchor="w", pady=(0, 5))
        self._detail_block(body, "FONTE", "Índice geral da Wiki: " + q.get("source_index", "https://wiki.otponline.com/Quests") + "\nPágina individual: " + q.get("source_detail", q.get("url", "")))
        actions = tk.Frame(body, bg=SURFACE); actions.pack(fill="x", pady=(6, 0))
        pill_button(actions, "Abrir página da Wiki ↗", lambda url=q.get("url","https://wiki.otponline.com/Quests"): webbrowser.open(url),
                    bg=BLUE, fg="white", hover_bg=darken(BLUE, 0.12), padx=12, pady=7).pack(side="left")
        pill_button(actions, "Fechar esta aba ×", lambda n=name: self.close_tab(n),
                    bg=SOFT, fg=MUTED, hover_bg="#F1EAD3", padx=12, pady=7).pack(side="right")

    def _detail_block(self, parent, title, text):
        block = tk.Frame(parent, bg=SURFACE); block.pack(fill="x", pady=(4, 7))
        tk.Label(block, text=title, bg=SURFACE, fg=RED, font=(FONT, 8, "bold")).pack(anchor="w")
        tk.Label(block, text=text, bg=SURFACE, fg=TEXT, font=(FONT, 9),
                 justify="left", anchor="w", wraplength=900).pack(fill="x", anchor="w", pady=(4,0))

    def _on_tab_changed(self, _event=None):
        self._update_map()

    def _selected_quest_name(self):
        try:
            current = self.notebook.select()
        except (tk.TclError, AttributeError):
            return None
        return next((n for n, f in self.panel_frames.items() if str(f) == str(current)), None)

    def close_tab(self, name):
        frame = self.panel_frames.pop(name, None)
        if frame is None: return
        try: self.notebook.forget(frame); frame.destroy()
        except tk.TclError: pass
        if not self.panel_frames and not self.notebook.tabs():
            self.empty_workspace = self._empty_workspace_frame()
            self.notebook.add(self.empty_workspace, text="Início")

    def close_all_tabs(self):
        for name in list(self.panel_frames.keys()): self.close_tab(name)

    def reset_filters(self):
        # Limpar filtros não altera o perfil nem o level salvo do jogador.
        self.search.set("")
        self.status_filter.set("Todas"); self.region_filter.set("Todas"); self.category_filter.set("Todas")
        self.refresh()

    def on_close(self):
        # Persist profile and progress, then stop the Tk event loop by destroying the root.
        self.save_progress()
        if self._refresh_after_id:
            try: self.root.after_cancel(self._refresh_after_id)
            except tk.TclError: pass
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try: self.main_canvas.unbind_all(seq)
            except tk.TclError: pass
        self.panel_frames.clear()
        self.root.destroy()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--mapa-3d":
        from mapa_3d_launcher import main as run_3d
        run_3d(sys.argv[2:])
        return
    root = tk.Tk()
    QuestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
