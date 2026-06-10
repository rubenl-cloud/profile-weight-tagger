"""
SOCIAREM – Evaluación de perfiles de vulnerabilidad energética
Proof of Concept · Piloto Messina

6 perfiles (D1.5):
  P1 Económica estructural      · primarios I1,I2 · sec. I3,I4,I11,I12,I21,I25
  P2 Condiciones de vivienda     · primarios I9,I10 · sec. I5,I6,I7,I20
  P3 Pobreza energética oculta   · primario I8 · sec. I1,I3,I4,I5,I6,I9,I10
  P4 Fragilidad / dep. eléctrica · primarios I15,I16,I17 · sec. I5,I6,I9,I10
  P5 Territorial y acceso        · primarios I18,I19 · sec. I22,I23
  P6 Socio-comunitaria           · primarios I22,I23,I24 · sec. I1,I3,I18

Flujo:
  Fase 0: configuración de umbrales (el experto fija los puntos de corte)
  Fase 1: revisión de indicadores + etiquetado experto (+ auto-demo)
  Fase 2: pesos optimizados + sliders + métricas + umbral decisión + export
"""

import tkinter as tk
from tkinter import filedialog
import math
import json
import csv
from datetime import datetime

# ─── Paleta clara · sin verde/rojo en indicadores (neutro para evitar sesgo) ─
C = {
    "bg":           "#F4F5F7",
    "card":         "#FFFFFF",
    "card2":        "#F0F1F3",
    "border":       "#D8DCE3",
    "accent":       "#2563EB",
    "accent2":      "#7C3AED",
    "text":         "#111827",
    "muted":        "#6B7280",
    "ok":           "#16A34A",
    "warn":         "#D97706",
    "danger":       "#DC2626",
    "ok_dim":       "#DCFCE7",
    "warn_dim":     "#FEF3C7",
    "danger_dim":   "#FEE2E2",
    "neutral":      "#374151",     # valor de indicador (sin connotación)
    "neutral_dim":  "#F0F1F3",
    "badge_pri":    "#DBEAFE",
    "badge_pri_fg": "#1D4ED8",
    "badge_sec":    "#EDE9FE",
    "badge_sec_fg": "#6D28D9",
    "sel":          "#EFF6FF",
    "phase2_bg":    "#F0F4FF",
    "phase2_card":  "#FFFFFF",
    "slider_bg":    "#E2E8F0",
    "tooltip_bg":   "#1F2937",
    "tooltip_fg":   "#F9FAFB",
}

PROFILE_COLORS = {
    "P1": "#2563EB", "P2": "#D97706", "P3": "#0891B2",
    "P4": "#7C3AED", "P5": "#16A34A", "P6": "#DB2777",
}

# ─── Umbrales configurables (valores por defecto) ────────────────────────────
# El usuario los ajusta en la fase 0. Cada umbral convierte un valor numérico
# en señal de riesgo y define la normalización del indicador.
DEFAULT_THRESHOLDS = {
    "pobreza":      1050,   # I1/I2: € /mes equivalente, umbral pobreza relativa
    "renta_riesgo": 780,    # I1: € /mes, riesgo alto
    "carga":        10.0,   # I3: % de carga energética
    "consumo_elec": 350,    # I5: kWh/mes, consumo eléctrico alto
    "consumo_gas":  300,    # I6: kWh/mes, consumo no eléctrico alto
    "infra_elec":   150,    # I5: kWh/mes, consumo "anormalmente bajo" (P3)
    "infra_gas":    100,    # I6: kWh/mes, consumo no eléctrico bajo (P3)
    "ahorros":      1,      # I21: meses de renta cubiertos mínimos
    "estabilidad":  2,      # I25: años de residencia para considerarse estable
    "territorial":  60,     # I18: índice territorial (0-100), riesgo si >
    "acceso":       30,     # I19: minutos de acceso a servicios, riesgo si >
}

# ─── Definición de indicadores ───────────────────────────────────────────────
# norm(hh, T) -> [0,1] vulnerabilidad · risk(hh, T) -> bool · display(hh) -> str
# Las escalas ordinales (0-3) y binarias no dependen de umbrales configurables.

def clamp(x): return max(0.0, min(1.0, x))

