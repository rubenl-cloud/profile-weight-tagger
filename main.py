"""
SOCIAREM – P1 Vulnerabilidad Económica Estructural
Proof of Concept · Piloto Messina

10 individuos sintéticos · validación experto · optimización de pesos (scipy)

Indicadores disponibles en Messina para P1:
  Primarios : I1 (ISEE €/mes), I2 (bajo umbral pobreza, binario)
  Secundarios: I3 (carga energética %), I4 (impago, binario),
               I11 (ayudas, binario), I12 (microcrédito, binario)

Ejecutar: python p1_poc.py
"""

import tkinter as tk
from tkinter import ttk
import math

# ─── Paleta ──────────────────────────────────────────────────────────────────
C = {
    "bg":        "#0F1117",
    "card":      "#1A1D27",
    "card2":     "#21253A",
    "border":    "#2A2E45",
    "accent":    "#4F8EF7",
    "accent2":   "#7C5FD4",
    "text":      "#E8EAF0",
    "muted":     "#7A7F9A",
    "ok":        "#3DD68C",
    "warn":      "#F5A623",
    "danger":    "#E05C5C",
    "ok_dim":    "#1A3D2B",
    "warn_dim":  "#3A2C10",
    "danger_dim":"#3A1A1A",
    "badge_pri": "#1C2E54",
    "badge_pri_fg": "#4F8EF7",
    "badge_sec": "#221C3A",
    "badge_sec_fg": "#A78BFA",
    "sel":       "#1E2A4A",
}

# ─── 10 hogares sintéticos Messina ───────────────────────────────────────────
# Campos: id, nombre, edad, composición, descripción breve
# I1: ISEE mensual €  (umbral pobreza: ~780 €/mes = 9.360 €/año)
# I2: 1 = bajo umbral pobreza relativa (60% mediana italiana ~1.050 €/mes equiv.)
# I3: carga energética %  (alto riesgo > 10%)
# I4: 1 = impago/corte en últimos 12 meses
# I11: 1 = recibe ayudas sociales/energéticas
# I12: 1 = acceso a microcrédito/apoyo comunitario
# ground_truth: etiqueta "real" de vulnerabilidad P1 para calcular pesos

