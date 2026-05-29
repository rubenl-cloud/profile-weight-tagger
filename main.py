"""
SOCIAREM – P1 Structural Economic Vulnerability
Expert Assessment PoC (Proof of Concept)

Data sources available in Messina for P1:
  PRIMARY indicators:
    I1 (renta neta mensual equivalente) → DS2 (ISEE)
    I2 (hogar bajo umbral pobreza relativa) → DS2 (ISEE)
  SECONDARY indicators (disponibles en Messina):
    I3 (carga energética) → DS4 (factura electricidad), DS14 (factura gas)
    I4 (impago/corte suministro) → DS8 (autodeclaración)
    I11 (acceso a ayudas sociales/energéticas) → DS8 (autodeclaración)
    I12 (acceso a microcrédito/apoyo comunitario) → DS7 (registros ONG), DS27, DS8

Usage:
    pip install tkinter  (normalmente viene con Python)
    python p1_vulnerability_poc.py
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import json
from datetime import datetime


# ─── Datos de los indicadores para P1 ───────────────────────────────────────

INDICATORS = [
    {
        "id": "I1",
        "label": "I1 – Renta neta mensual equivalente",
        "role": "primary",
        "category": "A. Economía / Renta",
        "data_source": "DS2 – ISEE (Indicatore della Situazione Economica Equivalente)",
        "description": (
            "Renta neta mensual del hogar ajustada por tamaño y composición "
            "mediante escala de equivalencia (escala OCDE modificada / ISEE)."
        ),
        "field_label": "Valor ISEE mensual (€/mes)",
        "field_type": "numeric",
        "threshold_note": "Umbral orientativo: ISEE < 9.360 €/año (~780 €/mes) → riesgo alto",
        "threshold_value": 780.0,
        "threshold_direction": "below",
        "unit": "€/mes",
    },
    {
        "id": "I2",
        "label": "I2 – Hogar bajo umbral de pobreza relativa",
        "role": "primary",
        "category": "A. Economía / Renta",
        "data_source": "DS2 – ISEE",
        "description": (
            "Hogar clasificado con renta equivalente inferior al 60 % de la mediana "
            "nacional equivalente (metodología EU-SILC)."
        ),
        "field_label": "¿Renta < 60 % mediana nacional?",
        "field_type": "binary",
        "threshold_note": "Dato derivado directamente del ISEE: sí/no según cálculo automático.",
        "threshold_value": None,
        "threshold_direction": None,
        "unit": None,
    },
    {
        "id": "I3",
        "label": "I3 – Carga energética del hogar",
        "role": "secondary",
        "category": "B. Carga energética / Capacidad de pago",
        "data_source": "DS4 – Factura electricidad · DS14 – Factura gas",
        "description": (
            "Cociente entre el gasto energético total del hogar (electricidad + gas) "
            "y la renta neta mensual equivalente. "
            "Alta carga: > 10 % renta (criterio LIHC adaptado)."
        ),
        "field_label": "Gasto energético total mensual (€/mes)",
        "field_type": "numeric",
        "threshold_note": "Carga energética = gasto / renta. Alto si > 10 % de I1.",
        "threshold_value": None,
        "threshold_direction": None,
        "unit": "€/mes",
    },
    {
        "id": "I4",
        "label": "I4 – Impago o corte de suministro energético",
        "role": "secondary",
        "category": "B. Carga energética / Capacidad de pago",
        "data_source": "DS8 – Autodeclaración estructurada (Fundación Messina)",
        "description": (
            "Existencia documentada de impagos, deudas con la comercializadora "
            "o cortes de suministro en los últimos 12 meses."
        ),
        "field_label": "¿Ha habido impago o corte en los últimos 12 meses?",
        "field_type": "binary",
        "threshold_note": "Dato de autodeclaración verificada. Alto valor diagnóstico.",
        "threshold_value": None,
        "threshold_direction": None,
        "unit": None,
    },
    {
        "id": "I11",
        "label": "I11 – Acceso a ayudas sociales o energéticas",
        "role": "secondary",
        "category": "E. Acceso a asistencia y servicios",
        "data_source": "DS8 – Autodeclaración (Fundación Messina)",
        "description": (
            "Registro de si el hogar recibe o ha recibido ayudas públicas de energía "
            "(bonus energia, tarifa social) o ayudas sociales formales."
        ),
        "field_label": "¿Recibe ayudas sociales o energéticas actualmente?",
        "field_type": "binary",
        "threshold_note": (
            "Distingue vulnerabilidad reconocida administrativamente "
            "de vulnerabilidad real no reconocida."
        ),
        "threshold_value": None,
        "threshold_direction": None,
        "unit": None,
    },
    {
        "id": "I12",
        "label": "I12 – Acceso a microcrédito o apoyo financiero comunitario",
        "role": "secondary",
        "category": "E. Acceso a asistencia y servicios",
        "data_source": "DS7 – Registros ONG/Fundación · DS27 – Programas microcrédito · DS8 – Autodeclaración",
        "description": (
            "Acceso efectivo a microcrédito ético, fondos de emergencia comunitarios "
            "u otros mecanismos de apoyo financiero no bancario."
        ),
        "field_label": "¿Tiene acceso a microcrédito o apoyo financiero comunitario?",
        "field_type": "binary",
        "threshold_note": "Indicador de resiliencia económica. Ausencia refuerza severidad.",
        "threshold_value": None,
        "threshold_direction": None,
        "unit": None,
    },
]

# ─── Colores ─────────────────────────────────────────────────────────────────

COLORS = {
    "bg": "#F8F7F4",
    "bg_card": "#FFFFFF",
    "bg_primary_badge": "#EEF4FD",
    "bg_secondary_badge": "#F1EFE8",
    "text_main": "#1A1A18",
    "text_secondary": "#5F5E5A",
    "text_primary_badge": "#185FA5",
    "text_secondary_badge": "#5F5E5A",
    "border": "#D3D1C7",
    "border_accent_primary": "#378ADD",
    "border_accent_secondary": "#888780",
    "yes_bg": "#EAF3DE",
    "yes_fg": "#3B6D11",
    "no_bg": "#FCEBEB",
    "no_fg": "#A32D2D",
    "na_bg": "#F1EFE8",
    "na_fg": "#5F5E5A",
    "active_btn": "#185FA5",
    "active_btn_fg": "#FFFFFF",
    "inactive_btn": "#FFFFFF",
    "inactive_btn_fg": "#444441",
    "header_bg": "#FFFFFF",
    "header_border": "#D3D1C7",
    "result_activated": "#EAF3DE",
    "result_activated_border": "#3B6D11",
    "result_not_activated": "#F1EFE8",
    "result_not_activated_border": "#888780",
    "result_uncertain": "#FAEEDA",
    "result_uncertain_border": "#BA7517",
}


class P1VulnerabilityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOCIAREM – P1 Vulnerabilidad Económica Estructural")
        self.geometry("960x820")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        # Estado
        self.household_id = tk.StringVar(value="HOG-001")
        self.responses = {}   # id → {"value": ..., "yn": "y"/"n"/"?"}
        self.numeric_vars = {}
        self.yn_vars = {}

        self._setup_fonts()
        self._build_ui()

    def _setup_fonts(self):
        self.f_title = tkfont.Font(family="Helvetica Neue", size=15, weight="bold")
        self.f_header = tkfont.Font(family="Helvetica Neue", size=12, weight="bold")
        self.f_label = tkfont.Font(family="Helvetica Neue", size=11)
        self.f_label_bold = tkfont.Font(family="Helvetica Neue", size=11, weight="bold")
        self.f_small = tkfont.Font(family="Helvetica Neue", size=10)
        self.f_mono = tkfont.Font(family="Courier", size=10)
        self.f_badge = tkfont.Font(family="Helvetica Neue", size=9, weight="bold")
        self.f_result = tkfont.Font(family="Helvetica Neue", size=13, weight="bold")

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["header_bg"],
                          highlightbackground=COLORS["header_border"],
                          highlightthickness=1)
        header.pack(fill="x", side="top")

        tk.Label(header, text="SOCIAREM · Piloto Messina",
                 font=self.f_small, bg=COLORS["header_bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", padx=20, pady=(12, 0))

        tk.Label(header, text="P1 – Vulnerabilidad Económica Estructural",
                 font=self.f_title, bg=COLORS["header_bg"],
                 fg=COLORS["text_main"]).pack(anchor="w", padx=20, pady=(2, 4))

        hid_frame = tk.Frame(header, bg=COLORS["header_bg"])
        hid_frame.pack(anchor="w", padx=20, pady=(0, 12))
        tk.Label(hid_frame, text="ID de hogar:", font=self.f_small,
                 bg=COLORS["header_bg"], fg=COLORS["text_secondary"]).pack(side="left")
        tk.Entry(hid_frame, textvariable=self.household_id, font=self.f_mono,
                 width=14, relief="solid", bd=1,
                 bg=COLORS["bg_card"], fg=COLORS["text_main"]).pack(side="left", padx=(6, 0))

        # ── Scroll area ──────────────────────────────────────────────────────
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=COLORS["bg"])

        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.bind_all("<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>",
            lambda e: canvas.yview_scroll(1, "units"))

        # ── Separador primarios / secundarios ───────────────────────────────
        self._section_header(self.scroll_frame, "Indicadores primarios",
                             "Necesarios para activar el perfil P1 (fuente: ISEE / DS2)",
                             COLORS["text_primary_badge"])

        for ind in INDICATORS:
            if ind["role"] == "primary":
                self._build_indicator_card(self.scroll_frame, ind)

        self._section_header(self.scroll_frame, "Indicadores secundarios",
                             "Disponibles en Messina · gradan severidad del perfil",
                             COLORS["text_secondary"])

        for ind in INDICATORS:
            if ind["role"] == "secondary":
                self._build_indicator_card(self.scroll_frame, ind)

        # ── Footer con botones ───────────────────────────────────────────────
        footer = tk.Frame(self, bg=COLORS["header_bg"],
                          highlightbackground=COLORS["header_border"],
                          highlightthickness=1)
        footer.pack(fill="x", side="bottom")

        btn_frame = tk.Frame(footer, bg=COLORS["header_bg"])
        btn_frame.pack(anchor="e", padx=20, pady=10)

        tk.Button(btn_frame, text="Limpiar todo",
                  font=self.f_label, fg=COLORS["text_secondary"],
                  bg=COLORS["bg"], relief="solid", bd=1, cursor="hand2",
                  padx=14, pady=6,
                  command=self._clear_all).pack(side="left", padx=(0, 8))

        tk.Button(btn_frame, text="Calcular resultado →",
                  font=self.f_label_bold, fg=COLORS["active_btn_fg"],
                  bg=COLORS["active_btn"], relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=6,
                  command=self._compute_result).pack(side="left")

    def _section_header(self, parent, title, subtitle, color):
        f = tk.Frame(parent, bg=COLORS["bg"])
        f.pack(fill="x", padx=20, pady=(18, 4))
        tk.Label(f, text=title, font=self.f_header, bg=COLORS["bg"],
                 fg=color).pack(anchor="w")
        tk.Label(f, text=subtitle, font=self.f_small, bg=COLORS["bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w")
        tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x", padx=20)

    def _build_indicator_card(self, parent, ind):
        is_primary = ind["role"] == "primary"
        border_color = COLORS["border_accent_primary"] if is_primary else COLORS["border"]

        outer = tk.Frame(parent, bg=COLORS["bg"])
        outer.pack(fill="x", padx=20, pady=6)

        card = tk.Frame(outer, bg=COLORS["bg_card"],
                        highlightbackground=border_color,
                        highlightthickness=1 if is_primary else 1,
                        relief="flat")
        card.pack(fill="x")

        # ── Título + badge ───────────────────────────────────────────────────
        top = tk.Frame(card, bg=COLORS["bg_card"])
        top.pack(fill="x", padx=14, pady=(10, 0))

        badge_bg = COLORS["bg_primary_badge"] if is_primary else COLORS["bg_secondary_badge"]
        badge_fg = COLORS["text_primary_badge"] if is_primary else COLORS["text_secondary_badge"]
        badge_text = "PRIMARIO" if is_primary else "SECUNDARIO"

        tk.Label(top, text=badge_text, font=self.f_badge,
                 bg=badge_bg, fg=badge_fg,
                 padx=6, pady=2, relief="flat").pack(side="left", anchor="w")

        tk.Label(top, text=ind["label"], font=self.f_label_bold,
                 bg=COLORS["bg_card"], fg=COLORS["text_main"],
                 wraplength=680, justify="left").pack(side="left", padx=(8, 0))

        # ── Fuente de datos ──────────────────────────────────────────────────
        tk.Label(card, text=f"Fuente: {ind['data_source']}", font=self.f_small,
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 anchor="w").pack(fill="x", padx=14, pady=(2, 0))

        # ── Descripción ──────────────────────────────────────────────────────
        tk.Label(card, text=ind["description"], font=self.f_small,
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 wraplength=880, justify="left", anchor="w").pack(fill="x", padx=14, pady=(4, 0))

        # ── Nota umbral ──────────────────────────────────────────────────────
        tk.Label(card, text=f"⚑ {ind['threshold_note']}", font=self.f_small,
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 wraplength=880, justify="left", anchor="w").pack(fill="x", padx=14, pady=(2, 6))

        tk.Frame(card, bg=COLORS["border"], height=1).pack(fill="x", padx=14)

        # ── Área de entrada ──────────────────────────────────────────────────
        input_area = tk.Frame(card, bg=COLORS["bg_card"])
        input_area.pack(fill="x", padx=14, pady=10)

        tk.Label(input_area, text=ind["field_label"], font=self.f_label,
                 bg=COLORS["bg_card"], fg=COLORS["text_main"]).pack(anchor="w")

        if ind["field_type"] == "numeric":
            self._build_numeric_input(input_area, ind)
        else:
            self._build_binary_input(input_area, ind)

        # ── Separador y validación experto ──────────────────────────────────
        tk.Frame(card, bg=COLORS["border"], height=1).pack(fill="x", padx=14)

        val_area = tk.Frame(card, bg=COLORS["bg_card"])
        val_area.pack(fill="x", padx=14, pady=10)

        tk.Label(val_area,
                 text="Validación del experto: ¿Este indicador confirma vulnerabilidad P1?",
                 font=self.f_label_bold, bg=COLORS["bg_card"],
                 fg=COLORS["text_main"]).pack(anchor="w")

        btn_row = tk.Frame(val_area, bg=COLORS["bg_card"])
        btn_row.pack(anchor="w", pady=(6, 0))

        yn_var = tk.StringVar(value="?")
        self.yn_vars[ind["id"]] = yn_var

        for opt, label, yn_bg, yn_fg in [
            ("y", "SÍ – confirma vulnerabilidad", COLORS["yes_bg"], COLORS["yes_fg"]),
            ("n", "NO – no confirma vulnerabilidad", COLORS["no_bg"], COLORS["no_fg"]),
            ("?", "Sin datos / pendiente", COLORS["na_bg"], COLORS["na_fg"]),
        ]:
            b = tk.Button(
                btn_row, text=label, font=self.f_small,
                bg=COLORS["inactive_btn"], fg=COLORS["inactive_btn_fg"],
                relief="solid", bd=1, cursor="hand2",
                padx=10, pady=4,
                command=lambda o=opt, v=yn_var, b_bg=yn_bg, b_fg=yn_fg,
                               iid=ind["id"]: self._set_yn(iid, o, b_bg, b_fg)
            )
            b.pack(side="left", padx=(0, 6))
            # guardar referencia para poder resaltar
            if not hasattr(self, "_yn_btns"):
                self._yn_btns = {}
            self._yn_btns[f"{ind['id']}_{opt}"] = (b, yn_bg, yn_fg)

    def _build_numeric_input(self, parent, ind):
        row = tk.Frame(parent, bg=COLORS["bg_card"])
        row.pack(anchor="w", pady=(4, 0))

        var = tk.StringVar()
        self.numeric_vars[ind["id"]] = var

        entry = tk.Entry(row, textvariable=var, font=self.f_label,
                         width=12, relief="solid", bd=1,
                         bg=COLORS["bg"], fg=COLORS["text_main"])
        entry.pack(side="left")

        if ind["unit"]:
            tk.Label(row, text=ind["unit"], font=self.f_small,
                     bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(side="left", padx=(6, 0))

        # Live feedback cuando hay umbral
        if ind["threshold_value"] is not None:
            feedback_lbl = tk.Label(row, text="", font=self.f_small,
                                    bg=COLORS["bg_card"], fg=COLORS["text_secondary"])
            feedback_lbl.pack(side="left", padx=(12, 0))
            threshold = ind["threshold_value"]
            direction = ind["threshold_direction"]

            def on_change(*args, lbl=feedback_lbl, t=threshold, d=direction):
                try:
                    val = float(var.get().replace(",", "."))
                    if d == "below":
                        if val < t:
                            lbl.config(text=f"▼ Bajo umbral ({t} {ind['unit']}) → RIESGO ALTO",
                                       fg=COLORS["no_fg"])
                        else:
                            lbl.config(text=f"▲ Sobre umbral ({t} {ind['unit']}) → riesgo bajo",
                                       fg=COLORS["yes_fg"])
                except ValueError:
                    lbl.config(text="")

            var.trace_add("write", on_change)

    def _build_binary_input(self, parent, ind):
        row = tk.Frame(parent, bg=COLORS["bg_card"])
        row.pack(anchor="w", pady=(4, 0))

        var = tk.StringVar(value="")
        self.numeric_vars[ind["id"]] = var

        for val, label in [("si", "Sí"), ("no", "No"), ("desconocido", "Desconocido")]:
            rb = tk.Radiobutton(
                row, text=label, variable=var, value=val,
                font=self.f_label, bg=COLORS["bg_card"],
                fg=COLORS["text_main"], activebackground=COLORS["bg_card"],
                selectcolor=COLORS["bg"]
            )
            rb.pack(side="left", padx=(0, 14))

    def _set_yn(self, iid, opt, yn_bg, yn_fg):
        self.yn_vars[iid].set(opt)
        # Resaltar el botón seleccionado
        for o in ["y", "n", "?"]:
            key = f"{iid}_{o}"
            if key in self._yn_btns:
                b, bg, fg = self._yn_btns[key]
                if o == opt:
                    b.config(bg=bg, fg=fg, relief="solid", bd=2)
                else:
                    b.config(bg=COLORS["inactive_btn"],
                             fg=COLORS["inactive_btn_fg"],
                             relief="solid", bd=1)

    def _clear_all(self):
        for var in self.numeric_vars.values():
            var.set("")
        for iid, yn_var in self.yn_vars.items():
            yn_var.set("?")
            for o in ["y", "n", "?"]:
                key = f"{iid}_{o}"
                if key in self._yn_btns:
                    b, bg, fg = self._yn_btns[key]
                    b.config(bg=COLORS["inactive_btn"],
                             fg=COLORS["inactive_btn_fg"],
                             relief="solid", bd=1)
        self.household_id.set("HOG-001")

    def _compute_result(self):
        # Recoger respuestas
        results = {}
        for ind in INDICATORS:
            results[ind["id"]] = {
                "label": ind["label"],
                "role": ind["role"],
                "data_value": self.numeric_vars.get(ind["id"], tk.StringVar()).get(),
                "expert_yn": self.yn_vars.get(ind["id"], tk.StringVar()).get(),
            }

        # Lógica de activación P1:
        # Core: I1 Y/N = "y"  ó  I2 Y/N = "y"
        # Severidad: fracción de indicadores secundarios con Y/N = "y"
        primary_confirmed = sum(
            1 for iid in ["I1", "I2"]
            if results.get(iid, {}).get("expert_yn") == "y"
        )
        secondary_confirmed = sum(
            1 for iid in ["I3", "I4", "I11", "I12"]
            if results.get(iid, {}).get("expert_yn") == "y"
        )
        secondary_total = 4
        severity = secondary_confirmed / secondary_total if secondary_total > 0 else 0

        if primary_confirmed >= 1:
            activation = "ACTIVADO"
        elif primary_confirmed == 0 and secondary_confirmed >= 2:
            activation = "PROBABLE (revisar)"
        else:
            activation = "NO ACTIVADO"

        # Mostrar ventana resultado
        self._show_result_window(
            activation, primary_confirmed, secondary_confirmed,
            severity, results
        )

    def _show_result_window(self, activation, primary_count,
                            secondary_count, severity, results):
        win = tk.Toplevel(self)
        win.title(f"Resultado P1 – {self.household_id.get()}")
        win.geometry("680x580")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        if activation == "ACTIVADO":
            res_bg = COLORS["result_activated"]
            res_border = COLORS["result_activated_border"]
            res_fg = COLORS["yes_fg"]
        elif activation == "PROBABLE (revisar)":
            res_bg = COLORS["result_uncertain"]
            res_border = COLORS["result_uncertain_border"]
            res_fg = "#BA7517"
        else:
            res_bg = COLORS["result_not_activated"]
            res_border = COLORS["result_not_activated_border"]
            res_fg = COLORS["text_secondary"]

        # Banner resultado
        banner = tk.Frame(win, bg=res_bg,
                          highlightbackground=res_border,
                          highlightthickness=2)
        banner.pack(fill="x", padx=20, pady=(20, 0))

        tk.Label(banner, text=f"P1 – Vulnerabilidad Económica Estructural",
                 font=self.f_label, bg=res_bg,
                 fg=res_fg).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(banner, text=activation,
                 font=self.f_result, bg=res_bg,
                 fg=res_fg).pack(anchor="w", padx=14, pady=(0, 4))

        tk.Label(banner,
                 text=(
                     f"Hogar: {self.household_id.get()}  ·  "
                     f"Primarios confirmados: {primary_count}/2  ·  "
                     f"Secundarios confirmados: {secondary_count}/4  ·  "
                     f"Severidad: {severity:.0%}  ·  "
                     f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
                 ),
                 font=self.f_small, bg=res_bg,
                 fg=res_fg).pack(anchor="w", padx=14, pady=(0, 10))

        # Detalle por indicador
        tk.Label(win, text="Detalle por indicador",
                 font=self.f_header, bg=COLORS["bg"],
                 fg=COLORS["text_main"]).pack(anchor="w", padx=20, pady=(14, 4))

        detail_frame = tk.Frame(win, bg=COLORS["bg"])
        detail_frame.pack(fill="both", expand=True, padx=20)

        for ind in INDICATORS:
            r = results[ind["id"]]
            yn = r["expert_yn"]
            val = r["data_value"] if r["data_value"] else "—"
            row = tk.Frame(detail_frame, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
            row.pack(fill="x", pady=3)

            # Badge rol
            role_text = "PRI" if ind["role"] == "primary" else "SEC"
            role_bg = COLORS["bg_primary_badge"] if ind["role"] == "primary" else COLORS["bg_secondary_badge"]
            role_fg = COLORS["text_primary_badge"] if ind["role"] == "primary" else COLORS["text_secondary_badge"]
            tk.Label(row, text=role_text, font=self.f_badge,
                     bg=role_bg, fg=role_fg, width=4,
                     padx=4, pady=2).pack(side="left", padx=(8, 6), pady=6)

            # ID
            tk.Label(row, text=ind["id"], font=self.f_label_bold,
                     bg=COLORS["bg_card"], fg=COLORS["text_main"],
                     width=4).pack(side="left")

            # Valor
            tk.Label(row, text=val, font=self.f_mono,
                     bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                     width=14, anchor="w").pack(side="left", padx=(6, 0))

            # Decisión experto
            if yn == "y":
                yn_bg, yn_fg, yn_text = COLORS["yes_bg"], COLORS["yes_fg"], "SÍ"
            elif yn == "n":
                yn_bg, yn_fg, yn_text = COLORS["no_bg"], COLORS["no_fg"], "NO"
            else:
                yn_bg, yn_fg, yn_text = COLORS["na_bg"], COLORS["na_fg"], "?"

            tk.Label(row, text=yn_text, font=self.f_badge,
                     bg=yn_bg, fg=yn_fg, width=4,
                     padx=6, pady=2).pack(side="right", padx=(0, 8), pady=6)

            tk.Label(row, text=ind["id"] + " – " + ind["field_label"][:60],
                     font=self.f_small, bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"],
                     anchor="w").pack(side="left", padx=(8, 0))

        # Exportar JSON
        export_frame = tk.Frame(win, bg=COLORS["bg"])
        export_frame.pack(fill="x", padx=20, pady=(10, 0))

        def export():
            payload = {
                "household_id": self.household_id.get(),
                "profile": "P1",
                "timestamp": datetime.now().isoformat(),
                "activation": activation,
                "primary_confirmed": primary_count,
                "secondary_confirmed": secondary_count,
                "severity_ratio": round(severity, 3),
                "indicators": results,
            }
            fname = f"P1_{self.household_id.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            tk.Label(export_frame,
                     text=f"Guardado: {fname}",
                     font=self.f_small, bg=COLORS["bg"],
                     fg=COLORS["yes_fg"]).pack(side="left", padx=(10, 0))

        tk.Button(export_frame, text="Exportar JSON",
                  font=self.f_label, bg=COLORS["bg"], fg=COLORS["text_main"],
                  relief="solid", bd=1, cursor="hand2",
                  padx=12, pady=5,
                  command=export).pack(side="left")

        tk.Button(export_frame, text="Cerrar",
                  font=self.f_label, bg=COLORS["active_btn"],
                  fg=COLORS["active_btn_fg"],
                  relief="flat", bd=0, cursor="hand2",
                  padx=12, pady=5,
                  command=win.destroy).pack(side="right")


if __name__ == "__main__":
    app = P1VulnerabilityApp()
    app.mainloop()