INDICATOR_DEFS = {
    # ── Categoría A: Economía ──────────────────────────────────────────────
    "I1": {
        "name": "Renta neta equiv.", "long": "I1 – Renta neta mensual equivalente",
        "role": "primario", "source": "DS2 · ISEE",
        "definition": ("Renta neta mensual ajustada por composición (ISEE). Mide la capacidad "
                       "económica efectiva para afrontar gastos energéticos."),
        "display": lambda hh: f"{hh['I1']} €/mes",
        "note": lambda T: f"< {T['renta_riesgo']} €/mes → riesgo",
        "risk": lambda hh, T: hh["I1"] < T["renta_riesgo"],
        "norm": lambda hh, T: clamp((1200 - hh["I1"]) / 800),
    },
    "I2": {
        "name": "Bajo umbral pobreza", "long": "I2 – Hogar bajo umbral de pobreza relativa",
        "role": "primario", "source": "DS2 · ISEE (derivado)",
        "definition": ("Indica si la renta equivalente está por debajo del umbral de pobreza "
                       "relativa (60% mediana nacional). Se deriva directamente de I1."),
        "display": lambda hh: "—",  # se completa en runtime con el umbral
        "note": lambda T: f"umbral: {T['pobreza']} €/mes",
        "risk": lambda hh, T: hh["I1"] < T["pobreza"],
        "norm": lambda hh, T: clamp((T["pobreza"] - hh["I1"]) / T["pobreza"]),
        "derived": True,
        "display_t": lambda hh, T: f"{int(hh['I1']/T['pobreza']*100)}% del umbral",
    },
    # ── Categoría B: Carga / pago ──────────────────────────────────────────
    "I3": {
        "name": "Carga energética", "long": "I3 – Carga energética del hogar",
        "role": "secundario", "source": "DS4 · DS14",
        "definition": ("Cociente entre gasto energético total y renta. Criterio LIHC: "
                       "carga alta si supera el umbral configurado."),
        "display": lambda hh: f"{hh['I3']:.1f}%",
        "note": lambda T: f"> {T['carga']:.0f}% → riesgo",
        "risk": lambda hh, T: hh["I3"] > T["carga"],
        "norm": lambda hh, T: clamp((hh["I3"] - 5) / 25),
    },
    "I4": {
        "name": "Impago / corte", "long": "I4 – Impago o corte de suministro",
        "role": "secundario", "source": "DS8 · Fundación",
        "definition": "Impagos, deudas o cortes de suministro en los últimos 12 meses.",
        "display": lambda hh: "SÍ" if hh["I4"] else "NO",
        "note": lambda T: "Últimos 12 meses",
        "risk": lambda hh, T: bool(hh["I4"]),
        "norm": lambda hh, T: float(hh["I4"]),
    },
    # ── Categoría C: Consumo ───────────────────────────────────────────────
    "I5": {
        "name": "Consumo eléctrico", "long": "I5 – Consumo eléctrico del hogar",
        "role": "secundario", "source": "DS4 · DS6",
        "definition": "Consumo eléctrico total del hogar (kWh/mes).",
        "display": lambda hh: f"{hh['I5']} kWh",
        "note": lambda T: f"> {T['consumo_elec']} kWh → alto",
        "risk": lambda hh, T: hh["I5"] > T["consumo_elec"],
        "norm": lambda hh, T: clamp((hh["I5"] - 150) / 350),
    },
    "I6": {
        "name": "Consumo no eléctrico", "long": "I6 – Consumo energético no eléctrico",
        "role": "secundario", "source": "DS14",
        "definition": "Consumo de fuentes no eléctricas (gas, GLP, biomasa) en kWh equivalentes.",
        "display": lambda hh: f"{hh['I6']} kWh",
        "note": lambda T: f"> {T['consumo_gas']} kWh → alto",
        "risk": lambda hh, T: hh["I6"] > T["consumo_gas"],
        "norm": lambda hh, T: clamp((hh["I6"] - 100) / 350),
    },
    "I7": {
        "name": "Perfil horario", "long": "I7 – Perfil de consumo por franja horaria",
        "role": "secundario", "source": "DS6",
        "definition": ("Distribución del consumo eléctrico durante el día. Un perfil rígido "
                       "puede indicar limitaciones por sistemas inflexibles. Escala 0=flexible … 3=muy rígido."),
        "display": lambda hh: ["Flexible","Moderado","Rígido","Muy rígido"][hh["I7"]],
        "note": lambda T: "Rígido → riesgo",
        "risk": lambda hh, T: hh["I7"] >= 2,
        "norm": lambda hh, T: hh["I7"] / 3.0,
    },
    "I8": {
        "name": "Pobreza energética oculta", "long": "I8 – Pobreza energética oculta",
        "role": "primario", "source": "DS4 · DS6 · DS15 (derivado)",
        "definition": ("Consumo anormalmente bajo respecto a hogares comparables, no explicable "
                       "por eficiencia. Se deriva del cruce de I5/I6 con valores de referencia, "
                       "verificado contra habitabilidad (I9/I10) y renta (I1/I3)."),
        "display": lambda hh: "—",
        "note": lambda T: "Infraconsumo forzado",
        "risk": lambda hh, T: _i8_risk(hh, T),
        "norm": lambda hh, T: _i8_norm(hh, T),
        "derived": True,
        "display_t": lambda hh, T: _i8_display(hh, T),
    },
    # ── Categoría D: Vivienda ──────────────────────────────────────────────
    "I9": {
        "name": "Habitabilidad", "long": "I9 – Condiciones de habitabilidad",
        "role": "primario", "source": "DS11 · DS10",
        "definition": ("Estado térmico, estructural y sanitario de la vivienda (aislamiento, "
                       "humedades, riesgos para la salud). Escala 0=adecuada … 3=crítica."),
        "display": lambda hh: ["Adecuada","Aceptable","Pobre","Crítica"][hh["I9"]],
        "note": lambda T: "Pobre/crítica → riesgo",
        "risk": lambda hh, T: hh["I9"] >= 2,
        "norm": lambda hh, T: hh["I9"] / 3.0,
    },
    "I10": {
        "name": "Sistemas energéticos", "long": "I10 – Sistemas y elementos de consumo",
        "role": "primario", "source": "DS13",
        "definition": ("Sistemas energéticos del hogar (calefacción, ACS, refrigeración) y su "
                       "adecuación. Escala 0=eficiente … 3=obsoleto."),
        "display": lambda hh: ["Eficiente","Adecuado","Deficiente","Obsoleto"][hh["I10"]],
        "note": lambda T: "Deficiente/obsoleto → riesgo",
        "risk": lambda hh, T: hh["I10"] >= 2,
        "norm": lambda hh, T: hh["I10"] / 3.0,
    },
    # ── Categoría E: Acceso a asistencia ───────────────────────────────────
    "I11": {
        "name": "Recibe ayudas", "long": "I11 – Acceso a ayudas sociales/energéticas",
        "role": "secundario", "source": "DS8 · DS3",
        "definition": ("Si el hogar recibe ayudas públicas energéticas (bonus, tarifa social) "
                       "o sociales formales (RdC). Distingue vulnerabilidad reconocida."),
        "display": lambda hh: "SÍ" if hh["I11"] else "NO",
        "note": lambda T: "Bonus energía / RdC",
        "risk": lambda hh, T: bool(hh["I11"]),
        "norm": lambda hh, T: float(hh["I11"]),
    },
    "I12": {
        "name": "Microcrédito", "long": "I12 – Acceso a microcrédito/apoyo comunitario",
        "role": "secundario", "source": "DS7 · DS27",
        "definition": ("Acceso a microcrédito ético o apoyo financiero comunitario. "
                       "La ausencia refuerza la severidad."),
        "display": lambda hh: "SÍ" if hh["I12"] else "NO",
        "note": lambda T: "Sin acceso → riesgo",
        "risk": lambda hh, T: not bool(hh["I12"]),
        "norm": lambda hh, T: 1.0 - float(hh["I12"]),
    },
    # ── Categoría G: Fragilidad del hogar ──────────────────────────────────
    "I15": {
        "name": "Personas dependientes", "long": "I15 – Número de personas dependientes",
        "role": "primario", "source": "DS16",
        "definition": ("Número de personas <14 o >70 años en el hogar (mayores necesidades "
                       "térmicas y de cuidado). Escala por nº de personas."),
        "display": lambda hh: f"{hh['I15']} pers.",
        "note": lambda T: "≥ 1 dependiente → riesgo",
        "risk": lambda hh, T: hh["I15"] >= 1,
        "norm": lambda hh, T: clamp(hh["I15"] / 3.0),
    },
    "I16": {
        "name": "Dependencia funcional", "long": "I16 – Dependencia funcional / movilidad reducida",
        "role": "primario", "source": "DS17",
        "definition": ("Presencia de personas con dependencia funcional o movilidad reducida "
                       "reconocida. Aumenta sensibilidad a cortes y disconfort térmico."),
        "display": lambda hh: "SÍ" if hh["I16"] else "NO",
        "note": lambda T: "Dependencia reconocida",
        "risk": lambda hh, T: bool(hh["I16"]),
        "norm": lambda hh, T: float(hh["I16"]),
    },
    "I17": {
        "name": "Enfermedad crónica / dep. eléctrica", "long": "I17 – Enfermedades crónicas y dependencia eléctrica",
        "role": "primario", "source": "DS18",
        "definition": ("Enfermedades crónicas que aumentan necesidades energéticas o dependencia "
                       "de equipos médicos. Escala: 0=ninguna, 1=térmica, 2=eléctrica intermitente, "
                       "3=eléctrica vital (O₂, ventilación)."),
        "display": lambda hh: ["Ninguna","Térmica","Eléct. interm.","Eléct. vital"][hh["I17"]],
        "note": lambda T: "Dependencia eléctrica → riesgo",
        "risk": lambda hh, T: hh["I17"] >= 2,
        "norm": lambda hh, T: hh["I17"] / 3.0,
    },
    # ── Categoría H: Territorial ───────────────────────────────────────────
    "I18": {
        "name": "Índice territorial", "long": "I18 – Índice territorial socio-ambiental",
        "role": "primario", "source": "DS19 · DS20",
        "definition": ("Índice de riesgo del área de residencia (privación, exposición ambiental). "
                       "Escala 0-100, mayor = más desfavorecida."),
        "display": lambda hh: f"{hh['I18']}/100",
        "note": lambda T: f"> {T['territorial']} → riesgo",
        "risk": lambda hh, T: hh["I18"] > T["territorial"],
        "norm": lambda hh, T: clamp(hh["I18"] / 100.0),
    },
    "I19": {
        "name": "Acceso a servicios", "long": "I19 – Acceso efectivo a infraestructura y servicios",
        "role": "primario", "source": "DS21 · DS22",
        "definition": ("Tiempo medio de acceso a servicios esenciales (energía, salud, apoyo "
                       "social). Mayor tiempo = peor acceso."),
        "display": lambda hh: f"{hh['I19']} min",
        "note": lambda T: f"> {T['acceso']} min → riesgo",
        "risk": lambda hh, T: hh["I19"] > T["acceso"],
        "norm": lambda hh, T: clamp(hh["I19"] / 60.0),
    },
    # ── Categoría I: Percepción ────────────────────────────────────────────
    "I20": {
        "name": "Temp. percibida", "long": "I20 – Incapacidad percibida de mantener temperatura",
        "role": "secundario", "source": "DS8",
        "definition": "Percepción de incapacidad de mantener temperatura adecuada (frío/calor).",
        "display": lambda hh: "SÍ" if hh["I20"] else "NO",
        "note": lambda T: "Malestar térmico declarado",
        "risk": lambda hh, T: bool(hh["I20"]),
        "norm": lambda hh, T: float(hh["I20"]),
    },
    # ── Categoría J: Resiliencia ───────────────────────────────────────────
    "I21": {
        "name": "Ahorros líquidos", "long": "I21 – Ahorros líquidos o activos realizables",
        "role": "secundario", "source": "DS2 · DS8",
        "definition": ("Ahorros líquidos para absorber shocks, medidos en meses de renta cubiertos."),
        "display": lambda hh: f"{hh['I21']} mes{'es' if hh['I21']!=1 else ''}" if hh["I21"]>0 else "Ninguno",
        "note": lambda T: f"< {T['ahorros']} mes → riesgo",
        "risk": lambda hh, T: hh["I21"] < T["ahorros"],
        "norm": lambda hh, T: clamp((3 - hh["I21"]) / 3),
    },
    "I22": {
        "name": "Red de apoyo social", "long": "I22 – Red de apoyo social del hogar",
        "role": "primario", "source": "DS25 · DS29",
        "definition": ("Disponibilidad de apoyo informal (familia, vecinos, comunidad). "
                       "Escala 0=red sólida … 3=aislamiento total."),
        "display": lambda hh: ["Sólida","Moderada","Débil","Aislamiento"][hh["I22"]],
        "note": lambda T: "Débil/aislamiento → riesgo",
        "risk": lambda hh, T: hh["I22"] >= 2,
        "norm": lambda hh, T: hh["I22"] / 3.0,
    },
    "I23": {
        "name": "Participación comunitaria", "long": "I23 – Participación en actividades comunitarias",
        "role": "primario", "source": "DS24",
        "definition": ("Grado de participación en actividades de la comunidad energética o "
                       "iniciativas colectivas. Escala 0=regular … 3=nula."),
        "display": lambda hh: ["Regular","Ocasional","Escasa","Nula"][hh["I23"]],
        "note": lambda T: "Escasa/nula → riesgo",
        "risk": lambda hh, T: hh["I23"] >= 2,
        "norm": lambda hh, T: hh["I23"] / 3.0,
    },
    "I24": {
        "name": "Estigmatización percibida", "long": "I24 – Aceptación social y estigmatización",
        "role": "primario", "source": "DS26 · DS29",
        "definition": ("Estigmatización o rechazo social percibido que limita la participación "
                       "y el acceso a recursos comunitarios. Escala 0=ninguna … 3=severa."),
        "display": lambda hh: ["Ninguna","Leve","Moderada","Severa"][hh["I24"]],
        "note": lambda T: "Moderada/severa → riesgo",
        "risk": lambda hh, T: hh["I24"] >= 2,
        "norm": lambda hh, T: hh["I24"] / 3.0,
    },
    # ── Categoría K: Estabilidad ───────────────────────────────────────────
    "I25": {
        "name": "Estabilidad residencial", "long": "I25 – Estabilidad administrativa y residencial",
        "role": "secundario", "source": "DS8",
        "definition": ("Estabilidad de la situación residencial y administrativa, en años de "
                       "residencia continua."),
        "display": lambda hh: f"{hh['I25']} año{'s' if hh['I25']!=1 else ''}" if hh["I25"]>0 else "< 1 año",
        "note": lambda T: f"< {T['estabilidad']} años → inestable",
        "risk": lambda hh, T: hh["I25"] < T["estabilidad"],
        "norm": lambda hh, T: clamp((5 - hh["I25"]) / 5),
    },
}

# ── I8 (pobreza energética oculta) lógica derivada ──────────────────────────
def _i8_low_consumption(hh, T):
    return hh["I5"] < T["infra_elec"] and hh["I6"] < T["infra_gas"]
def _i8_risk(hh, T):
    # infraconsumo + (renta baja O carga alta) + NO explicable por buena vivienda
    low = _i8_low_consumption(hh, T)
    econ = hh["I1"] < T["pobreza"] or hh["I3"] > T["carga"]
    not_efficient = hh["I9"] >= 1 or hh["I10"] >= 1   # vivienda no es eficiente
    return low and econ and not_efficient
def _i8_norm(hh, T):
    if _i8_risk(hh, T):
        # severidad proporcional a cuán bajo es el consumo
        deficit = (T["infra_elec"] - hh["I5"]) / T["infra_elec"]
        return clamp(0.5 + 0.5 * deficit)
    return 0.0
def _i8_display(hh, T):
    return "Infraconsumo" if _i8_risk(hh, T) else "Normal"