HOUSEHOLDS = [
    {
        "id": "HOG-01", "nombre": "Rosa M.", "edad": 67,
        "composicion": "Pensionista, vive sola",
        "desc": "Pensionista mínima. Piso de alquiler antiguo. Concentrador O₂ nocturno.",
        "I1": 530, "I2": 1, "I3": 18.2, "I4": 1, "I11": 1, "I12": 0,
        "ground_truth": 1,
    },
    {
        "id": "HOG-02", "nombre": "Antonio e Grazia B.", "edad": 72,
        "composicion": "Pareja jubilados",
        "desc": "Dos pensiones mínimas combinadas. Sin deudas energéticas. Reciben bonus gas.",
        "I1": 820, "I2": 1, "I3": 11.4, "I4": 0, "I11": 1, "I12": 0,
        "ground_truth": 1,
    },
    {
        "id": "HOG-03", "nombre": "Fatima O.", "edad": 34,
        "composicion": "Madre sola, 2 hijos menores",
        "desc": "Trabajo informal, ingresos irregulares. Corte de luz hace 8 meses.",
        "I1": 490, "I2": 1, "I3": 22.7, "I4": 1, "I11": 0, "I12": 1,
        "ground_truth": 1,
    },
    {
        "id": "HOG-04", "nombre": "Marco e Lucia F.", "edad": 45,
        "composicion": "Pareja, 1 hijo",
        "desc": "Desempleo reciente. ISEE actualizado. Sin cortes aún pero deuda acumulada.",
        "I1": 710, "I2": 1, "I3": 14.8, "I4": 0, "I11": 0, "I12": 0,
        "ground_truth": 1,
    },
    {
        "id": "HOG-05", "nombre": "Salvatore C.", "edad": 58,
        "composicion": "Solo, trabajador precario",
        "desc": "Ingresos bajos pero estables. Gasto energético moderado. Sin ayudas formales.",
        "I1": 850, "I2": 0, "I3": 8.9, "I4": 0, "I11": 0, "I12": 0,
        "ground_truth": 0,
    },
    {
        "id": "HOG-06", "nombre": "Concetta e figli", "edad": 39,
        "composicion": "Madre sola, 3 hijos",
        "desc": "Renta de ciudadanía (RdC) activa. Alta carga energética por piso deficiente.",
        "I1": 640, "I2": 1, "I3": 19.5, "I4": 1, "I11": 1, "I12": 1,
        "ground_truth": 1,
    },
    {
        "id": "HOG-07", "nombre": "Giuseppe N.", "edad": 29,
        "composicion": "Solo, empleado",
        "desc": "Contrato fijo desde este año. ISEE algo bajo pero situación estabilizándose.",
        "I1": 940, "I2": 0, "I3": 7.2, "I4": 0, "I11": 0, "I12": 0,
        "ground_truth": 0,
    },
    {
        "id": "HOG-08", "nombre": "Carmela V.", "edad": 81,
        "composicion": "Anciana sola, tutela de la Fundación",
        "desc": "Pensión social mínima. Deuda histórica con comercializadora. Sin microcrédito.",
        "I1": 460, "I2": 1, "I3": 24.1, "I4": 1, "I11": 1, "I12": 0,
        "ground_truth": 1,
    },
    {
        "id": "HOG-09", "nombre": "Emanuele e Sandra R.", "edad": 51,
        "composicion": "Pareja, hijos mayores independientes",
        "desc": "Ambos con trabajo a tiempo parcial. ISEE limítrofe. Situación estable.",
        "I1": 1050, "I2": 0, "I3": 9.1, "I4": 0, "I11": 0, "I12": 0,
        "ground_truth": 0,
    },
    {
        "id": "HOG-10", "nombre": "Nadia T.", "edad": 44,
        "composicion": "Sola, desempleada larga duración",
        "desc": "ISEE bajo, sin ayudas formales. Sin cortes pero riesgo latente alto.",
        "I1": 580, "I2": 1, "I3": 16.3, "I4": 0, "I11": 0, "I12": 1,
        "ground_truth": 1,
    },
]

# Pesos iniciales (igual para todos) — serán optimizados
INIT_WEIGHTS = {"I1": 0.30, "I2": 0.25, "I3": 0.20, "I4": 0.10, "I11": 0.10, "I12": 0.05}

# Umbrales de normalización
THRESHOLDS = {
    "I1":  {"low": 780, "mid": 1050},   # €/mes
    "I3":  {"warn": 10, "high": 20},    # %
}


def normalize_score(hh, weights):
    """Score 0-1 de vulnerabilidad P1 dado un hogar y pesos."""
    # I1: cuanto más bajo, más vulnerable; normalizar 0-1 (0=1200€, 1=400€)
    i1_norm = max(0, min(1, (1200 - hh["I1"]) / 800))
    # I2, I4, I11 (ausencia de ayuda), I12 (ausencia de microcrédito)
    i2_norm = float(hh["I2"])
    i3_norm = max(0, min(1, (hh["I3"] - 5) / 25))   # 5%-30%
    i4_norm = float(hh["I4"])
    i11_norm = float(hh["I11"])   # tener ayuda = ya reconocido como vulnerable
    i12_norm = 1.0 - float(hh["I12"])  # sin microcrédito = más vulnerable

    vals = {"I1": i1_norm, "I2": i2_norm, "I3": i3_norm,
            "I4": i4_norm, "I11": i11_norm, "I12": i12_norm}
    total_w = sum(weights.values())
    score = sum(weights[k] * vals[k] for k in weights) / total_w
    return score


def optimize_weights(expert_labels):
    """
    Dada la etiqueta experto (dict id→0/1), optimiza pesos para maximizar
    separación de score entre vulnerables y no vulnerables (logistic loss).
    Devuelve dict de pesos optimizados.
    """
    try:
        from scipy.optimize import minimize
        import numpy as np
    except ImportError:
        return INIT_WEIGHTS.copy()

    keys = list(INIT_WEIGHTS.keys())
    n = len(keys)

    def loss(w_arr):
        w = {k: max(0.001, w_arr[i]) for i, k in enumerate(keys)}
        total = 0
        for hh in HOUSEHOLDS:
            label = expert_labels.get(hh["id"], hh["ground_truth"])
            score = normalize_score(hh, w)
            score = max(1e-7, min(1 - 1e-7, score))
            total -= label * math.log(score) + (1 - label) * math.log(1 - score)
        return total

    w0 = np.array([INIT_WEIGHTS[k] for k in keys])
    bounds = [(0.001, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: sum(w) - 1.0}]
    res = minimize(loss, w0, method="SLSQP", bounds=bounds, constraints=constraints,
                   options={"maxiter": 500, "ftol": 1e-9})
    if res.success:
        return {k: float(max(0.001, res.x[i])) for i, k in enumerate(keys)}
    return INIT_WEIGHTS.copy()