# ─── Configuración de los 6 perfiles ─────────────────────────────────────────
PROFILES = {
    "P1": {
        "name": "Vulnerabilidad económica estructural", "short": "Económica",
        "display_keys": ["I1","I2","I3","I4","I11","I12","I21","I25"],
        "weight_keys":  ["I1","I3","I4","I11","I12","I21","I25"],
        "init_weights": {"I1":0.28,"I3":0.18,"I4":0.15,"I11":0.12,"I12":0.10,"I21":0.10,"I25":0.07},
        "question": "¿Presenta vulnerabilidad P1 · económica estructural?",
    },
    "P2": {
        "name": "Vulnerabilidad por condiciones de la vivienda", "short": "Vivienda",
        "display_keys": ["I9","I10","I5","I6","I7","I20"],
        "weight_keys":  ["I9","I10","I5","I6","I7","I20"],
        "init_weights": {"I9":0.30,"I10":0.25,"I5":0.12,"I6":0.12,"I7":0.08,"I20":0.13},
        "question": "¿Presenta vulnerabilidad P2 · condiciones de la vivienda?",
    },
    "P3": {
        "name": "Pobreza energética oculta (infraconsumo)", "short": "P. oculta",
        "display_keys": ["I8","I5","I6","I1","I3","I4","I9","I10"],
        "weight_keys":  ["I8","I5","I6","I1","I3","I4","I9","I10"],
        "init_weights": {"I8":0.34,"I5":0.12,"I6":0.10,"I1":0.14,"I3":0.12,"I4":0.08,"I9":0.05,"I10":0.05},
        "question": "¿Presenta vulnerabilidad P3 · pobreza energética oculta?",
    },
    "P4": {
        "name": "Fragilidad del hogar y dependencia eléctrica", "short": "Fragilidad",
        "display_keys": ["I15","I16","I17","I5","I6","I9","I10"],
        "weight_keys":  ["I15","I16","I17","I5","I6","I9","I10"],
        "init_weights": {"I15":0.18,"I16":0.22,"I17":0.30,"I5":0.10,"I6":0.06,"I9":0.07,"I10":0.07},
        "question": "¿Presenta vulnerabilidad P4 · fragilidad / dependencia eléctrica?",
    },
    "P5": {
        "name": "Vulnerabilidad territorial y de acceso", "short": "Territorial",
        "display_keys": ["I18","I19","I22","I23"],
        "weight_keys":  ["I18","I19","I22","I23"],
        "init_weights": {"I18":0.34,"I19":0.34,"I22":0.16,"I23":0.16},
        "question": "¿Presenta vulnerabilidad P5 · territorial y de acceso?",
    },
    "P6": {
        "name": "Vulnerabilidad socio-comunitaria", "short": "Socio-com.",
        "display_keys": ["I22","I23","I24","I1","I3","I18"],
        "weight_keys":  ["I22","I23","I24","I1","I3","I18"],
        "init_weights": {"I22":0.26,"I23":0.22,"I24":0.22,"I1":0.12,"I3":0.10,"I18":0.08},
        "question": "¿Presenta vulnerabilidad P6 · socio-comunitaria?",
    },
}

# ─── 10 hogares · realidades muy distintas, perfiles solapados ───────────────
# Cada perfil tiene ~5 vulnerables y ~5 no vulnerables repartidos.
# Campos completos para los 25 indicadores usados.
HOUSEHOLDS = [
    {"id":"HOG-01","nombre":"Hogar 1","edad":67,"composicion":"Pensionista sola, O₂ nocturno",
     "desc":"Pensión mínima. Concentrador de oxígeno nocturno. Piso antiguo con humedades, "
            "barrio céntrico bien comunicado, buena red familiar.",
     "I1":530,"I3":18.2,"I4":1,"I5":145,"I6":78,"I7":2,"I9":2,"I10":2,
     "I11":1,"I12":0,"I15":1,"I16":1,"I17":3,"I18":35,"I19":12,"I20":1,
     "I21":0,"I22":1,"I23":1,"I24":0,"I25":12,
     "gt":{"P1":1,"P2":1,"P3":1,"P4":1,"P5":0,"P6":0}},

    {"id":"HOG-02","nombre":"Hogar 2","edad":34,"composicion":"Madre sola, 2 hijos menores",
     "desc":"Trabajo informal, ingresos irregulares. Corte de luz hace 8 meses. Vivienda precaria "
            "mal aislada en zona periférica. Recién llegada, red social escasa.",
     "I1":490,"I3":22.7,"I4":1,"I5":340,"I6":160,"I7":2,"I9":3,"I10":2,
     "I11":0,"I12":1,"I15":2,"I16":0,"I17":0,"I18":68,"I19":42,"I20":1,
     "I21":0,"I22":3,"I23":3,"I24":2,"I25":2,
     "gt":{"P1":1,"P2":1,"P3":0,"P4":1,"P5":1,"P6":1}},

    {"id":"HOG-03","nombre":"Hogar 3","edad":74,"composicion":"Solo, pensión invalidez",
     "desc":"Consumo anormalmente bajo: se abriga en vez de calefactar. Piso mal aislado. "
            "Renta baja, impago reciente. Barrio bien conectado, red vecinal moderada.",
     "I1":510,"I3":8.1,"I4":1,"I5":120,"I6":85,"I7":1,"I9":3,"I10":3,
     "I11":1,"I12":0,"I15":1,"I16":0,"I17":1,"I18":64,"I19":38,"I20":1,
     "I21":0,"I22":1,"I23":2,"I24":1,"I25":22,
     "gt":{"P1":1,"P2":1,"P3":1,"P4":0,"P5":1,"P6":0}},

    {"id":"HOG-04","nombre":"Hogar 4","edad":45,"composicion":"Pareja, 1 hijo con parálisis cerebral",
     "desc":"Cuidados intensivos en casa, equipos eléctricos vitales. ISEE razonable. Vivienda "
            "adecuada, barrio bien comunicado, buena integración comunitaria.",
     "I1":1050,"I3":18.6,"I4":0,"I5":440,"I6":160,"I7":3,"I9":1,"I10":1,
     "I11":1,"I12":0,"I15":1,"I16":1,"I17":3,"I18":30,"I19":10,"I20":0,
     "I21":2,"I22":1,"I23":0,"I24":0,"I25":10,
     "gt":{"P1":0,"P2":0,"P3":0,"P4":1,"P5":0,"P6":0}},

    {"id":"HOG-05","nombre":"Hogar 5","edad":31,"composicion":"Solo, solicitante asilo",
     "desc":"Centro de acogida temporal aislado en la periferia. Sin ingresos propios. Barrera "
            "institucional total, sin red social, estigmatización percibida. Vivienda compartida deficiente.",
     "I1":290,"I3":31.0,"I4":0,"I5":140,"I6":80,"I7":2,"I9":2,"I10":2,
     "I11":1,"I12":1,"I15":0,"I16":0,"I17":0,"I18":75,"I19":55,"I20":1,
     "I21":0,"I22":3,"I23":3,"I24":3,"I25":1,
     "gt":{"P1":1,"P2":0,"P3":1,"P4":0,"P5":1,"P6":1}},

    {"id":"HOG-06","nombre":"Hogar 6","edad":48,"composicion":"Pareja, 2 hijos adolescentes",
     "desc":"ISEE razonable pero villa antigua con humedades graves y caldera obsoleta. Frío en "
            "invierno. Barrio céntrico, buena red social y participación comunitaria activa.",
     "I1":1120,"I3":13.6,"I4":0,"I5":390,"I6":280,"I7":2,"I9":3,"I10":3,
     "I11":0,"I12":0,"I15":0,"I16":0,"I17":0,"I18":28,"I19":9,"I20":1,
     "I21":3,"I22":0,"I23":0,"I24":0,"I25":10,
     "gt":{"P1":0,"P2":1,"P3":0,"P4":0,"P5":0,"P6":0}},

    {"id":"HOG-07","nombre":"Hogar 7","edad":78,"composicion":"Pareja ancianos dependientes",
     "desc":"Dos pensiones sociales. Consumen muy poco por restricción forzada, no eficiencia. "
            "Vivienda deficiente. Zona rural mal comunicada, lejos de servicios, red social débil.",
     "I1":490,"I3":6.8,"I4":0,"I5":110,"I6":80,"I7":1,"I9":2,"I10":2,
     "I11":1,"I12":0,"I15":2,"I16":1,"I17":1,"I18":62,"I19":48,"I20":1,
     "I21":0,"I22":2,"I23":2,"I24":2,"I25":30,
     "gt":{"P1":1,"P2":1,"P3":1,"P4":1,"P5":1,"P6":1}},

    {"id":"HOG-08","nombre":"Hogar 8","edad":53,"composicion":"Solo, funcionario",
     "desc":"Funcionario municipal, ingresos estables. Piso moderno eficiente en barrio céntrico. "
            "Sin señales de vulnerabilidad en ninguna dimensión. Buena red social.",
     "I1":1540,"I3":4.9,"I4":0,"I5":210,"I6":100,"I7":0,"I9":0,"I10":0,
     "I11":0,"I12":0,"I15":0,"I16":0,"I17":0,"I18":20,"I19":8,"I20":0,
     "I21":6,"I22":0,"I23":1,"I24":0,"I25":15,
     "gt":{"P1":0,"P2":0,"P3":0,"P4":0,"P5":0,"P6":0}},

    {"id":"HOG-09","nombre":"Hogar 9","edad":35,"composicion":"Solo, ex-recluso en reinserción",
     "desc":"6 meses fuera del sistema penitenciario. Sin historial crediticio ni red social, "
            "estigmatización severa. ISEE bajo. Vivienda modesta en barrio céntrico, participación nula.",
     "I1":680,"I3":8.1,"I4":0,"I5":135,"I6":70,"I7":1,"I9":2,"I10":2,
     "I11":1,"I12":0,"I15":0,"I16":0,"I17":0,"I18":38,"I19":14,"I20":1,
     "I21":0,"I22":3,"I23":3,"I24":3,"I25":1,
     "gt":{"P1":1,"P2":0,"P3":1,"P4":0,"P5":0,"P6":1}},

    {"id":"HOG-10","nombre":"Hogar 10","edad":44,"composicion":"Pareja, 2 hijos, clase media",
     "desc":"Ambos empleados fijos, ingresos holgados. Piso en propiedad bien aislado y eficiente. "
            "Barrio bien comunicado, integración comunitaria plena. Sin vulnerabilidad.",
     "I1":1680,"I3":5.8,"I4":0,"I5":280,"I6":160,"I7":1,"I9":0,"I10":0,
     "I11":0,"I12":0,"I15":0,"I16":0,"I17":0,"I18":22,"I19":7,"I20":0,
     "I21":6,"I22":0,"I23":0,"I24":0,"I25":12,
     "gt":{"P1":0,"P2":0,"P3":0,"P4":0,"P5":0,"P6":0}},
]