# ─── App ─────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOCIAREM · P1 Vulnerabilidad Económica Estructural · Messina")
        self.geometry("1100x760")
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        self.current_idx = 0
        self.expert_labels = {}   # id → 0/1
        self.weights = INIT_WEIGHTS.copy()
        self.opt_weights = None

        self._build()
        self._render_household()

    # ── Construcción UI ───────────────────────────────────────────────────────
    def _build(self):
        # ── Sidebar (lista individuos) ────────────────────────────────────────
        self.sidebar = tk.Frame(self, bg=C["card"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="SOCIAREM", font=("Helvetica Neue", 11, "bold"),
                 bg=C["card"], fg=C["accent"]).pack(anchor="w", padx=16, pady=(18, 0))
        tk.Label(self.sidebar, text="Piloto Messina · P1",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(0, 12))

        sep = tk.Frame(self.sidebar, bg=C["border"], height=1)
        sep.pack(fill="x", padx=0, pady=(0, 8))

        tk.Label(self.sidebar, text="Hogares", font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(0, 6))

        self.sidebar_btns = []
        for i, hh in enumerate(HOUSEHOLDS):
            btn = tk.Button(
                self.sidebar,
                text=f"{hh['id']}  {hh['nombre']}",
                font=("Helvetica Neue", 10),
                anchor="w", padx=12, pady=6,
                relief="flat", cursor="hand2",
                bg=C["card"], fg=C["text"],
                activebackground=C["sel"],
                activeforeground=C["text"],
                command=lambda idx=i: self._select(idx)
            )
            btn.pack(fill="x", padx=4)
            self.sidebar_btns.append(btn)

        sep2 = tk.Frame(self.sidebar, bg=C["border"], height=1)
        sep2.pack(fill="x", pady=8)

        self.opt_btn = tk.Button(
            self.sidebar, text="⚡  Optimizar pesos",
            font=("Helvetica Neue", 10, "bold"),
            bg=C["accent2"], fg=C["text"],
            relief="flat", cursor="hand2",
            padx=12, pady=7,
            command=self._run_optimization
        )
        self.opt_btn.pack(fill="x", padx=8, pady=(0, 6))

        self.progress_lbl = tk.Label(self.sidebar, text="",
                                     font=("Helvetica Neue", 9),
                                     bg=C["card"], fg=C["muted"], wraplength=190)
        self.progress_lbl.pack(anchor="w", padx=12)

        # ── Main area ─────────────────────────────────────────────────────────
        self.main = tk.Frame(self, bg=C["bg"])
        self.main.pack(side="left", fill="both", expand=True)

        # Header individuo
        self.header_frame = tk.Frame(self.main, bg=C["card"], height=90)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)

        self.lbl_id     = tk.Label(self.header_frame, text="", font=("Helvetica Neue", 10),
                                   bg=C["card"], fg=C["muted"])
        self.lbl_nombre = tk.Label(self.header_frame, text="", font=("Helvetica Neue", 17, "bold"),
                                   bg=C["card"], fg=C["text"])
        self.lbl_comp   = tk.Label(self.header_frame, text="", font=("Helvetica Neue", 11),
                                   bg=C["card"], fg=C["muted"])
        self.lbl_desc   = tk.Label(self.header_frame, text="", font=("Helvetica Neue", 10),
                                   bg=C["card"], fg=C["muted"], wraplength=700, justify="left")
        self.lbl_id.place(x=24, y=12)
        self.lbl_nombre.place(x=24, y=28)
        self.lbl_comp.place(x=24, y=54)
        self.lbl_desc.place(x=24, y=70)

        # Nav
        nav = tk.Frame(self.header_frame, bg=C["card"])
        nav.place(relx=1.0, x=-16, y=28, anchor="ne")
        tk.Button(nav, text="←", font=("Helvetica Neue", 14), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2", padx=6,
                  command=lambda: self._select((self.current_idx - 1) % 10)).pack(side="left")
        self.lbl_nav = tk.Label(nav, text="", font=("Helvetica Neue", 10),
                                bg=C["card"], fg=C["muted"])
        self.lbl_nav.pack(side="left", padx=4)
        tk.Button(nav, text="→", font=("Helvetica Neue", 14), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2", padx=6,
                  command=lambda: self._select((self.current_idx + 1) % 10)).pack(side="left")

        sep3 = tk.Frame(self.main, bg=C["border"], height=1)
        sep3.pack(fill="x")

        # Scroll
        canvas = tk.Canvas(self.main, bg=C["bg"], highlightthickness=0)
        vsb = tk.Scrollbar(self.main, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(canvas, bg=C["bg"])
        self._canvas_win = canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda e: (
            canvas.configure(scrollregion=canvas.bbox("all")),
            canvas.itemconfig(self._canvas_win, width=canvas.winfo_width())
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self._canvas_win, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    # ── Render hogar ─────────────────────────────────────────────────────────
    def _select(self, idx):
        self.current_idx = idx
        for i, btn in enumerate(self.sidebar_btns):
            btn.configure(bg=C["sel"] if i == idx else C["card"])
        self._render_household()

    def _render_household(self):
        hh = HOUSEHOLDS[self.current_idx]

        # Header
        self.lbl_id.configure(text=hh["id"])
        self.lbl_nombre.configure(text=f"{hh['nombre']}  ·  {hh['edad']} años")
        self.lbl_comp.configure(text=hh["composicion"])
        self.lbl_desc.configure(text=hh["desc"])
        self.lbl_nav.configure(text=f"{self.current_idx+1}/10")

        # Limpiar content
        for w in self.content.winfo_children():
            w.destroy()

        pad = {"padx": 20}

        # ── Score actual ──────────────────────────────────────────────────────
        score = normalize_score(hh, self.weights)
        score_pct = int(score * 100)
        if score_pct >= 65:
            score_color, score_dim, score_label = C["danger"], C["danger_dim"], "ALTA"
        elif score_pct >= 40:
            score_color, score_dim, score_label = C["warn"], C["warn_dim"], "MEDIA"
        else:
            score_color, score_dim, score_label = C["ok"], C["ok_dim"], "BAJA"

        score_card = tk.Frame(self.content, bg=score_dim,
                              highlightbackground=score_color, highlightthickness=1)
        score_card.pack(fill="x", padx=20, pady=(18, 8))
        sc_inner = tk.Frame(score_card, bg=score_dim)
        sc_inner.pack(fill="x", padx=16, pady=12)

        tk.Label(sc_inner, text="SCORE P1 · VULNERABILIDAD ECONÓMICA",
                 font=("Helvetica Neue", 9, "bold"), bg=score_dim,
                 fg=score_color).pack(anchor="w")
        row_s = tk.Frame(sc_inner, bg=score_dim)
        row_s.pack(fill="x", pady=(4, 0))
        tk.Label(row_s, text=f"{score_pct}%", font=("Helvetica Neue", 36, "bold"),
                 bg=score_dim, fg=score_color).pack(side="left")
        tk.Label(row_s, text=f" {score_label}", font=("Helvetica Neue", 20, "bold"),
                 bg=score_dim, fg=score_color).pack(side="left", padx=(6, 0))

        # Barra de score
        bar_frame = tk.Frame(sc_inner, bg=C["border"], height=6)
        bar_frame.pack(fill="x", pady=(8, 0))
        bar_fill = tk.Frame(bar_frame, bg=score_color, height=6)
        bar_fill.place(x=0, y=0, relwidth=min(1.0, score))

        # Pesos usados (mini)
        w_txt = "  ".join([f"{k}: {v:.2f}" for k, v in self.weights.items()])
        w_label = "pesos optimizados" if self.opt_weights else "pesos iniciales"
        tk.Label(sc_inner, text=f"({w_label})  {w_txt}",
                 font=("Helvetica Neue", 9), bg=score_dim, fg=score_color).pack(anchor="w", pady=(4, 0))

        # ── Indicadores ───────────────────────────────────────────────────────
        tk.Label(self.content, text="Indicadores",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", **pad, pady=(14, 4))

        grid_frame = tk.Frame(self.content, bg=C["bg"])
        grid_frame.pack(fill="x", **pad)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(2, weight=1)

        indicators = [
            ("I1", "Renta neta equiv.", "primario",
             f"{hh['I1']} €/mes",
             "< 780 €/mes → riesgo",
             hh["I1"] < 780, "DS2 · ISEE"),
            ("I2", "Bajo umbral pobreza", "primario",
             "SÍ" if hh["I2"] else "NO",
             "60% mediana nacional",
             bool(hh["I2"]), "DS2 · ISEE"),
            ("I3", "Carga energética", "secundario",
             f"{hh['I3']:.1f}%",
             "> 10% → alto riesgo",
             hh["I3"] > 10, "DS4 · DS14 · facturas"),
            ("I4", "Impago / corte suministro", "secundario",
             "SÍ" if hh["I4"] else "NO",
             "En últimos 12 meses",
             bool(hh["I4"]), "DS8 · autodeclaración"),
            ("I11", "Recibe ayudas sociales", "secundario",
             "SÍ" if hh["I11"] else "NO",
             "Bonus energía / RdC",
             bool(hh["I11"]), "DS8 · Fundación Messina"),
            ("I12", "Acceso a microcrédito", "secundario",
             "SÍ" if hh["I12"] else "NO",
             "Apoyo financiero comunit.",
             bool(hh["I12"]), "DS7 · DS27 · ONG"),
        ]

        for idx_i, (iid, name, role, value, note, is_risk, source) in enumerate(indicators):
            col = idx_i % 3
            row = idx_i // 3
            self._ind_card(grid_frame, iid, name, role, value, note, is_risk, source, row, col)

        # ── Validación experto ────────────────────────────────────────────────
        tk.Label(self.content, text="Validación experto",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", **pad, pady=(18, 4))

        val_card = tk.Frame(self.content, bg=C["card"],
                            highlightbackground=C["border"], highlightthickness=1)
        val_card.pack(fill="x", **pad, pady=(0, 4))
        vc = tk.Frame(val_card, bg=C["card"])
        vc.pack(fill="x", padx=16, pady=12)

        tk.Label(vc, text="¿Este hogar presenta vulnerabilidad P1 · económica estructural?",
                 font=("Helvetica Neue", 11), bg=C["card"], fg=C["text"]).pack(anchor="w")
        tk.Label(vc, text="La etiqueta experto se usará para optimizar los pesos del modelo.",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", pady=(2, 8))

        btn_row = tk.Frame(vc, bg=C["card"])
        btn_row.pack(anchor="w")

        current_label = self.expert_labels.get(hh["id"], None)

        for val, label, bg_active, fg_active in [
            (1, "SÍ – vulnerable P1", C["danger_dim"], C["danger"]),
            (0, "NO – no vulnerable", C["ok_dim"], C["ok"]),
        ]:
            is_active = current_label == val
            btn = tk.Button(
                btn_row, text=label,
                font=("Helvetica Neue", 11, "bold" if is_active else "normal"),
                bg=bg_active if is_active else C["card2"],
                fg=fg_active if is_active else C["muted"],
                highlightbackground=fg_active if is_active else C["border"],
                highlightthickness=2 if is_active else 1,
                relief="flat", cursor="hand2", padx=18, pady=8,
                command=lambda v=val, hid=hh["id"]: self._set_expert(hid, v)
            )
            btn.pack(side="left", padx=(0, 10))

        # Estado etiquetas
        n_labeled = len(self.expert_labels)
        status_txt = f"{n_labeled}/10 hogares etiquetados"
        if n_labeled == 10:
            status_txt += "  ·  ¡Listo para optimizar pesos!"
            status_col = C["ok"]
        else:
            status_col = C["muted"]
        tk.Label(vc, text=status_txt, font=("Helvetica Neue", 9),
                 bg=C["card"], fg=status_col).pack(anchor="w", pady=(8, 0))

        # ── Panel pesos (si existe optimización) ─────────────────────────────
        if self.opt_weights:
            self._render_weights_panel()

    def _ind_card(self, parent, iid, name, role, value, note, is_risk, source, row, col):
        is_primary = role == "primario"
        risk_color = C["danger"] if is_risk else C["ok"]
        risk_dim = C["danger_dim"] if is_risk else C["ok_dim"]
        badge_bg = C["badge_pri"] if is_primary else C["badge_sec"]
        badge_fg = C["badge_pri_fg"] if is_primary else C["badge_sec_fg"]

        frame = tk.Frame(parent, bg=C["card"],
                         highlightbackground=risk_color if is_risk else C["border"],
                         highlightthickness=1)
        frame.grid(row=row, column=col, padx=(0, 8) if col < 2 else 0, pady=(0, 8), sticky="nsew")

        inner = tk.Frame(frame, bg=C["card"])
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Cabecera: ID + badge
        top = tk.Frame(inner, bg=C["card"])
        top.pack(fill="x")
        tk.Label(top, text=iid, font=("Helvetica Neue", 9, "bold"),
                 bg=badge_bg, fg=badge_fg, padx=6, pady=2).pack(side="left")
        role_lbl = "PRIMARIO" if is_primary else "SECUNDARIO"
        tk.Label(top, text=role_lbl, font=("Helvetica Neue", 8),
                 bg=C["card"], fg=badge_fg).pack(side="left", padx=(6, 0))

        # Nombre
        tk.Label(inner, text=name, font=("Helvetica Neue", 10, "bold"),
                 bg=C["card"], fg=C["text"], anchor="w").pack(fill="x", pady=(4, 0))

        # Valor grande
        tk.Label(inner, text=value, font=("Helvetica Neue", 22, "bold"),
                 bg=C["card"], fg=risk_color, anchor="w").pack(fill="x", pady=(2, 0))

        # Nota umbral
        tk.Label(inner, text=note, font=("Helvetica Neue", 9),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")

        # Separador
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(6, 4))

        # Fuente
        tk.Label(inner, text=source, font=("Helvetica Neue", 8),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")

    def _set_expert(self, hid, val):
        self.expert_labels[hid] = val
        n = len(self.expert_labels)
        self.progress_lbl.configure(
            text=f"{n}/10 hogares etiquetados" + ("\n¡Listo!" if n == 10 else "")
        )
        self._render_household()

    def _run_optimization(self):
        if len(self.expert_labels) < 5:
            self.progress_lbl.configure(
                text="Necesitas ≥ 5 hogares etiquetados para optimizar.",
                fg=C["warn"]
            )
            return

        self.progress_lbl.configure(text="Optimizando…", fg=C["accent"])
        self.update()

        # Completar etiquetas faltantes con ground_truth
        full_labels = {hh["id"]: self.expert_labels.get(hh["id"], hh["ground_truth"])
                       for hh in HOUSEHOLDS}
        opt = optimize_weights(full_labels)
        self.opt_weights = opt
        self.weights = opt

        self.progress_lbl.configure(
            text="✓ Pesos optimizados\nRecargando vistas…",
            fg=C["ok"]
        )
        self.update()
        self._render_household()

    def _render_weights_panel(self):
        tk.Label(self.content, text="Pesos optimizados por el modelo",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=20, pady=(18, 4))

        wcard = tk.Frame(self.content, bg=C["card"],
                         highlightbackground=C["accent2"], highlightthickness=1)
        wcard.pack(fill="x", padx=20, pady=(0, 12))
        wc = tk.Frame(wcard, bg=C["card"])
        wc.pack(fill="x", padx=16, pady=14)

        tk.Label(wc,
                 text="Pesos calculados via SLSQP (scipy) minimizando log-loss sobre las etiquetas experto.",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", pady=(0, 10))

        ind_names = {
            "I1": "I1 – Renta neta equivalente",
            "I2": "I2 – Bajo umbral pobreza",
            "I3": "I3 – Carga energética",
            "I4": "I4 – Impago / corte",
            "I11": "I11 – Recibe ayudas",
            "I12": "I12 – Acceso microcrédito",
        }
        max_w = max(self.opt_weights.values())

        for k, w in sorted(self.opt_weights.items(), key=lambda x: -x[1]):
            row = tk.Frame(wc, bg=C["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=ind_names[k], font=("Helvetica Neue", 10),
                     bg=C["card"], fg=C["text"], width=30, anchor="w").pack(side="left")
            # barra
            bar_bg = tk.Frame(row, bg=C["border"], height=14, width=200)
            bar_bg.pack(side="left", padx=(8, 0))
            bar_fill = tk.Frame(bar_bg, bg=C["accent2"], height=14)
            bar_fill.place(x=0, y=0, width=int(200 * w / max_w))
            tk.Label(row, text=f"{w:.3f}", font=("Helvetica Neue", 10, "bold"),
                     bg=C["card"], fg=C["accent2"], width=6).pack(side="left", padx=(8, 0))
            init_w = INIT_WEIGHTS[k]
            delta = w - init_w
            delta_txt = f"{'↑' if delta > 0 else '↓'} {abs(delta):.3f}"
            delta_col = C["ok"] if delta > 0 else C["danger"]
            tk.Label(row, text=delta_txt, font=("Helvetica Neue", 9),
                     bg=C["card"], fg=delta_col).pack(side="left", padx=(6, 0))

        # Tabla resumen: score antes vs después por hogar
        tk.Label(wc, text="Scores por hogar · pesos iniciales vs optimizados",
                 font=("Helvetica Neue", 10, "bold"),
                 bg=C["card"], fg=C["text"]).pack(anchor="w", pady=(14, 4))

        for hh in HOUSEHOLDS:
            s_init = normalize_score(hh, INIT_WEIGHTS)
            s_opt = normalize_score(hh, self.opt_weights)
            label = self.expert_labels.get(hh["id"], hh["ground_truth"])
            label_txt = "vulnerable" if label == 1 else "no vulnerable"
            label_col = C["danger"] if label == 1 else C["ok"]

            hrow = tk.Frame(wc, bg=C["card2"],
                            highlightbackground=C["border"], highlightthickness=1)
            hrow.pack(fill="x", pady=2)
            hr = tk.Frame(hrow, bg=C["card2"])
            hr.pack(fill="x", padx=10, pady=5)

            tk.Label(hr, text=hh["id"], font=("Helvetica Neue", 9, "bold"),
                     bg=C["card2"], fg=C["muted"], width=8).pack(side="left")
            tk.Label(hr, text=hh["nombre"], font=("Helvetica Neue", 10),
                     bg=C["card2"], fg=C["text"], width=22, anchor="w").pack(side="left")
            tk.Label(hr, text=label_txt, font=("Helvetica Neue", 9),
                     bg=C["card2"], fg=label_col, width=12).pack(side="left")
            tk.Label(hr, text=f"inicial: {s_init:.2f}", font=("Helvetica Neue", 9),
                     bg=C["card2"], fg=C["muted"], width=12).pack(side="left")

            opt_col = (C["ok"] if (label == 1 and s_opt >= 0.5) or
                                  (label == 0 and s_opt < 0.5) else C["danger"])
            tk.Label(hr, text=f"opt: {s_opt:.2f}", font=("Helvetica Neue", 10, "bold"),
                     bg=C["card2"], fg=opt_col, width=10).pack(side="left")
            correct = ((label == 1 and s_opt >= 0.5) or (label == 0 and s_opt < 0.5))
            tk.Label(hr, text="✓" if correct else "✗",
                     font=("Helvetica Neue", 12, "bold"),
                     bg=C["card2"], fg=C["ok"] if correct else C["danger"]).pack(side="left", padx=(6, 0))


if __name__ == "__main__":
    app = App()
    app.mainloop()