# ─── Funciones de cálculo (con umbrales configurables T) ─────────────────────

def score(hh, weights, profile, T):
    keys = PROFILES[profile]["weight_keys"]
    total_w = sum(weights.values()) or 1
    return sum(weights[k] * INDICATOR_DEFS[k]["norm"](hh, T) for k in keys) / total_w

def optimize_weights(expert_labels, profile, T):
    init = PROFILES[profile]["init_weights"]
    keys = PROFILES[profile]["weight_keys"]
    try:
        from scipy.optimize import minimize
        import numpy as np
    except ImportError:
        return init.copy()
    LAMBDA = 15.0   # regularización L2 hacia pesos iniciales (interpretabilidad)
    def loss(w_arr):
        w = {k: max(1e-4, w_arr[i]) for i, k in enumerate(keys)}
        total = 0.0
        for hh in HOUSEHOLDS:
            label = expert_labels.get(hh["id"], hh["gt"][profile])
            s = max(1e-7, min(1 - 1e-7, score(hh, w, profile, T)))
            total -= label * math.log(s) + (1 - label) * math.log(1 - s)
        reg = LAMBDA * sum((w_arr[i] - init[k]) ** 2 for i, k in enumerate(keys))
        return total + reg
    w0 = np.array([init[k] for k in keys])
    res = minimize(loss, w0, method="SLSQP",
                   bounds=[(0.001, 1.0)] * len(keys),
                   constraints=[{"type": "eq", "fun": lambda w: sum(w) - 1.0}],
                   options={"maxiter": 800, "ftol": 1e-10})
    if res.success:
        raw = {k: float(max(0.001, res.x[i])) for i, k in enumerate(keys)}
        t = sum(raw.values())
        return {k: v / t for k, v in raw.items()}
    return init.copy()

def compute_metrics(weights, profile, expert_labels, threshold, T):
    tp = fp = tn = fn = 0
    for hh in HOUSEHOLDS:
        label = expert_labels.get(hh["id"], hh["gt"][profile])
        pred = 1 if score(hh, weights, profile, T) >= threshold else 0
        if   label == 1 and pred == 1: tp += 1
        elif label == 0 and pred == 1: fp += 1
        elif label == 0 and pred == 0: tn += 1
        elif label == 1 and pred == 0: fn += 1
    precision = tp/(tp+fp) if (tp+fp) else 0.0
    recall    = tp/(tp+fn) if (tp+fn) else 0.0
    f1        = 2*precision*recall/(precision+recall) if (precision+recall) else 0.0
    accuracy  = (tp+tn)/len(HOUSEHOLDS)
    return {"tp":tp,"fp":fp,"tn":tn,"fn":fn,
            "precision":precision,"recall":recall,"f1":f1,"accuracy":accuracy}

# ─────────────────────────────────────────────────────────────────────────────
class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tip = widget, text, None
        widget.bind("<Enter>", self._show); widget.bind("<Leave>", self._hide)
    def _show(self, _e):
        if self.tip or not self.text: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget); self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, justify="left", bg=C["tooltip_bg"], fg=C["tooltip_fg"],
                 font=("Helvetica Neue", 9), wraplength=320, padx=10, pady=8).pack()
    def _hide(self, _e):
        if self.tip: self.tip.destroy(); self.tip = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOCIAREM · Perfiles de vulnerabilidad · Messina")
        self.geometry("1260x840")
        self.configure(bg=C["bg"])
        self.thresholds = dict(DEFAULT_THRESHOLDS)
        self.configured = False
        self.profile = "P1"
        self.state = {p: {"phase":1,"expert_labels":{},"opt_weights":None,"live_weights":None}
                      for p in PROFILES}
        self.current_idx = 0
        self.decision_threshold = 0.5
        self.search_text = ""
        self.filtered_idx = list(range(len(HOUSEHOLDS)))
        self._show_config_screen()

    # estado del perfil activo
    @property
    def phase(self): return self.state[self.profile]["phase"]
    @phase.setter
    def phase(self, v): self.state[self.profile]["phase"] = v
    @property
    def expert_labels(self): return self.state[self.profile]["expert_labels"]
    @property
    def opt_weights(self): return self.state[self.profile]["opt_weights"]
    @opt_weights.setter
    def opt_weights(self, v): self.state[self.profile]["opt_weights"] = v
    @property
    def live_weights(self): return self.state[self.profile]["live_weights"]
    @live_weights.setter
    def live_weights(self, v): self.state[self.profile]["live_weights"] = v

    # ── FASE 0: configuración de umbrales ────────────────────────────────────
    def _show_config_screen(self):
        for w in self.winfo_children():
            w.destroy()
        wrap = tk.Frame(self, bg=C["bg"]); wrap.pack(fill="both", expand=True)
        # cabecera
        head = tk.Frame(wrap, bg=C["card"]); head.pack(fill="x")
        tk.Label(head, text="SOCIAREM · Configuración inicial",
                 font=("Helvetica Neue", 15, "bold"), bg=C["card"], fg=C["text"]).pack(anchor="w", padx=24, pady=(20, 2))
        tk.Label(head, text="Define los umbrales que convierten valores numéricos en señales de riesgo. "
                            "Estos umbrales se aplican a todos los perfiles.",
                 font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"],
                 wraplength=900, justify="left").pack(anchor="w", padx=24, pady=(0, 18))

        body = tk.Frame(wrap, bg=C["bg"]); body.pack(fill="both", expand=True, padx=24, pady=16)
        self._thr_entries = {}
        thr_specs = [
            ("pobreza",      "Umbral de pobreza relativa (I1/I2)", "€/mes equivalente", "Renta por debajo → bajo umbral de pobreza"),
            ("renta_riesgo", "Renta de riesgo alto (I1)",          "€/mes",            "Renta por debajo → riesgo económico alto"),
            ("carga",        "Carga energética alta (I3)",          "% de la renta",    "Gasto energético / renta por encima → carga alta"),
            ("consumo_elec", "Consumo eléctrico alto (I5)",         "kWh/mes",          "Consumo por encima → elevado"),
            ("consumo_gas",  "Consumo no eléctrico alto (I6)",      "kWh/mes",          "Consumo por encima → elevado"),
            ("infra_elec",   "Infraconsumo eléctrico (I5/I8)",      "kWh/mes",          "Consumo por debajo → posible infraconsumo (P3)"),
            ("infra_gas",    "Infraconsumo no eléctrico (I6/I8)",   "kWh/mes",          "Consumo por debajo → posible infraconsumo (P3)"),
            ("ahorros",      "Ahorros mínimos (I21)",               "meses de renta",   "Ahorros por debajo → sin colchón financiero"),
            ("estabilidad",  "Estabilidad residencial (I25)",       "años de residencia","Por debajo → situación inestable"),
            ("territorial",  "Riesgo territorial alto (I18)",       "índice 0-100",     "Índice por encima → zona desfavorecida"),
            ("acceso",       "Acceso deficiente a servicios (I19)", "minutos",          "Tiempo por encima → mal acceso"),
        ]
        grid = tk.Frame(body, bg=C["bg"]); grid.pack(anchor="w")
        for i, (key, label, unit, expl) in enumerate(thr_specs):
            row = tk.Frame(grid, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.grid(row=i//2, column=i%2, sticky="ew", padx=(0,10) if i%2==0 else 0, pady=4, ipadx=2)
            grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1)
            inn = tk.Frame(row, bg=C["card"]); inn.pack(fill="x", padx=12, pady=8)
            tk.Label(inn, text=label, font=("Helvetica Neue", 10, "bold"),
                     bg=C["card"], fg=C["text"]).pack(anchor="w")
            tk.Label(inn, text=expl, font=("Helvetica Neue", 8),
                     bg=C["card"], fg=C["muted"], wraplength=440, justify="left").pack(anchor="w", pady=(0,4))
            er = tk.Frame(inn, bg=C["card"]); er.pack(anchor="w")
            var = tk.StringVar(value=str(self.thresholds[key]))
            ent = tk.Entry(er, textvariable=var, font=("Helvetica Neue", 11), width=10,
                           relief="solid", bd=1, bg=C["bg"], fg=C["text"])
            ent.pack(side="left", ipady=2)
            tk.Label(er, text=unit, font=("Helvetica Neue", 9),
                     bg=C["card"], fg=C["muted"]).pack(side="left", padx=(8,0))
            self._thr_entries[key] = var

        # pie con botones
        foot = tk.Frame(wrap, bg=C["card"]); foot.pack(fill="x", side="bottom")
        self._cfg_err = tk.Label(foot, text="", font=("Helvetica Neue", 9),
                                 bg=C["card"], fg=C["danger"])
        self._cfg_err.pack(side="left", padx=24)
        tk.Button(foot, text="Restablecer valores por defecto",
                  font=("Helvetica Neue", 9), bg=C["card2"], fg=C["muted"],
                  relief="flat", cursor="hand2", padx=12, pady=7,
                  command=self._reset_thresholds).pack(side="right", padx=(0,8), pady=12)
        tk.Button(foot, text="Comenzar evaluación  →",
                  font=("Helvetica Neue", 11, "bold"), bg=C["accent"], fg="#FFFFFF",
                  relief="flat", cursor="hand2", padx=18, pady=8,
                  command=self._apply_config).pack(side="right", padx=(0,24), pady=12)

    def _reset_thresholds(self):
        for k, v in DEFAULT_THRESHOLDS.items():
            self._thr_entries[k].set(str(v))

    def _apply_config(self):
        new = {}
        for k, var in self._thr_entries.items():
            try:
                val = float(var.get().replace(",", "."))
                # los enteros se quedan enteros
                if k in ("pobreza","renta_riesgo","consumo_elec","consumo_gas",
                         "infra_elec","infra_gas","ahorros","estabilidad","territorial","acceso"):
                    val = int(val)
                new[k] = val
            except ValueError:
                self._cfg_err.configure(text=f"Valor inválido en '{k}'. Revisa los campos.")
                return
        self.thresholds = new
        self.configured = True
        self._build_main()
        self._select(0)

    # ── UI principal ─────────────────────────────────────────────────────────
    def _build_main(self):
        for w in self.winfo_children():
            w.destroy()
        self.sidebar = tk.Frame(self, bg=C["card"], width=244)
        self.sidebar.pack(side="left", fill="y"); self.sidebar.pack_propagate(False)
        self._build_sidebar()

        self.right = tk.Frame(self, bg=C["bg"]); self.right.pack(side="left", fill="both", expand=True)

        # barra de perfil
        self.topbar = tk.Frame(self.right, bg=C["card"], height=46); self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        tk.Label(self.topbar, text="Perfil:", font=("Helvetica Neue", 10),
                 bg=C["card"], fg=C["muted"]).pack(side="left", padx=(16, 8))
        self.profile_btns = {}
        for p in PROFILES:
            b = tk.Button(self.topbar, text=p, font=("Helvetica Neue", 10, "bold"),
                          relief="flat", cursor="hand2", padx=12, pady=5,
                          command=lambda pr=p: self._switch_profile(pr))
            b.pack(side="left", padx=(0, 4), pady=7)
            Tooltip(b, PROFILES[p]["name"])
            self.profile_btns[p] = b
        tk.Button(self.topbar, text="⚙ Umbrales", font=("Helvetica Neue", 9),
                  bg=C["card2"], fg=C["muted"], relief="flat", cursor="hand2", padx=10, pady=5,
                  command=self._show_config_screen).pack(side="right", padx=(0,12), pady=7)

        # header hogar
        self.hdr = tk.Frame(self.right, bg=C["card"], height=86); self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        tk.Frame(self.right, bg=C["border"], height=1).pack(fill="x")
        self.lbl_id    = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"])
        self.lbl_name  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 16, "bold"), bg=C["card"], fg=C["text"])
        self.lbl_comp  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"])
        self.lbl_desc  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"],
                                  wraplength=760, justify="left")
        self.lbl_profiles = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"])
        self.lbl_id.place(x=22, y=7); self.lbl_name.place(x=22, y=21)
        self.lbl_comp.place(x=22, y=45); self.lbl_desc.place(x=22, y=61); self.lbl_profiles.place(x=22, y=74)
        nav = tk.Frame(self.hdr, bg=C["card"]); nav.place(relx=1.0, x=-14, y=30, anchor="ne")
        tk.Button(nav, text="←", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2", command=lambda: self._nav(-1)).pack(side="left")
        self.lbl_nav = tk.Label(nav, text="", font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"])
        self.lbl_nav.pack(side="left", padx=4)
        tk.Button(nav, text="→", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2", command=lambda: self._nav(1)).pack(side="left")

        # canvas scroll
        self._canvas = tk.Canvas(self.right, bg=C["bg"], highlightthickness=0)
        vsb = tk.Scrollbar(self.right, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); self._canvas.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(self._canvas, bg=C["bg"])
        self._cwin = self._canvas.create_window((0,0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda e: (
            self._canvas.configure(scrollregion=self._canvas.bbox("all")),
            self._canvas.itemconfig(self._cwin, width=self._canvas.winfo_width())))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._cwin, width=e.width))
        self._canvas.bind_all("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._canvas.bind_all("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>",   lambda e: self._canvas.yview_scroll(1, "units"))

    def _nav(self, d):
        if not self.filtered_idx: return
        pos = self.filtered_idx.index(self.current_idx) if self.current_idx in self.filtered_idx else 0
        self._select(self.filtered_idx[(pos + d) % len(self.filtered_idx)])

    def _switch_profile(self, p):
        self.profile = p
        self._select(self.current_idx)

    def _build_sidebar(self):
        for w in self.sidebar.winfo_children(): w.destroy()
        app = self
        top = tk.Frame(self.sidebar, bg=C["card"]); top.pack(side="top", fill="x")
        tk.Label(top, text="SOCIAREM", font=("Helvetica Neue", 11, "bold"),
                 bg=C["card"], fg=C["accent"]).pack(anchor="w", padx=16, pady=(16, 0))
        tk.Label(top, text="Piloto Messina", font=("Helvetica Neue", 9),
                 bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(0, 6))
        tk.Frame(top, bg=C["border"], height=1).pack(fill="x")
        ptxt = f"{self.profile} · FASE {self.phase}" + (" · Etiquetado" if self.phase==1 else " · Ajuste")
        tk.Label(top, text=ptxt, font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=PROFILE_COLORS[self.profile]).pack(anchor="w", padx=16, pady=(6, 4))
        sf = tk.Frame(top, bg=C["card"]); sf.pack(fill="x", padx=12, pady=(0, 4))
        self._search_var = tk.StringVar(value=self.search_text)
        tk.Entry(sf, textvariable=self._search_var, font=("Helvetica Neue", 9),
                 relief="solid", bd=1, bg=C["bg"], fg=C["text"]).pack(fill="x", ipady=3)
        self._search_var.trace_add("write", lambda *a: self._on_search())
        tk.Label(top, text="Buscar por ID, nombre o perfil", font=("Helvetica Neue", 7),
                 bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=14, pady=(0,4))

        bottom = tk.Frame(self.sidebar, bg=C["card"]); bottom.pack(side="bottom", fill="x")
        tk.Frame(bottom, bg=C["border"], height=1).pack(fill="x")
        if self.phase == 1:
            af = tk.Frame(bottom, bg=C["card"]); af.pack(fill="x", padx=8, pady=(6,2))
            tk.Button(af, text="▶ Auto-demo", font=("Helvetica Neue", 9, "bold"),
                      bg=C["accent"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=8, pady=6,
                      command=lambda a=app: a._auto_assign(True)).pack(side="left", fill="x", expand=True, padx=(0,3))
            tk.Button(af, text="⚡ Instant.", font=("Helvetica Neue", 9),
                      bg=C["card2"], fg=C["text"], relief="flat", cursor="hand2", padx=8, pady=6,
                      command=lambda a=app: a._auto_assign(False)).pack(side="left", fill="x", expand=True, padx=(3,0))
            tk.Button(bottom, text="⚙ Optimizar pesos", font=("Helvetica Neue", 10, "bold"),
                      bg=C["accent2"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=12, pady=7,
                      command=lambda a=app: a._run_optimization()).pack(fill="x", padx=8, pady=(2,4))
            self.progress_lbl = tk.Label(bottom, text=getattr(self,"_progress_text",""),
                                         font=("Helvetica Neue", 9), bg=C["card"],
                                         fg=getattr(self,"_progress_color",C["muted"]), wraplength=208)
            self.progress_lbl.pack(anchor="w", padx=12, pady=(0,8))
        else:
            tk.Button(bottom, text="⬇ Exportar resultados", font=("Helvetica Neue", 9, "bold"),
                      bg=C["accent"], fg="#FFFFFF", relief="flat", cursor="hand2", padx=10, pady=6,
                      command=lambda a=app: a._export_dialog()).pack(fill="x", padx=8, pady=(6,3))
            tk.Button(bottom, text="← Volver a fase 1", font=("Helvetica Neue", 9),
                      bg=C["card2"], fg=C["muted"], relief="flat", cursor="hand2", padx=10, pady=5,
                      command=lambda a=app: a._back_to_phase1()).pack(fill="x", padx=8, pady=(0,6))

        sbc = tk.Canvas(self.sidebar, bg=C["card"], highlightthickness=0)
        sbv = tk.Scrollbar(self.sidebar, orient="vertical", command=sbc.yview)
        sbc.configure(yscrollcommand=sbv.set); sbv.pack(side="right", fill="y"); sbc.pack(side="left", fill="both", expand=True)
        sff = tk.Frame(sbc, bg=C["card"]); sw = sbc.create_window((0,0), window=sff, anchor="nw")
        sff.bind("<Configure>", lambda e: (sbc.configure(scrollregion=sbc.bbox("all")),
                                           sbc.itemconfig(sw, width=sbc.winfo_width())))
        sbc.bind("<Configure>", lambda e: sbc.itemconfig(sw, width=e.width))
        def _s(e): sbc.yview_scroll(-1*(e.delta//120),"units")
        def _su(e): sbc.yview_scroll(-1,"units")
        def _sd(e): sbc.yview_scroll(1,"units")
        for wd in (sbc, sff): wd.bind("<MouseWheel>",_s); wd.bind("<Button-4>",_su); wd.bind("<Button-5>",_sd)
        self.sidebar_btns = {}
        for i in self.filtered_idx:
            hh = HOUSEHOLDS[i]; extra, dot = "", C["muted"]
            if self.phase == 2 and self.opt_weights:
                pct = int(score(hh, self._current_weights(), self.profile, self.thresholds)*100)
                extra = f"  {pct}%"
                dot = C["danger"] if pct>=65 else (C["warn"] if pct>=40 else C["ok"])
            elif self.phase == 1:
                lbl = self.expert_labels.get(hh["id"])
                if lbl==1: dot=C["danger"]
                elif lbl==0: dot=C["ok"]
            fg = dot if self.expert_labels.get(hh["id"]) is not None else C["text"]
            btn = tk.Button(sff, text=f"{hh['id']}  {hh['nombre']}{extra}", font=("Helvetica Neue", 9),
                            anchor="w", padx=10, pady=4, relief="flat", cursor="hand2",
                            bg=C["sel"] if i==self.current_idx else C["card"], fg=fg,
                            activebackground=C["sel"], activeforeground=C["text"],
                            command=lambda idx=i, a=app: a._select(idx))
            btn.pack(fill="x", padx=4)
            for ev, fn in [("<MouseWheel>",_s),("<Button-4>",_su),("<Button-5>",_sd)]: btn.bind(ev, fn)
            self.sidebar_btns[i] = btn

    def _on_search(self):
        self.search_text = self._search_var.get().strip().lower()
        if not self.search_text:
            self.filtered_idx = list(range(len(HOUSEHOLDS)))
        else:
            t = self.search_text
            self.filtered_idx = [i for i,hh in enumerate(HOUSEHOLDS)
                                 if t in hh["id"].lower() or t in hh["nombre"].lower()
                                 or any(t in p.lower() for p in self._hh_profiles(hh))]
        self._build_sidebar()

    def _hh_profiles(self, hh):
        return [p for p in PROFILES if hh["gt"][p] == 1]

    def _set_progress(self, text, color):
        self._progress_text = text; self._progress_color = color
        if hasattr(self, "progress_lbl") and self.progress_lbl.winfo_exists():
            self.progress_lbl.configure(text=text, fg=color)

    def _select(self, idx):
        self.current_idx = idx
        for p, b in self.profile_btns.items():
            b.configure(bg=PROFILE_COLORS[p] if p==self.profile else C["card2"],
                        fg="#FFFFFF" if p==self.profile else C["muted"])
        self._build_sidebar()
        hh = HOUSEHOLDS[idx]
        self.lbl_id.configure(text=hh["id"])
        self.lbl_name.configure(text=f"{hh['nombre']}  ·  {hh['edad']} años")
        self.lbl_comp.configure(text=hh["composicion"])
        self.lbl_desc.configure(text=hh["desc"])
        pos = self.filtered_idx.index(idx)+1 if idx in self.filtered_idx else 0
        self.lbl_nav.configure(text=f"{pos}/{len(self.filtered_idx)}")
        pfs = self._hh_profiles(hh)
        self.lbl_profiles.configure(text=f"Vulnerable en: {'  '.join(pfs)}" if pfs else "Sin vulnerabilidad de referencia")
        for w in self.content.winfo_children(): w.destroy()
        self._canvas.yview_moveto(0)
        if self.phase == 1: self._render_phase1(hh)
        else: self._render_phase2(hh)

    def _current_weights(self):
        if self.live_weights:
            raw = {k: max(0.001, self.live_weights[k].get()) for k in PROFILES[self.profile]["weight_keys"]}
            t = sum(raw.values()) or 1
            return {k: v/t for k, v in raw.items()}
        return self.opt_weights or PROFILES[self.profile]["init_weights"].copy()

    def _auto_assign(self, animated=False):
        if animated: self._auto_step(0)
        else:
            for hh in HOUSEHOLDS: self.expert_labels[hh["id"]] = hh["gt"][self.profile]
            self._set_progress(f"{len(HOUSEHOLDS)}/{len(HOUSEHOLDS)} etiquetados\n¡Listo!", C["ok"])
            self._select(self.current_idx)

    def _auto_step(self, i):
        if i >= len(HOUSEHOLDS):
            self._set_progress(f"{len(HOUSEHOLDS)}/{len(HOUSEHOLDS)} etiquetados\n¡Listo!", C["ok"])
            self._select(0); return
        hh = HOUSEHOLDS[i]; self.expert_labels[hh["id"]] = hh["gt"][self.profile]
        self.current_idx = i; self.filtered_idx = list(range(len(HOUSEHOLDS)))
        self._select(i)
        self._set_progress(f"Auto-demo: {i+1}/{len(HOUSEHOLDS)}", C["accent"])
        self.after(160, lambda: self._auto_step(i+1))

    def _set_expert(self, hid, val):
        was = hid not in self.expert_labels
        self.expert_labels[hid] = val
        n, nt = len(self.expert_labels), len(HOUSEHOLDS)
        self._set_progress(f"{n}/{nt} etiquetados" + ("\n¡Listo!" if n==nt else ""),
                           C["ok"] if n==nt else C["muted"])
        if was and self.current_idx in self.filtered_idx:
            pos = self.filtered_idx.index(self.current_idx)
            if pos < len(self.filtered_idx)-1:
                self._select(self.filtered_idx[pos+1]); return
        self._select(self.current_idx)

    def _run_optimization(self):
        if len(self.expert_labels) < 5:
            self._set_progress("Necesitas ≥ 5 hogares etiquetados.", C["warn"]); return
        self._set_progress("Optimizando…", C["accent"]); self.update()
        full = {hh["id"]: self.expert_labels.get(hh["id"], hh["gt"][self.profile]) for hh in HOUSEHOLDS}
        self.opt_weights = optimize_weights(full, self.profile, self.thresholds)
        self.phase = 2
        self.live_weights = {k: tk.DoubleVar(value=round(self.opt_weights[k]*100,1))
                             for k in PROFILES[self.profile]["weight_keys"]}
        self._select(self.current_idx)

    def _back_to_phase1(self):
        self.phase = 1; self.live_weights = None
        self._select(self.current_idx)

    # ─────────────────────────────────────────────────────────────────────────
    # FASE 1  (tarjetas de indicadores en color NEUTRO, sin verde/rojo)
    # ─────────────────────────────────────────────────────────────────────────
    def _render_phase1(self, hh):
        self.content.configure(bg=C["bg"]); self._canvas.configure(bg=C["bg"])
        px = 20
        self._render_profile_summary(self.content, px)
        tk.Label(self.content, text=f"Indicadores · {PROFILES[self.profile]['name']}",
                 font=("Helvetica Neue", 12, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(14, 6))
        keys = PROFILES[self.profile]["display_keys"]
        grid = tk.Frame(self.content, bg=C["bg"]); grid.pack(fill="x", padx=px)
        ncols = 4
        for c in range(ncols): grid.columnconfigure(c, weight=1)
        for i, k in enumerate(keys):
            self._ind_card(grid, k, hh, i//ncols, i%ncols, ncols)

        tk.Label(self.content, text="Validación experto",
                 font=("Helvetica Neue", 12, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(20, 6))
        vcard = tk.Frame(self.content, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        vcard.pack(fill="x", padx=px, pady=(0, 16))
        vc = tk.Frame(vcard, bg=C["card"]); vc.pack(fill="x", padx=16, pady=14)
        tk.Label(vc, text=PROFILES[self.profile]["question"], font=("Helvetica Neue", 11),
                 bg=C["card"], fg=C["text"]).pack(anchor="w")
        tk.Label(vc, text="Etiqueta usada para optimizar los pesos del modelo.",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", pady=(2, 10))
        brow = tk.Frame(vc, bg=C["card"]); brow.pack(anchor="w")
        cur = self.expert_labels.get(hh["id"])
        for val, lbl, bg_a, fg_a in [
            (1, f"SÍ – vulnerable {self.profile}", C["danger_dim"], C["danger"]),
            (0, "NO – no vulnerable",              C["ok_dim"],     C["ok"]),
        ]:
            active = cur == val
            tk.Button(brow, text=lbl, font=("Helvetica Neue", 11, "bold" if active else "normal"),
                      bg=bg_a if active else C["card2"], fg=fg_a if active else C["muted"],
                      highlightbackground=fg_a if active else C["border"], highlightthickness=2 if active else 1,
                      relief="flat", cursor="hand2", padx=18, pady=8,
                      command=lambda v=val, hid=hh["id"]: self._set_expert(hid, v)).pack(side="left", padx=(0,10))
        n, nt = len(self.expert_labels), len(HOUSEHOLDS)
        st = f"{n}/{nt} hogares etiquetados" + ("  ·  ¡Listo para optimizar!" if n==nt else "")
        tk.Label(vc, text=st, font=("Helvetica Neue", 9), bg=C["card"],
                 fg=C["ok"] if n==nt else C["muted"]).pack(anchor="w", pady=(10, 0))

    def _render_profile_summary(self, parent, px):
        card = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        card.pack(fill="x", padx=px, pady=(16, 0))
        ci = tk.Frame(card, bg=C["card"]); ci.pack(fill="x", padx=16, pady=10)
        tk.Label(ci, text="Distribución de vulnerabilidad por perfil (etiqueta de referencia)",
                 font=("Helvetica Neue", 10, "bold"), bg=C["card"], fg=C["text"]).pack(anchor="w")
        row = tk.Frame(ci, bg=C["card"]); row.pack(fill="x", pady=(8, 0))
        for p in PROFILES:
            n = sum(1 for h in HOUSEHOLDS if h["gt"][p] == 1)
            cell = tk.Frame(row, bg=C["card"]); cell.pack(side="left", expand=True, fill="x")
            tk.Label(cell, text=str(n), font=("Helvetica Neue", 20, "bold"),
                     bg=C["card"], fg=PROFILE_COLORS[p]).pack()
            tk.Label(cell, text=f"{p} · {PROFILES[p]['short']}", font=("Helvetica Neue", 8),
                     bg=C["card"], fg=C["muted"]).pack()

    def _ind_card(self, parent, k, hh, row, col, ncols):
        d = INDICATOR_DEFS[k]
        is_pri = d["role"] == "primario"
        bbg = C["badge_pri"] if is_pri else C["badge_sec"]
        bfg = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]
        value = d["display_t"](hh, self.thresholds) if d.get("derived") else d["display"](hh)
        note = d["note"](self.thresholds)
        # SIN verde/rojo: borde y valor en color neutro
        f = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        f.grid(row=row, column=col, padx=(0,6) if col<ncols-1 else 0, pady=(0,6), sticky="nsew")
        inn = tk.Frame(f, bg=C["card"]); inn.pack(fill="both", expand=True, padx=10, pady=8)
        top = tk.Frame(inn, bg=C["card"]); top.pack(fill="x")
        tk.Label(top, text=k, font=("Helvetica Neue", 8, "bold"), bg=bbg, fg=bfg, padx=5, pady=1).pack(side="left")
        tk.Label(top, text="PRI" if is_pri else "SEC", font=("Helvetica Neue", 7),
                 bg=C["card"], fg=bfg).pack(side="left", padx=(5, 0))
        info = tk.Label(top, text="ⓘ", font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"], cursor="hand2")
        info.pack(side="right")
        Tooltip(info, f"{d['long']}\n\n{d['definition']}\n\nFuente: {d['source']}")
        tk.Label(inn, text=d["name"], font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=C["text"], anchor="w").pack(fill="x", pady=(3, 0))
        tk.Label(inn, text=value, font=("Helvetica Neue", 16, "bold"),
                 bg=C["card"], fg=C["neutral"], anchor="w").pack(fill="x", pady=(1, 0))
        tk.Label(inn, text=note, font=("Helvetica Neue", 8),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")
        tk.Frame(inn, bg=C["border"], height=1).pack(fill="x", pady=(5, 3))
        tk.Label(inn, text=d["source"], font=("Helvetica Neue", 7),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")

    # ─────────────────────────────────────────────────────────────────────────
    # FASE 2
    # ─────────────────────────────────────────────────────────────────────────
    def _score_style(self, pct):
        if pct >= 65:   return C["danger"], C["danger_dim"], "ALTA"
        elif pct >= 40: return C["warn"],   C["warn_dim"],   "MEDIA"
        else:           return C["ok"],      C["ok_dim"],     "BAJA"

    def _render_phase2(self, hh):
        bg = C["phase2_bg"]; self.content.configure(bg=bg); self._canvas.configure(bg=bg)
        px = 20; T = self.thresholds
        w = self._current_weights(); s = score(hh, w, self.profile, T); pct = int(s*100)
        sc, sd, sl = self._score_style(pct)
        banner = tk.Frame(self.content, bg=sd, highlightbackground=sc, highlightthickness=1)
        banner.pack(fill="x", padx=px, pady=(18,10))
        bi = tk.Frame(banner, bg=sd); bi.pack(fill="x", padx=18, pady=14)
        tk.Label(bi, text=f"VULNERABILIDAD {self.profile} · SCORE", font=("Helvetica Neue", 9, "bold"),
                 bg=sd, fg=sc).pack(anchor="w")
        rs = tk.Frame(bi, bg=sd); rs.pack(fill="x", pady=(4,0))
        self._score_lbl = tk.Label(rs, text=f"{pct}%", font=("Helvetica Neue", 40, "bold"), bg=sd, fg=sc)
        self._score_lbl.pack(side="left")
        self._score_level_lbl = tk.Label(rs, text=f"  {sl}", font=("Helvetica Neue", 22, "bold"), bg=sd, fg=sc)
        self._score_level_lbl.pack(side="left")
        pred = "VULNERABLE" if s >= self.decision_threshold else "NO VULNERABLE"
        self._pred_lbl = tk.Label(rs, text=f"   → clasificado: {pred}", font=("Helvetica Neue", 11), bg=sd, fg=sc)
        self._pred_lbl.pack(side="left")
        bo = tk.Frame(bi, bg=C["border"], height=8); bo.pack(fill="x", pady=(10,0))
        self._bar_inner = tk.Frame(bo, bg=sc, height=8); self._bar_inner.place(x=0, y=0, relwidth=min(1.0,s))
        self._banner_frame, self._banner_inner = banner, bi

        self._render_metrics(self.content, w, px)

        # umbral de decisión
        tc = tk.Frame(self.content, bg=C["phase2_card"], highlightbackground=C["border"], highlightthickness=1)
        tc.pack(fill="x", padx=px, pady=(0,10))
        tci = tk.Frame(tc, bg=C["phase2_card"]); tci.pack(fill="x", padx=16, pady=10)
        tk.Label(tci, text="Umbral de decisión", font=("Helvetica Neue", 10, "bold"),
                 bg=C["phase2_card"], fg=C["text"]).pack(side="left")
        self._thr_var2 = tk.DoubleVar(value=self.decision_threshold*100)
        tk.Scale(tci, variable=self._thr_var2, from_=10, to=90, resolution=1, orient="horizontal", length=240,
                 bg=C["phase2_card"], fg=C["text"], troughcolor=C["slider_bg"], activebackground=C["accent"],
                 highlightthickness=0, bd=0, sliderrelief="flat",
                 command=lambda v: self._on_threshold_change()).pack(side="left", padx=(10,0))
        self._thr_lbl2 = tk.Label(tci, text=f"{int(self.decision_threshold*100)}%", font=("Helvetica Neue", 11, "bold"),
                                  bg=C["phase2_card"], fg=C["accent"], width=5)
        self._thr_lbl2.pack(side="left", padx=(8,0))
        tk.Label(tci, text="score ≥ umbral → clasificado vulnerable", font=("Helvetica Neue", 8),
                 bg=C["phase2_card"], fg=C["muted"]).pack(side="left", padx=(10,0))

        tk.Label(self.content, text="Indicadores · contribución al score", font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(8,6))
        for k in PROFILES[self.profile]["display_keys"]:
            self._ind_row_phase2(self.content, hh, k, w, px)

        tk.Label(self.content, text="Pesos del modelo", font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20,6))
        wc = tk.Frame(self.content, bg=C["phase2_card"], highlightbackground=C["accent2"], highlightthickness=1)
        wc.pack(fill="x", padx=px, pady=(0,10))
        wci = tk.Frame(wc, bg=C["phase2_card"]); wci.pack(fill="x", padx=16, pady=14)
        tk.Label(wci, text="Calculados por SLSQP (scipy) con regularización L2 · log-loss sobre etiquetas experto.",
                 font=("Helvetica Neue", 9), bg=C["phase2_card"], fg=C["muted"]).pack(anchor="w", pady=(0,10))
        self._w_val_lbls = {}; self._w_delta_lbls = {}
        for k in PROFILES[self.profile]["weight_keys"]:
            self._weight_slider_row(wci, k, hh)

        tk.Label(self.content, text="Todos los hogares · score actual", font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20,6))
        tt = tk.Frame(self.content, bg=C["phase2_card"], highlightbackground=C["border"], highlightthickness=1)
        tt.pack(fill="x", padx=px, pady=(0,20))
        tti = tk.Frame(tt, bg=C["phase2_card"]); tti.pack(fill="x", padx=14, pady=12)
        self._all_score_labels = {}; self._all_bar_frames = {}; self._all_check_lbls = {}
        for h in HOUSEHOLDS:
            self._table_row(tti, h, w)

    def _render_metrics(self, parent, w, px):
        m = compute_metrics(w, self.profile, self.expert_labels, self.decision_threshold, self.thresholds)
        card = tk.Frame(parent, bg=C["phase2_card"], highlightbackground=C["accent"], highlightthickness=1)
        card.pack(fill="x", padx=px, pady=(0,10))
        ci = tk.Frame(card, bg=C["phase2_card"]); ci.pack(fill="x", padx=16, pady=12)
        tk.Label(ci, text="Calidad del modelo (sobre etiquetas experto)", font=("Helvetica Neue", 10, "bold"),
                 bg=C["phase2_card"], fg=C["text"]).pack(anchor="w")
        row = tk.Frame(ci, bg=C["phase2_card"]); row.pack(fill="x", pady=(8,0))
        self._metric_lbls = {}
        for key, lab in [("accuracy","Exactitud"),("precision","Precisión"),("recall","Sensibilidad"),("f1","F1")]:
            cell = tk.Frame(row, bg=C["phase2_card"]); cell.pack(side="left", expand=True, fill="x")
            vl = tk.Label(cell, text=f"{m[key]*100:.0f}%", font=("Helvetica Neue", 18, "bold"),
                          bg=C["phase2_card"], fg=C["accent"]); vl.pack()
            tk.Label(cell, text=lab, font=("Helvetica Neue", 8), bg=C["phase2_card"], fg=C["muted"]).pack()
            self._metric_lbls[key] = vl
        cm = tk.Frame(ci, bg=C["phase2_card"]); cm.pack(anchor="w", pady=(10,0))
        self._cm_lbls = {}
        for key, lab in [("tp","VP"),("fp","FP"),("fn","FN"),("tn","VN")]:
            cell = tk.Frame(cm, bg=C["phase2_card"]); cell.pack(side="left", padx=(0,14))
            l = tk.Label(cell, text=str(m[key]), font=("Helvetica Neue", 13, "bold"),
                         bg=C["phase2_card"], fg=C["neutral"]); l.pack(side="left")
            tk.Label(cell, text=f" {lab}", font=("Helvetica Neue", 9), bg=C["phase2_card"], fg=C["muted"]).pack(side="left")
            self._cm_lbls[key] = l

    def _table_row(self, parent, h, w):
        T = self.thresholds
        hs = score(h, w, self.profile, T); hpct = int(hs*100)
        hc = C["danger"] if hpct>=65 else (C["warn"] if hpct>=40 else C["ok"])
        lbl = self.expert_labels.get(h["id"], h["gt"][self.profile])
        is_cur = h["id"] == HOUSEHOLDS[self.current_idx]["id"]
        rb = C["sel"] if is_cur else C["phase2_card"]
        rf = tk.Frame(parent, bg=rb, highlightbackground=C["accent"] if is_cur else C["border"],
                      highlightthickness=1 if is_cur else 0); rf.pack(fill="x", pady=2)
        ri = tk.Frame(rf, bg=rb); ri.pack(fill="x", padx=10, pady=5)
        tk.Label(ri, text=h["id"], font=("Helvetica Neue", 9, "bold"), bg=rb, fg=C["muted"], width=8).pack(side="left")
        tk.Label(ri, text=h["nombre"], font=("Helvetica Neue", 9), bg=rb, fg=C["text"], width=10, anchor="w").pack(side="left")
        pf = " ".join(self._hh_profiles(h)) if self._hh_profiles(h) else "—"
        tk.Label(ri, text=pf, font=("Helvetica Neue", 8), bg=rb, fg=C["muted"], width=18, anchor="w").pack(side="left")
        tk.Label(ri, text="vuln." if lbl==1 else "no vuln.", font=("Helvetica Neue", 9),
                 bg=rb, fg=C["neutral"], width=8).pack(side="left")
        bf = tk.Frame(ri, bg=C["border"], height=10, width=120); bf.pack(side="left", padx=(4,0)); bf.pack_propagate(False)
        bfill = tk.Frame(bf, bg=hc, height=10); bfill.place(x=0, y=0, width=int(120*min(1.0,hs)))
        self._all_bar_frames[h["id"]] = (bf, bfill)
        sl = tk.Label(ri, text=f"{hpct}%", font=("Helvetica Neue", 10, "bold"), bg=rb, fg=hc, width=5)
        sl.pack(side="left", padx=(5,0)); self._all_score_labels[h["id"]] = (sl, rb)
        corr = (lbl==1 and hs>=self.decision_threshold) or (lbl==0 and hs<self.decision_threshold)
        ck = tk.Label(ri, text="✓" if corr else "✗", font=("Helvetica Neue", 12, "bold"),
                      bg=rb, fg=C["ok"] if corr else C["danger"]); ck.pack(side="left", padx=(3,0))
        self._all_check_lbls[h["id"]] = (ck, rb)

    def _ind_row_phase2(self, parent, hh, k, weights, px):
        T = self.thresholds; d = INDICATOR_DEFS[k]
        is_derived = d.get("derived", False)
        wk = PROFILES[self.profile]["weight_keys"]
        contrib = (weights.get(k,0) * d["norm"](hh, T)) if (k in wk and not is_derived) else 0
        total_w = sum(weights.values()) or 1
        cpct = int((contrib/total_w)*100)
        value = d["display_t"](hh, T) if is_derived else d["display"](hh)
        # SIN verde/rojo: fondo neutro
        rf = tk.Frame(parent, bg=C["phase2_card"], highlightbackground=C["border"], highlightthickness=1)
        rf.pack(fill="x", padx=px, pady=(0,5))
        ri = tk.Frame(rf, bg=C["phase2_card"]); ri.pack(fill="x", padx=14, pady=8)
        is_pri = d["role"]=="primario"
        bbg = C["badge_pri"] if is_pri else C["badge_sec"]; bfg = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]
        left = tk.Frame(ri, bg=C["phase2_card"]); left.pack(side="left")
        tk.Label(left, text=k, font=("Helvetica Neue", 8, "bold"), bg=bbg, fg=bfg, padx=5, pady=1).pack(anchor="w")
        tk.Label(left, text=d["name"], font=("Helvetica Neue", 9), bg=C["phase2_card"], fg=C["muted"]).pack(anchor="w", pady=(2,0))
        tk.Label(ri, text=value, font=("Helvetica Neue", 15, "bold"), bg=C["phase2_card"], fg=C["neutral"],
                 width=14, anchor="w").pack(side="left", padx=(14,0))
        tk.Label(ri, text=d["note"](T), font=("Helvetica Neue", 9), bg=C["phase2_card"], fg=C["muted"],
                 width=22, anchor="w").pack(side="left")
        if not is_derived:
            cb = tk.Frame(ri, bg=C["border"], height=8, width=100); cb.pack(side="left", padx=(6,0)); cb.pack_propagate(False)
            tk.Frame(cb, bg=C["accent2"], height=8, width=min(100, int(100*min(1.0, contrib*4)))).place(x=0, y=0)
            tk.Label(ri, text=f"+{cpct}%", font=("Helvetica Neue", 9, "bold"),
                     bg=C["phase2_card"], fg=C["accent2"], width=5).pack(side="left", padx=(5,0))
        else:
            tk.Label(ri, text="(derivado)", font=("Helvetica Neue", 8),
                     bg=C["phase2_card"], fg=C["muted"]).pack(side="left", padx=(8,0))

    def _weight_slider_row(self, parent, k, hh):
        d = INDICATOR_DEFS[k]
        row = tk.Frame(parent, bg=C["phase2_card"]); row.pack(fill="x", pady=3)
        tk.Label(row, text=d["long"], font=("Helvetica Neue", 10), bg=C["phase2_card"], fg=C["text"],
                 width=42, anchor="w").pack(side="left")
        tk.Scale(row, variable=self.live_weights[k], from_=0.1, to=60.0, resolution=0.1,
                 orient="horizontal", length=160, bg=C["phase2_card"], fg=C["text"],
                 troughcolor=C["slider_bg"], activebackground=C["accent2"], highlightthickness=0, bd=0,
                 sliderrelief="flat", command=lambda v, hh=hh: self._on_weight_change(hh)).pack(side="left", padx=(6,0))
        raw = {k2: max(0.001, self.live_weights[k2].get()) for k2 in PROFILES[self.profile]["weight_keys"]}
        t = sum(raw.values()) or 1; nv = raw[k]/t
        lv = tk.Label(row, text=f"{nv:.3f}", font=("Helvetica Neue", 10, "bold"),
                      bg=C["phase2_card"], fg=C["accent2"], width=6); lv.pack(side="left", padx=(5,0))
        self._w_val_lbls[k] = lv
        delta = nv - self.opt_weights.get(k, 0)
        dl = tk.Label(row, text=f"{'↑' if delta>0.0005 else ('↓' if delta<-0.0005 else '·')} {abs(delta):.3f}",
                      font=("Helvetica Neue", 9), bg=C["phase2_card"],
                      fg=C["warn"] if abs(delta)>0.01 else C["muted"], width=8); dl.pack(side="left", padx=(4,0))
        self._w_delta_lbls[k] = (dl, self.opt_weights.get(k, 0))

    def _refresh_live(self, hh):
        T = self.thresholds; w = self._current_weights()
        s = score(hh, w, self.profile, T); pct = int(s*100); sc, sd, sl = self._score_style(pct)
        if hasattr(self, "_score_lbl") and self._score_lbl.winfo_exists():
            self._score_lbl.configure(text=f"{pct}%", fg=sc, bg=sd)
            self._score_level_lbl.configure(text=f"  {sl}", fg=sc, bg=sd)
            self._pred_lbl.configure(text=f"   → clasificado: {'VULNERABLE' if s>=self.decision_threshold else 'NO VULNERABLE'}", fg=sc, bg=sd)
            self._banner_inner.configure(bg=sd); self._banner_frame.configure(bg=sd, highlightbackground=sc)
            self._bar_inner.configure(bg=sc); self._bar_inner.place(relwidth=min(1.0,s))
        if hasattr(self, "_w_val_lbls"):
            raw = {k: max(0.001, self.live_weights[k].get()) for k in PROFILES[self.profile]["weight_keys"]}
            t = sum(raw.values()) or 1
            for k in PROFILES[self.profile]["weight_keys"]:
                nv = raw[k]/t
                if k in self._w_val_lbls and self._w_val_lbls[k].winfo_exists():
                    self._w_val_lbls[k].configure(text=f"{nv:.3f}")
                if k in self._w_delta_lbls:
                    dl, ov = self._w_delta_lbls[k]
                    if dl.winfo_exists():
                        dd = nv - ov
                        dl.configure(text=f"{'↑' if dd>0.0005 else ('↓' if dd<-0.0005 else '·')} {abs(dd):.3f}",
                                     fg=C["warn"] if abs(dd)>0.01 else C["muted"])
        m = compute_metrics(w, self.profile, self.expert_labels, self.decision_threshold, T)
        if hasattr(self, "_metric_lbls"):
            for key in ("accuracy","precision","recall","f1"):
                if self._metric_lbls[key].winfo_exists():
                    self._metric_lbls[key].configure(text=f"{m[key]*100:.0f}%")
        if hasattr(self, "_cm_lbls"):
            for key in ("tp","fp","fn","tn"):
                if self._cm_lbls[key].winfo_exists(): self._cm_lbls[key].configure(text=str(m[key]))
        if hasattr(self, "_all_score_labels"):
            for h in HOUSEHOLDS:
                hs = score(h, w, self.profile, T); hpct = int(hs*100)
                hc = C["danger"] if hpct>=65 else (C["warn"] if hpct>=40 else C["ok"])
                if h["id"] in self._all_score_labels:
                    sl_, _ = self._all_score_labels[h["id"]]
                    if sl_.winfo_exists(): sl_.configure(text=f"{hpct}%", fg=hc)
                if h["id"] in self._all_bar_frames:
                    bf, bfill = self._all_bar_frames[h["id"]]
                    if bfill.winfo_exists(): bfill.configure(bg=hc); bfill.place(width=int(120*min(1.0,hs)))
                if h["id"] in self._all_check_lbls:
                    ck, _ = self._all_check_lbls[h["id"]]
                    lbl = self.expert_labels.get(h["id"], h["gt"][self.profile])
                    corr = (lbl==1 and hs>=self.decision_threshold) or (lbl==0 and hs<self.decision_threshold)
                    if ck.winfo_exists(): ck.configure(text="✓" if corr else "✗", fg=C["ok"] if corr else C["danger"])

    def _on_weight_change(self, hh):
        self._refresh_live(hh); self._build_sidebar()

    def _on_threshold_change(self):
        self.decision_threshold = self._thr_var2.get()/100.0
        if hasattr(self, "_thr_lbl2") and self._thr_lbl2.winfo_exists():
            self._thr_lbl2.configure(text=f"{int(self.decision_threshold*100)}%")
        self._refresh_live(HOUSEHOLDS[self.current_idx])

    def _export_dialog(self):
        T = self.thresholds; w = self._current_weights()
        m = compute_metrics(w, self.profile, self.expert_labels, self.decision_threshold, T)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(defaultextension=".json",
                initialfile=f"sociarem_{self.profile}_{ts}.json",
                filetypes=[("JSON","*.json"),("CSV","*.csv")])
        if not path: return
        rows = []
        for h in HOUSEHOLDS:
            s = score(h, w, self.profile, T)
            rows.append({"id":h["id"],"nombre":h["nombre"],
                         "perfiles_referencia":",".join(self._hh_profiles(h)),
                         "score":round(s,4),"pred":1 if s>=self.decision_threshold else 0,
                         "etiqueta_experto":self.expert_labels.get(h["id"], h["gt"][self.profile]),
                         "ground_truth":h["gt"][self.profile]})
        if path.lower().endswith(".csv"):
            with open(path,"w",newline="",encoding="utf-8") as f:
                wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
        else:
            with open(path,"w",encoding="utf-8") as f:
                json.dump({"perfil":self.profile,"perfil_nombre":PROFILES[self.profile]["name"],
                           "timestamp":datetime.now().isoformat(),"umbrales_indicadores":T,
                           "umbral_decision":self.decision_threshold,"pesos":w,"metricas":m,
                           "hogares":rows}, f, ensure_ascii=False, indent=2)
        self._set_progress(f"Guardado:\n{path.split('/')[-1]}", C["ok"])


if __name__ == "__main__":
    app = App()
    app.mainloop()