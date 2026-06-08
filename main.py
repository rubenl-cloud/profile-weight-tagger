"""
SOCIAREM – Evaluación de perfiles de vulnerabilidad energética
Proof of Concept · Piloto Messina

Perfiles implementados (separados, según D1.5):
  P1 – Vulnerabilidad económica estructural
       Primarios: I1 (ISEE), I2 (umbral pobreza, derivado de I1)
       Secundarios: I3, I4, I11, I12, I21, I25
  P2 – Vulnerabilidad por condiciones de la vivienda
       Primarios: I9 (habitabilidad), I10 (sistemas energéticos)
       Secundarios: I5 (consumo elec.), I6 (consumo no elec.), I7 (perfil horario), I20 (temp. percibida)

Fase 1: revisión de indicadores + etiquetado experto (con auto-asignar para demo)
Fase 2: pesos optimizados + sliders + métricas + umbral ajustable + export
"""

import tkinter as tk
from tkinter import filedialog
import math
import json
import csv
from datetime import datetime

# ─── Paleta clara ─────────────────────────────────────────────────────────────
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
    "P1": "#2563EB", "P2": "#D97706", "P3": "#DC2626",
    "P4": "#7C3AED", "P5": "#16A34A", "P6": "#DB2777",
}

# ─── Definición de indicadores por perfil ────────────────────────────────────
# Cada indicador: norma(hh)->[0,1], display(hh)->str, riesgo(hh)->bool,
#                 nota, fuente, rol, definicion (para tooltip F)

INDICATOR_DEFS = {
    # ─── P1 ───────────────────────────────────────────────────────────────
    "I1": {
        "name": "Renta neta equiv.",
        "long": "I1 – Renta neta mensual equivalente",
        "role": "primario",
        "source": "DS2 · ISEE",
        "definition": ("Renta neta mensual del hogar ajustada por composición mediante escala "
                       "de equivalencia (ISEE en Italia). Mide la capacidad económica efectiva "
                       "para afrontar gastos energéticos. Umbral de riesgo: < 780 €/mes."),
        "display": lambda hh: f"{hh['I1']} €/mes",
        "note": "< 780 €/mes → riesgo",
        "risk": lambda hh: hh["I1"] < 780,
        "norm": lambda hh: max(0.0, min(1.0, (1200 - hh["I1"]) / 800)),
    },
    "I2": {
        "name": "Bajo umbral pobreza",
        "long": "I2 – Hogar bajo umbral de pobreza relativa",
        "role": "primario",
        "source": "DS2 · ISEE (derivado)",
        "definition": ("Indica si la renta equivalente está por debajo del 60% de la mediana "
                       "nacional (metodología EU-SILC/ISTAT, ~1.050 €/mes equiv.). Se deriva "
                       "automáticamente del valor ISEE de I1, no se mide por separado."),
        "display": lambda hh: f"{int(hh['I1']/1050*100)}% del umbral",
        "note": "umbral: 1.050 €/mes equiv.",
        "risk": lambda hh: hh["I1"] < 1050,
        "norm": lambda hh: max(0.0, min(1.0, (1050 - hh["I1"]) / 1050)),
        "derived": True,  # no tiene peso propio
    },
    "I3": {
        "name": "Carga energética",
        "long": "I3 – Carga energética del hogar",
        "role": "secundario",
        "source": "DS4 · DS14 · facturas",
        "definition": ("Cociente entre gasto energético total (electricidad + gas) y renta neta "
                       "del hogar. Criterio LIHC adaptado: carga alta si supera el 10% de la renta."),
        "display": lambda hh: f"{hh['I3']:.1f}%",
        "note": "> 10% → riesgo",
        "risk": lambda hh: hh["I3"] > 10,
        "norm": lambda hh: max(0.0, min(1.0, (hh["I3"] - 5) / 25)),
    },
    "I4": {
        "name": "Impago / corte",
        "long": "I4 – Impago o corte de suministro",
        "role": "secundario",
        "source": "DS8 · Fundación Messina",
        "definition": ("Existencia documentada de impagos, deudas con la comercializadora o cortes "
                       "de suministro en los últimos 12 meses. Dato de autodeclaración verificada."),
        "display": lambda hh: "SÍ" if hh["I4"] else "NO",
        "note": "Últimos 12 meses",
        "risk": lambda hh: bool(hh["I4"]),
        "norm": lambda hh: float(hh["I4"]),
    },
    "I11": {
        "name": "Recibe ayudas",
        "long": "I11 – Acceso a ayudas sociales/energéticas",
        "role": "secundario",
        "source": "DS8 · DS3",
        "definition": ("Registro de si el hogar recibe ayudas públicas energéticas (bonus energia, "
                       "tarifa social) o sociales formales (RdC). Distingue vulnerabilidad reconocida."),
        "display": lambda hh: "SÍ" if hh["I11"] else "NO",
        "note": "Bonus energía / RdC",
        "risk": lambda hh: bool(hh["I11"]),
        "norm": lambda hh: float(hh["I11"]),
    },
    "I12": {
        "name": "Microcrédito",
        "long": "I12 – Acceso a microcrédito/apoyo comunitario",
        "role": "secundario",
        "source": "DS7 · DS27",
        "definition": ("Acceso efectivo a microcrédito ético, fondos de emergencia comunitarios u "
                       "otros mecanismos de apoyo financiero no bancario. La ausencia refuerza la severidad."),
        "display": lambda hh: "SÍ" if hh["I12"] else "NO",
        "note": "Sin acceso = riesgo",
        "risk": lambda hh: not bool(hh["I12"]),
        "norm": lambda hh: 1.0 - float(hh["I12"]),
    },
    "I21": {
        "name": "Ahorros líquidos",
        "long": "I21 – Ahorros líquidos o activos realizables",
        "role": "secundario",
        "source": "DS2 · DS8",
        "definition": ("Disponibilidad de ahorros líquidos o activos realizables a corto plazo para "
                       "absorber shocks económicos. Se mide en meses de renta cubiertos. <1 mes = riesgo alto."),
        "display": lambda hh: f"{hh['I21']} mes{'es' if hh['I21']!=1 else ''}" if hh["I21"]>0 else "Ninguno",
        "note": "< 1 mes → riesgo",
        "risk": lambda hh: hh["I21"] < 1,
        "norm": lambda hh: max(0.0, min(1.0, (3 - hh["I21"]) / 3)),
    },
    "I25": {
        "name": "Estabilidad residencial",
        "long": "I25 – Estabilidad administrativa y residencial",
        "role": "secundario",
        "source": "DS8",
        "definition": ("Estabilidad de la situación administrativa y residencial. Residencia inestable o "
                       "discontinuidad administrativa reducen acceso a ayudas. Se mide en años de residencia continua."),
        "display": lambda hh: f"{hh['I25']} año{'s' if hh['I25']!=1 else ''}" if hh["I25"]>0 else "< 1 año",
        "note": "< 2 años → inestable",
        "risk": lambda hh: hh["I25"] < 2,
        "norm": lambda hh: max(0.0, min(1.0, (5 - hh["I25"]) / 5)),
    },
    # ─── P2 ───────────────────────────────────────────────────────────────
    "I9": {
        "name": "Habitabilidad vivienda",
        "long": "I9 – Condiciones de habitabilidad de la vivienda",
        "role": "primario",
        "source": "DS11 · DS10",
        "definition": ("Evaluación cualitativa del estado térmico, estructural y sanitario de la vivienda "
                       "(aislamiento, humedades, riesgos para la salud). Escala ordinal: adecuada, aceptable, "
                       "pobre, crítica. Valor 0=adecuada … 3=crítica."),
        "display": lambda hh: ["Adecuada","Aceptable","Pobre","Crítica"][hh["I9"]],
        "note": "Pobre/crítica → riesgo",
        "risk": lambda hh: hh["I9"] >= 2,
        "norm": lambda hh: hh["I9"] / 3.0,
    },
    "I10": {
        "name": "Sistemas energéticos",
        "long": "I10 – Sistemas y elementos de consumo energético",
        "role": "primario",
        "source": "DS13",
        "definition": ("Caracterización de los sistemas energéticos del hogar (calefacción, ACS, refrigeración, "
                       "iluminación) y su adecuación a las necesidades. Escala: 0=eficiente/adecuado … 3=obsoleto/inadecuado."),
        "display": lambda hh: ["Eficiente","Adecuado","Deficiente","Obsoleto"][hh["I10"]],
        "note": "Deficiente/obsoleto → riesgo",
        "risk": lambda hh: hh["I10"] >= 2,
        "norm": lambda hh: hh["I10"] / 3.0,
    },
    "I5": {
        "name": "Consumo eléctrico",
        "long": "I5 – Consumo eléctrico del hogar",
        "role": "secundario",
        "source": "DS4 · DS6",
        "definition": ("Consumo eléctrico total del hogar en el periodo de referencia (kWh/mes). En P2 ayuda a "
                       "contextualizar si el gasto alto es coherente con deficiencias estructurales de la vivienda."),
        "display": lambda hh: f"{hh['I5']} kWh",
        "note": "> 350 kWh/mes → alto",
        "risk": lambda hh: hh["I5"] > 350,
        "norm": lambda hh: max(0.0, min(1.0, (hh["I5"] - 150) / 350)),
    },
    "I6": {
        "name": "Consumo no eléctrico",
        "long": "I6 – Consumo energético no eléctrico",
        "role": "secundario",
        "source": "DS14",
        "definition": ("Consumo de fuentes no eléctricas (gas, GLP, biomasa) expresado en kWh equivalentes. "
                       "Complementa I5 para evaluar la demanda térmica total del hogar."),
        "display": lambda hh: f"{hh['I6']} kWh",
        "note": "> 300 kWh/mes → alto",
        "risk": lambda hh: hh["I6"] > 300,
        "norm": lambda hh: max(0.0, min(1.0, (hh["I6"] - 100) / 350)),
    },
    "I7": {
        "name": "Perfil horario",
        "long": "I7 – Perfil de consumo eléctrico por franja horaria",
        "role": "secundario",
        "source": "DS6",
        "definition": ("Distribución del consumo eléctrico a lo largo del día. Un perfil rígido o concentrado puede "
                       "indicar limitaciones por sistemas ineficientes o inflexibles. 0=flexible … 3=muy rígido."),
        "display": lambda hh: ["Flexible","Moderado","Rígido","Muy rígido"][hh["I7"]],
        "note": "Rígido → riesgo",
        "risk": lambda hh: hh["I7"] >= 2,
        "norm": lambda hh: hh["I7"] / 3.0,
    },
    "I20": {
        "name": "Temp. percibida",
        "long": "I20 – Incapacidad percibida de mantener temperatura",
        "role": "secundario",
        "source": "DS8",
        "definition": ("Percepción del hogar sobre su incapacidad de mantener temperatura adecuada en invierno "
                       "y/o verano. Captura el malestar térmico desde el punto de vista subjetivo (EU-SILC)."),
        "display": lambda hh: "SÍ" if hh["I20"] else "NO",
        "note": "Malestar térmico declarado",
        "risk": lambda hh: bool(hh["I20"]),
        "norm": lambda hh: float(hh["I20"]),
    },
}

# ─── Configuración de cada perfil ────────────────────────────────────────────
PROFILES = {
    "P1": {
        "name": "Vulnerabilidad económica estructural",
        "short": "Económica estructural",
        "display_keys": ["I1", "I2", "I3", "I4", "I11", "I12", "I21", "I25"],   # incluye I2 derivado
        "weight_keys":  ["I1", "I3", "I4", "I11", "I12", "I21", "I25"],          # I2 sin peso
        "init_weights": {"I1":0.28,"I3":0.18,"I4":0.15,"I11":0.12,"I12":0.10,"I21":0.10,"I25":0.07},
        "question": "¿Este hogar presenta vulnerabilidad P1 · económica estructural?",
    },
    "P2": {
        "name": "Vulnerabilidad por condiciones de la vivienda",
        "short": "Condiciones de vivienda",
        "display_keys": ["I9", "I10", "I5", "I6", "I7", "I20"],
        "weight_keys":  ["I9", "I10", "I5", "I6", "I7", "I20"],
        "init_weights": {"I9":0.30,"I10":0.25,"I5":0.12,"I6":0.12,"I7":0.08,"I20":0.13},
        "question": "¿Este hogar presenta vulnerabilidad P2 · condiciones de la vivienda?",
    },
}

# ─── 50 hogares · datos para P1 y P2, etiqueta ground_truth por perfil ───────
# I1 ISEE€ · I3 carga% · I4 impago · I11 ayudas · I12 microcred · I21 ahorros(meses) · I25 estab(años)
# I5 kWh elec · I6 kWh no-elec · I7 perfil(0-3) · I9 habitab(0-3) · I10 sistemas(0-3) · I20 temp(0/1)
# gt: {"P1":0/1, "P2":0/1}
HOUSEHOLDS = [
    {"id":"HOG-01","nombre":"Rosa M.","edad":67,"composicion":"Pensionista, sola",
     "desc":"Pensión mínima. Concentrador O₂ nocturno. Piso antiguo de alquiler con humedades.",
     "I1":530,"I3":18.2,"I4":1,"I11":1,"I12":0,"I21":0,"I25":12,
     "I5":290,"I6":180,"I7":2,"I9":2,"I10":2,"I20":1,"perfiles":["P1","P2","P4"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-02","nombre":"Carmela V.","edad":81,"composicion":"Anciana sola, tutela Fundación",
     "desc":"Pensión social mínima. Deuda histórica. Piso viejo sin reformas.",
     "I1":460,"I3":24.1,"I4":1,"I11":1,"I12":0,"I21":0,"I25":20,
     "I5":310,"I6":210,"I7":2,"I9":3,"I10":3,"I20":1,"perfiles":["P1","P2"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-03","nombre":"Fatima O.","edad":34,"composicion":"Madre sola, 2 hijos menores",
     "desc":"Trabajo informal. Corte de luz hace 8 meses. Piso en mal estado.",
     "I1":490,"I3":22.7,"I4":1,"I11":0,"I12":1,"I21":0,"I25":2,
     "I5":340,"I6":160,"I7":2,"I9":2,"I10":2,"I20":1,"perfiles":["P1","P2","P6"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-04","nombre":"Amina B.","edad":28,"composicion":"Madre sola, 3 hijos pequeños",
     "desc":"Recién llegada. Trabajo en negro. Vivienda precaria muy mal aislada.",
     "I1":380,"I3":29.4,"I4":1,"I11":0,"I12":0,"I21":0,"I25":1,
     "I5":380,"I6":190,"I7":3,"I9":3,"I10":3,"I20":1,"perfiles":["P1","P2","P5","P6"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-05","nombre":"Marco e Lucia F.","edad":45,"composicion":"Pareja, 1 hijo",
     "desc":"Desempleo reciente. Deuda acumulada. Piso normal en buen estado.",
     "I1":710,"I3":14.8,"I4":0,"I11":0,"I12":0,"I21":1,"I25":8,
     "I5":260,"I6":140,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-06","nombre":"Concetta e figli","edad":39,"composicion":"Madre sola, 3 hijos",
     "desc":"RdC activa. Alta carga energética por piso muy deficiente.",
     "I1":640,"I3":19.5,"I4":1,"I11":1,"I12":1,"I21":0,"I25":6,
     "I5":360,"I6":200,"I7":2,"I9":3,"I10":2,"I20":1,"perfiles":["P1","P2"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-07","nombre":"Nadia T.","edad":44,"composicion":"Sola, desempleada larga duración",
     "desc":"ISEE bajo, sin ayudas. Piso correcto, sin problemas estructurales.",
     "I1":580,"I3":16.3,"I4":0,"I11":0,"I12":1,"I21":0,"I25":5,
     "I5":230,"I6":130,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-08","nombre":"Leila M.","edad":42,"composicion":"Sola, 1 hijo adolescente",
     "desc":"Separada recientemente. Primer impago. Piso de alquiler aceptable.",
     "I1":690,"I3":18.7,"I4":1,"I11":0,"I12":0,"I21":0,"I25":4,
     "I5":280,"I6":150,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-09","nombre":"Calogero F.","edad":55,"composicion":"Solo, desempleo estructural",
     "desc":"Economía sumergida. Sin ISEE actualizado. Piso modesto pero sin deficiencias graves.",
     "I1":610,"I3":13.2,"I4":1,"I11":0,"I12":0,"I21":0,"I25":9,
     "I5":240,"I6":120,"I7":1,"I9":1,"I10":2,"I20":0,"perfiles":["P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-10","nombre":"Beatrice L.","edad":38,"composicion":"Sola, trabajo precario",
     "desc":"ISEE limítrofe. Ahorros mínimos. Vivienda normal.",
     "I1":820,"I3":10.8,"I4":0,"I11":1,"I12":0,"I21":1,"I25":7,
     "I5":250,"I6":130,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P1"],"gt":{"P1":1,"P2":0}},

    # ── P2 dominante (vivienda mala, renta OK) ───────────────────────────────
    {"id":"HOG-11","nombre":"Piero e Claudia M.","edad":48,"composicion":"Pareja, 2 hijos adolescentes",
     "desc":"ISEE razonable pero piso con humedades graves y caldera obsoleta.",
     "I1":1120,"I3":13.6,"I4":0,"I11":0,"I12":0,"I21":2,"I25":10,
     "I5":390,"I6":280,"I7":2,"I9":3,"I10":3,"I20":1,"perfiles":["P2"],"gt":{"P1":0,"P2":1}},
    {"id":"HOG-12","nombre":"Bruna C.","edad":70,"composicion":"Sola, pensión media",
     "desc":"Pensión suficiente pero piso sin aislamiento. Sin deudas.",
     "I1":1100,"I3":14.3,"I4":0,"I11":0,"I12":0,"I21":3,"I25":25,
     "I5":340,"I6":290,"I7":2,"I9":3,"I10":2,"I20":1,"perfiles":["P2"],"gt":{"P1":0,"P2":1}},
    {"id":"HOG-13","nombre":"Rosario e Maria C.","edad":68,"composicion":"Pareja, 1 hijo discapacitado en casa",
     "desc":"Hijo adulto con discapacidad. Gasto eléctrico muy alto. Piso deficiente.",
     "I1":780,"I3":20.4,"I4":0,"I11":1,"I12":0,"I21":1,"I25":18,
     "I5":420,"I6":250,"I7":3,"I9":2,"I10":3,"I20":1,"perfiles":["P1","P2","P4"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-14","nombre":"Antonino L.","edad":47,"composicion":"Solo, autónomo irregular",
     "desc":"Ingresos variables. Piso viejo con humedades. Impago en año malo.",
     "I1":1090,"I3":12.1,"I4":1,"I11":0,"I12":1,"I21":1,"I25":6,
     "I5":300,"I6":270,"I7":2,"I9":2,"I10":2,"I20":1,"perfiles":["P2","P1"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-15","nombre":"Giuseppina R.","edad":62,"composicion":"Sola, ex-trabajadora informal",
     "desc":"Sin pensión aún. Piso propio en muy mal estado. Calefacción inexistente.",
     "I1":670,"I3":17.1,"I4":0,"I11":0,"I12":0,"I21":0,"I25":15,
     "I5":280,"I6":300,"I7":3,"I9":3,"I10":3,"I20":1,"perfiles":["P1","P2"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-16","nombre":"Tommaso e Rita V.","edad":54,"composicion":"Pareja, clase media",
     "desc":"Buena renta pero villa antigua sin reformar. Climatización ineficiente.",
     "I1":1480,"I3":12.8,"I4":0,"I11":0,"I12":0,"I21":4,"I25":20,
     "I5":410,"I6":320,"I7":2,"I9":2,"I10":3,"I20":1,"perfiles":["P2"],"gt":{"P1":0,"P2":1}},
    {"id":"HOG-17","nombre":"Salvo e Ada P.","edad":59,"composicion":"Pareja jubilados",
     "desc":"Pensiones medias. Piso heredado en mal estado térmico. Frío en invierno.",
     "I1":1250,"I3":15.2,"I4":0,"I11":0,"I12":0,"I21":3,"I25":30,
     "I5":300,"I6":310,"I7":2,"I9":3,"I10":2,"I20":1,"perfiles":["P2"],"gt":{"P1":0,"P2":1}},

    # ── P3 dominante (infraconsumo) ──────────────────────────────────────────
    {"id":"HOG-18","nombre":"Vincenzo P.","edad":74,"composicion":"Solo, pensión invalidez",
     "desc":"Consumo anormalmente bajo. Se abriga en vez de calefactar. Piso mal aislado.",
     "I1":510,"I3":8.1,"I4":1,"I11":1,"I12":0,"I21":0,"I25":22,
     "I5":120,"I6":90,"I7":1,"I9":3,"I10":3,"I20":1,"perfiles":["P3","P1","P2"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-19","nombre":"Pietrina e Rocco A.","edad":78,"composicion":"Pareja ancianos dependientes",
     "desc":"Dos pensiones sociales. Consumen muy poco por restricción forzada.",
     "I1":490,"I3":6.8,"I4":0,"I11":1,"I12":0,"I21":0,"I25":30,
     "I5":110,"I6":80,"I7":1,"I9":2,"I10":2,"I20":1,"perfiles":["P3","P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-20","nombre":"Sebastiano M.","edad":26,"composicion":"Solo, NEET",
     "desc":"Sin trabajo ni estudios. Consumo mínimo. Vive con ayuda familiar informal.",
     "I1":420,"I3":7.2,"I4":0,"I11":0,"I12":0,"I21":0,"I25":3,
     "I5":130,"I6":70,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P3","P1","P6"],"gt":{"P1":1,"P2":0}},

    # ── P4 dominante (dependencia eléctrica) ─────────────────────────────────
    {"id":"HOG-21","nombre":"Lucia e figli","edad":41,"composicion":"Madre sola, 1 hijo con TEA",
     "desc":"Trabajo media jornada para cuidar a hijo con autismo. Alta carga eléctrica.",
     "I1":730,"I3":16.8,"I4":0,"I11":1,"I12":1,"I21":0,"I25":7,
     "I5":380,"I6":150,"I7":3,"I9":1,"I10":1,"I20":0,"perfiles":["P4","P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-22","nombre":"Enzo F.","edad":57,"composicion":"Solo, diálisis domiciliaria",
     "desc":"Paciente renal en diálisis 3 veces/semana. Máquina consume mucho. ISEE bajo.",
     "I1":600,"I3":25.3,"I4":0,"I11":1,"I12":0,"I21":0,"I25":14,
     "I5":450,"I6":140,"I7":3,"I9":2,"I10":2,"I20":0,"perfiles":["P4","P1","P2"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-23","nombre":"Carmelo e figli","edad":45,"composicion":"Pareja, 1 hijo con parálisis cerebral",
     "desc":"Cuidados intensivos en casa. ISEE razonable. Dependencia eléctrica crítica.",
     "I1":1050,"I3":18.6,"I4":0,"I11":1,"I12":0,"I21":2,"I25":10,
     "I5":440,"I6":160,"I7":3,"I9":1,"I10":1,"I20":0,"perfiles":["P4"],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-24","nombre":"Tiziana F.","edad":50,"composicion":"Sola, cuidadora no remunerada",
     "desc":"Cuida a madre con Alzheimer. Sin ingresos propios. ISEE bajo. Piso normal.",
     "I1":720,"I3":9.3,"I4":0,"I11":1,"I12":0,"I21":0,"I25":8,
     "I5":250,"I6":120,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P1","P4"],"gt":{"P1":1,"P2":0}},

    # ── P5 dominante (territorial) ───────────────────────────────────────────
    {"id":"HOG-25","nombre":"Youssef A.","edad":38,"composicion":"Solo, trabajador agrícola",
     "desc":"Trabajo agrícola estacional. ISEE bajo. Alojamiento en cortijo aislado.",
     "I1":560,"I3":6.4,"I4":0,"I11":0,"I12":0,"I21":0,"I25":2,
     "I5":160,"I6":110,"I7":1,"I9":2,"I10":2,"I20":1,"perfiles":["P5","P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-26","nombre":"Moussa D.","edad":31,"composicion":"Solo, solicitante asilo",
     "desc":"Centro de acogida temporal. Sin ingresos. Barrera institucional total.",
     "I1":290,"I3":31.0,"I4":0,"I11":1,"I12":1,"I21":0,"I25":1,
     "I5":140,"I6":80,"I7":2,"I9":2,"I10":2,"I20":1,"perfiles":["P5","P1","P6"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-27","nombre":"Cristian e Alina P.","edad":30,"composicion":"Pareja, recién llegados",
     "desc":"Rumaneses. ISEE sobre umbral pero sin red ni acceso a servicios. Piso correcto.",
     "I1":1130,"I3":8.3,"I4":0,"I11":0,"I12":0,"I21":1,"I25":1,
     "I5":230,"I6":120,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P5"],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-28","nombre":"Ivan e Olena S.","edad":43,"composicion":"Pareja inmigrante, 1 hijo",
     "desc":"Ucranianos. Trabajo estable de él. ISEE sobre umbral pero sin historial.",
     "I1":1060,"I3":10.8,"I4":0,"I11":0,"I12":1,"I21":1,"I25":2,
     "I5":250,"I6":140,"I7":1,"I9":1,"I10":2,"I20":0,"perfiles":["P5"],"gt":{"P1":0,"P2":0}},

    # ── P6 dominante (socio-comunitario) ─────────────────────────────────────
    {"id":"HOG-29","nombre":"Gaetano P.","edad":35,"composicion":"Solo, ex-recluso, reinserción",
     "desc":"6 meses fuera del sistema penitenciario. Sin historial ni red social.",
     "I1":680,"I3":8.1,"I4":0,"I11":1,"I12":0,"I21":0,"I25":1,
     "I5":200,"I6":100,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P6","P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-30","nombre":"Lina V.","edad":77,"composicion":"Anciana sola, heredera inmobiliaria",
     "desc":"ISEE alto por patrimonio heredado pero pensión mínima y piso antiguo.",
     "I1":1250,"I3":19.6,"I4":1,"I11":0,"I12":0,"I21":0,"I25":30,
     "I5":290,"I6":280,"I7":2,"I9":3,"I10":3,"I20":1,"perfiles":["P6","P1","P2"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-31","nombre":"Djamila K.","edad":36,"composicion":"Pareja, 2 hijos, marido en paro",
     "desc":"Sola con ingresos. Red social débil. Bonus energía activo.",
     "I1":760,"I3":15.9,"I4":0,"I11":1,"I12":1,"I21":0,"I25":5,
     "I5":300,"I6":160,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P1","P6"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-32","nombre":"Miriam e Abebe T.","edad":35,"composicion":"Pareja, 1 hijo",
     "desc":"Trabajo estable ambos. Sin ISEE consolidado. Piso compartido mal aislado.",
     "I1":870,"I3":13.8,"I4":0,"I11":0,"I12":0,"I21":1,"I25":2,
     "I5":320,"I6":230,"I7":2,"I9":2,"I10":2,"I20":1,"perfiles":["P6","P2"],"gt":{"P1":1,"P2":1}},

    # ── AMBIGUOS / FRONTERA ──────────────────────────────────────────────────
    {"id":"HOG-33","nombre":"Carmelo e Ida B.","edad":65,"composicion":"Pareja, jubilación parcial",
     "desc":"ISEE justo en el umbral. Pequeño negocio. Piso correcto.",
     "I1":1040,"I3":10.1,"I4":0,"I11":0,"I12":0,"I21":2,"I25":20,
     "I5":260,"I6":150,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":["P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-34","nombre":"Grazia e Luigi C.","edad":55,"composicion":"Pareja, trabajo estacional",
     "desc":"Ingresos buenos en verano, bajos en invierno. ISEE promedio engañoso.",
     "I1":970,"I3":12.4,"I4":1,"I11":0,"I12":0,"I21":1,"I25":15,
     "I5":280,"I6":200,"I7":2,"I9":2,"I10":2,"I20":1,"perfiles":["P1","P2"],"gt":{"P1":1,"P2":1}},
    {"id":"HOG-35","nombre":"Roberto A.","edad":48,"composicion":"Solo, desahucio reciente",
     "desc":"ISEE alto el año anterior. Desahuciado hace 2 meses. Ahora en albergue.",
     "I1":1100,"I3":22.0,"I4":1,"I11":1,"I12":0,"I21":0,"I25":0,
     "I5":210,"I6":120,"I7":1,"I9":2,"I10":2,"I20":1,"perfiles":["P1","P5"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-36","nombre":"Antonella e figli","edad":43,"composicion":"Madre sola, 4 hijos",
     "desc":"ISEE bajo por escala equivalencia. Ingresos absolutos razonables.",
     "I1":740,"I3":11.3,"I4":0,"I11":1,"I12":1,"I21":1,"I25":8,
     "I5":340,"I6":170,"I7":2,"I9":1,"I10":1,"I20":0,"perfiles":["P1"],"gt":{"P1":1,"P2":0}},
    {"id":"HOG-37","nombre":"Tancredi M.","edad":24,"composicion":"Solo, estudiante trabajador",
     "desc":"ISEE bajo pero trayectoria ascendente. Sin cargas. Piso compartido moderno.",
     "I1":760,"I3":8.8,"I4":0,"I11":0,"I12":1,"I21":2,"I25":2,
     "I5":190,"I6":90,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-38","nombre":"Emanuele e Sandra R.","edad":51,"composicion":"Pareja, hijos independientes",
     "desc":"Trabajo a tiempo parcial ambos. ISEE limítrofe. Situación estable.",
     "I1":1050,"I3":9.1,"I4":0,"I11":0,"I12":0,"I21":3,"I25":14,
     "I5":250,"I6":140,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},

    # ── SIN VULNERABILIDAD ──────────────────────────────────────────────────
    {"id":"HOG-39","nombre":"Salvatore C.","edad":58,"composicion":"Solo, trabajador precario",
     "desc":"Ingresos bajos pero estables. Gasto moderado. Vivienda correcta.",
     "I1":850,"I3":8.9,"I4":0,"I11":0,"I12":0,"I21":2,"I25":10,
     "I5":220,"I6":120,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-40","nombre":"Giuseppe N.","edad":29,"composicion":"Solo, empleado",
     "desc":"Contrato fijo reciente. Situación estabilizándose. Piso moderno.",
     "I1":940,"I3":7.2,"I4":0,"I11":0,"I12":0,"I21":3,"I25":3,
     "I5":200,"I6":90,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-41","nombre":"Roberta e Franco L.","edad":44,"composicion":"Pareja, 2 hijos, clase media",
     "desc":"Ambos empleados fijos. Piso en propiedad bien aislado.",
     "I1":1680,"I3":5.8,"I4":0,"I11":0,"I12":0,"I21":6,"I25":12,
     "I5":280,"I6":160,"I7":1,"I9":0,"I10":0,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-42","nombre":"Mario T.","edad":53,"composicion":"Solo, funcionario",
     "desc":"Funcionario municipal. Sin ninguna señal de vulnerabilidad. Piso eficiente.",
     "I1":1540,"I3":4.9,"I4":0,"I11":0,"I12":0,"I21":6,"I25":15,
     "I5":210,"I6":100,"I7":0,"I9":0,"I10":0,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-43","nombre":"Daniela e Luca P.","edad":37,"composicion":"Pareja joven, empleados",
     "desc":"Contratos indefinidos. Piso de alquiler moderno bien equipado.",
     "I1":1420,"I3":6.1,"I4":0,"I11":0,"I12":0,"I21":4,"I25":4,
     "I5":240,"I6":120,"I7":1,"I9":0,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-44","nombre":"Silvana R.","edad":66,"composicion":"Sola, pensión media-alta",
     "desc":"Pensión de empleada bancaria. Piso propio pagado y reformado.",
     "I1":1310,"I3":7.3,"I4":0,"I11":0,"I12":0,"I21":6,"I25":25,
     "I5":230,"I6":140,"I7":1,"I9":0,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-45","nombre":"Carmelo G.","edad":41,"composicion":"Solo, profesional liberal",
     "desc":"Abogado con clientela estable. Vivienda de lujo eficiente.",
     "I1":2100,"I3":3.2,"I4":0,"I11":0,"I12":0,"I21":6,"I25":8,
     "I5":260,"I6":130,"I7":0,"I9":0,"I10":0,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-46","nombre":"Nunzia e Aldo C.","edad":60,"composicion":"Pareja, pensiones medias",
     "desc":"Jubilados con pensiones dignas. Piso en propiedad reformado.",
     "I1":1750,"I3":5.1,"I4":0,"I11":0,"I12":0,"I21":6,"I25":28,
     "I5":250,"I6":150,"I7":1,"I9":0,"I10":0,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-47","nombre":"Federica M.","edad":32,"composicion":"Sola, ingeniería",
     "desc":"Contrato indefinido. Sin cargas. Ahorro positivo. Piso moderno.",
     "I1":1890,"I3":4.4,"I4":0,"I11":0,"I12":0,"I21":6,"I25":5,
     "I5":220,"I6":90,"I7":0,"I9":0,"I10":0,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-48","nombre":"Sonia P.","edad":33,"composicion":"Sola, contrato parcial",
     "desc":"Media jornada. ISEE sobre umbral por poco. Piso correcto.",
     "I1":1080,"I3":11.2,"I4":0,"I11":0,"I12":1,"I21":2,"I25":5,
     "I5":250,"I6":140,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-49","nombre":"Domenico A.","edad":61,"composicion":"Solo, pensión anticipada",
     "desc":"Pensión anticipada media. Piso en propiedad. Gasto contenido.",
     "I1":1200,"I3":7.4,"I4":0,"I11":0,"I12":0,"I21":4,"I25":18,
     "I5":230,"I6":130,"I7":1,"I9":1,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
    {"id":"HOG-50","nombre":"Orazio e Valeria B.","edad":49,"composicion":"Pareja, hostelería",
     "desc":"Negocio estable. Ingresos buenos. Vivienda bien mantenida.",
     "I1":1600,"I3":6.7,"I4":0,"I11":0,"I12":0,"I21":6,"I25":12,
     "I5":270,"I6":160,"I7":1,"I9":0,"I10":1,"I20":0,"perfiles":[],"gt":{"P1":0,"P2":0}},
]

# ─── Funciones de cálculo (genéricas por perfil) ─────────────────────────────

def score(hh, weights, profile):
    keys = PROFILES[profile]["weight_keys"]
    total_w = sum(weights.values()) or 1
    return sum(weights[k] * INDICATOR_DEFS[k]["norm"](hh) for k in keys) / total_w

def optimize_weights(expert_labels, profile):
    init = PROFILES[profile]["init_weights"]
    keys = PROFILES[profile]["weight_keys"]
    try:
        from scipy.optimize import minimize
        import numpy as np
    except ImportError:
        return init.copy()
    # Regularización: penaliza alejarse de los pesos iniciales para evitar
    # que el óptimo colapse todo el peso en un único indicador (pesos
    # interpretables y defendibles, no solo predictivos).
    LAMBDA = 15.0
    def loss(w_arr):
        w = {k: max(1e-4, w_arr[i]) for i, k in enumerate(keys)}
        total = 0.0
        for hh in HOUSEHOLDS:
            label = expert_labels.get(hh["id"], hh["gt"][profile])
            s = max(1e-7, min(1 - 1e-7, score(hh, w, profile)))
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

def compute_metrics(weights, profile, expert_labels, threshold):
    """Precision, recall, F1, matriz de confusión sobre las etiquetas disponibles."""
    tp = fp = tn = fn = 0
    for hh in HOUSEHOLDS:
        label = expert_labels.get(hh["id"], hh["gt"][profile])
        pred = 1 if score(hh, weights, profile) >= threshold else 0
        if   label == 1 and pred == 1: tp += 1
        elif label == 0 and pred == 1: fp += 1
        elif label == 0 and pred == 0: tn += 1
        elif label == 1 and pred == 0: fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = 2*precision*recall/(precision+recall) if (precision+recall) else 0.0
    accuracy  = (tp + tn) / len(HOUSEHOLDS)
    return {"tp":tp,"fp":fp,"tn":tn,"fn":fn,
            "precision":precision,"recall":recall,"f1":f1,"accuracy":accuracy}

# ─────────────────────────────────────────────────────────────────────────────
class Tooltip:
    """Tooltip simple para mostrar definiciones de indicadores (mejora F)."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _e):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self.tip, text=self.text, justify="left",
                       bg=C["tooltip_bg"], fg=C["tooltip_fg"],
                       font=("Helvetica Neue", 9), wraplength=320,
                       padx=10, pady=8, relief="flat")
        lbl.pack()

    def _hide(self, _e):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOCIAREM · Perfiles de vulnerabilidad · Messina")
        self.geometry("1240x820")
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        self.profile = "P1"
        # estado por perfil (independiente)
        self.state = {p: {"phase":1, "expert_labels":{}, "opt_weights":None, "live_weights":None}
                      for p in PROFILES}
        self.current_idx = 0
        self.threshold = 0.5
        self.search_text = ""
        self.filtered_idx = list(range(len(HOUSEHOLDS)))

        self._build()
        self._select(0)

    # ── accesos rápidos al estado del perfil activo ──────────────────────────
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

    def _build(self):
        self.sidebar = tk.Frame(self, bg=C["card"], width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        self.right = tk.Frame(self, bg=C["bg"])
        self.right.pack(side="left", fill="both", expand=True)

        # ── Barra de perfil + nav ────────────────────────────────────────────
        self.topbar = tk.Frame(self.right, bg=C["card"], height=44)
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)
        tk.Label(self.topbar, text="Perfil:", font=("Helvetica Neue", 10),
                 bg=C["card"], fg=C["muted"]).pack(side="left", padx=(16, 8))
        self.profile_btns = {}
        for p in PROFILES:
            b = tk.Button(self.topbar, text=f"{p} · {PROFILES[p]['short']}",
                          font=("Helvetica Neue", 10, "bold"),
                          relief="flat", cursor="hand2", padx=12, pady=5,
                          command=lambda pr=p: self._switch_profile(pr))
            b.pack(side="left", padx=(0, 6), pady=6)
            self.profile_btns[p] = b

        # ── Header hogar ─────────────────────────────────────────────────────
        self.hdr = tk.Frame(self.right, bg=C["card"], height=84)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        tk.Frame(self.right, bg=C["border"], height=1).pack(fill="x")
        self.lbl_id    = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"])
        self.lbl_name  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 16, "bold"), bg=C["card"], fg=C["text"])
        self.lbl_comp  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"])
        self.lbl_desc  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"],
                                  wraplength=720, justify="left")
        self.lbl_profiles = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"])
        self.lbl_id.place(x=22, y=6)
        self.lbl_name.place(x=22, y=20)
        self.lbl_comp.place(x=22, y=44)
        self.lbl_desc.place(x=22, y=60)
        self.lbl_profiles.place(x=22, y=73)

        nav = tk.Frame(self.hdr, bg=C["card"])
        nav.place(relx=1.0, x=-14, y=28, anchor="ne")
        n = len(HOUSEHOLDS)
        tk.Button(nav, text="←", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2",
                  command=lambda: self._nav(-1)).pack(side="left")
        self.lbl_nav = tk.Label(nav, text="", font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"])
        self.lbl_nav.pack(side="left", padx=4)
        tk.Button(nav, text="→", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2",
                  command=lambda: self._nav(1)).pack(side="left")

        # ── Canvas scroll ────────────────────────────────────────────────────
        self._canvas = tk.Canvas(self.right, bg=C["bg"], highlightthickness=0)
        vsb = tk.Scrollbar(self.right, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(self._canvas, bg=C["bg"])
        self._cwin = self._canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda e: (
            self._canvas.configure(scrollregion=self._canvas.bbox("all")),
            self._canvas.itemconfig(self._cwin, width=self._canvas.winfo_width())
        ))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._cwin, width=e.width))
        self._canvas.bind_all("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._canvas.bind_all("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>",   lambda e: self._canvas.yview_scroll(1, "units"))

    def _nav(self, direction):
        # navega dentro de la lista filtrada
        if not self.filtered_idx:
            return
        if self.current_idx in self.filtered_idx:
            pos = self.filtered_idx.index(self.current_idx)
        else:
            pos = 0
        pos = (pos + direction) % len(self.filtered_idx)
        self._select(self.filtered_idx[pos])

    def _switch_profile(self, p):
        self.profile = p
        self._select(self.current_idx)

    def _build_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()
        app = self

        # ── Cabecera fija ─────────────────────────────────────────────────────
        top = tk.Frame(self.sidebar, bg=C["card"])
        top.pack(side="top", fill="x")
        tk.Label(top, text="SOCIAREM", font=("Helvetica Neue", 11, "bold"),
                 bg=C["card"], fg=C["accent"]).pack(anchor="w", padx=16, pady=(16, 0))
        tk.Label(top, text="Piloto Messina",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(0, 6))
        tk.Frame(top, bg=C["border"], height=1).pack(fill="x")

        phase_txt = f"{self.profile} · FASE {self.phase}" + (" · Etiquetado" if self.phase==1 else " · Ajuste")
        phase_col = PROFILE_COLORS[self.profile]
        tk.Label(top, text=phase_txt, font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=phase_col).pack(anchor="w", padx=16, pady=(6, 4))

        # ── Búsqueda (mejora C) ──────────────────────────────────────────────
        search_frame = tk.Frame(top, bg=C["card"])
        search_frame.pack(fill="x", padx=12, pady=(0, 6))
        self._search_var = tk.StringVar(value=self.search_text)
        entry = tk.Entry(search_frame, textvariable=self._search_var,
                         font=("Helvetica Neue", 9), relief="solid", bd=1,
                         bg=C["bg"], fg=C["text"])
        entry.pack(fill="x", ipady=3)
        entry.insert(0, "")
        self._search_var.trace_add("write", lambda *a: self._on_search())
        tk.Label(top, text="Buscar por ID, nombre o perfil",
                 font=("Helvetica Neue", 7), bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=14)

        # ── Pie fijo ─────────────────────────────────────────────────────────
        bottom = tk.Frame(self.sidebar, bg=C["card"])
        bottom.pack(side="bottom", fill="x")
        tk.Frame(bottom, bg=C["border"], height=1).pack(fill="x")

        if self.phase == 1:
            # Auto-asignar para demo
            auto_frame = tk.Frame(bottom, bg=C["card"])
            auto_frame.pack(fill="x", padx=8, pady=(6, 2))
            tk.Button(auto_frame, text="▶ Auto-demo",
                      font=("Helvetica Neue", 9, "bold"),
                      bg=C["ok"], fg="#FFFFFF",
                      relief="flat", cursor="hand2", padx=8, pady=6,
                      command=lambda a=app: a._auto_assign(animated=True)
                      ).pack(side="left", fill="x", expand=True, padx=(0, 3))
            tk.Button(auto_frame, text="⚡ Instant.",
                      font=("Helvetica Neue", 9),
                      bg=C["card2"], fg=C["text"],
                      relief="flat", cursor="hand2", padx=8, pady=6,
                      command=lambda a=app: a._auto_assign(animated=False)
                      ).pack(side="left", fill="x", expand=True, padx=(3, 0))

            tk.Button(bottom, text="⚙ Optimizar pesos",
                      font=("Helvetica Neue", 10, "bold"),
                      bg=C["accent2"], fg="#FFFFFF",
                      relief="flat", cursor="hand2", padx=12, pady=7,
                      command=lambda a=app: a._run_optimization()
                      ).pack(fill="x", padx=8, pady=(2, 4))
            self.progress_lbl = tk.Label(bottom,
                                         text=getattr(self, "_progress_text", ""),
                                         font=("Helvetica Neue", 9),
                                         bg=C["card"],
                                         fg=getattr(self, "_progress_color", C["muted"]),
                                         wraplength=204)
            self.progress_lbl.pack(anchor="w", padx=12, pady=(0, 8))
        else:
            tk.Button(bottom, text="⬇ Exportar resultados",
                      font=("Helvetica Neue", 9, "bold"),
                      bg=C["accent"], fg="#FFFFFF",
                      relief="flat", cursor="hand2", padx=10, pady=6,
                      command=lambda a=app: a._export_dialog()
                      ).pack(fill="x", padx=8, pady=(6, 3))
            tk.Button(bottom, text="← Volver a fase 1",
                      font=("Helvetica Neue", 9),
                      bg=C["card2"], fg=C["muted"],
                      relief="flat", cursor="hand2", padx=10, pady=5,
                      command=lambda a=app: a._back_to_phase1()
                      ).pack(fill="x", padx=8, pady=(0, 6))

        # ── Lista scrollable ──────────────────────────────────────────────────
        sb_canvas = tk.Canvas(self.sidebar, bg=C["card"], highlightthickness=0)
        sb_vsb = tk.Scrollbar(self.sidebar, orient="vertical", command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_vsb.set)
        sb_vsb.pack(side="right", fill="y")
        sb_canvas.pack(side="left", fill="both", expand=True)
        sb_frame = tk.Frame(sb_canvas, bg=C["card"])
        sb_win = sb_canvas.create_window((0, 0), window=sb_frame, anchor="nw")
        sb_frame.bind("<Configure>", lambda e: (
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all")),
            sb_canvas.itemconfig(sb_win, width=sb_canvas.winfo_width())))
        sb_canvas.bind("<Configure>", lambda e: sb_canvas.itemconfig(sb_win, width=e.width))
        def _s(e):  sb_canvas.yview_scroll(-1*(e.delta//120), "units")
        def _su(e): sb_canvas.yview_scroll(-1, "units")
        def _sd(e): sb_canvas.yview_scroll(1, "units")
        for wdg in (sb_canvas, sb_frame):
            wdg.bind("<MouseWheel>", _s); wdg.bind("<Button-4>", _su); wdg.bind("<Button-5>", _sd)

        self.sidebar_btns = {}
        for i in self.filtered_idx:
            hh = HOUSEHOLDS[i]
            extra, dot_col = "", C["muted"]
            if self.phase == 2 and self.opt_weights:
                w = self._current_weights()
                pct = int(score(hh, w, self.profile) * 100)
                extra = f"  {pct}%"
                dot_col = C["danger"] if pct >= 65 else (C["warn"] if pct >= 40 else C["ok"])
            elif self.phase == 1:
                lbl = self.expert_labels.get(hh["id"])
                if lbl == 1:   dot_col = C["danger"]
                elif lbl == 0: dot_col = C["ok"]
            fg = dot_col if self.expert_labels.get(hh["id"]) is not None else C["text"]
            btn = tk.Button(sb_frame, text=f"{hh['id']}  {hh['nombre']}{extra}",
                            font=("Helvetica Neue", 9), anchor="w", padx=10, pady=4,
                            relief="flat", cursor="hand2",
                            bg=C["sel"] if i == self.current_idx else C["card"],
                            fg=fg, activebackground=C["sel"], activeforeground=C["text"],
                            command=lambda idx=i, a=app: a._select(idx))
            btn.pack(fill="x", padx=4)
            for ev, fn in [("<MouseWheel>", _s), ("<Button-4>", _su), ("<Button-5>", _sd)]:
                btn.bind(ev, fn)
            self.sidebar_btns[i] = btn

    def _on_search(self):
        self.search_text = self._search_var.get().strip().lower()
        if not self.search_text:
            self.filtered_idx = list(range(len(HOUSEHOLDS)))
        else:
            t = self.search_text
            self.filtered_idx = [
                i for i, hh in enumerate(HOUSEHOLDS)
                if t in hh["id"].lower()
                or t in hh["nombre"].lower()
                or any(t in p.lower() for p in hh["perfiles"])
            ]
        self._build_sidebar()

    def _set_progress(self, text, color):
        self._progress_text = text
        self._progress_color = color
        if hasattr(self, "progress_lbl") and self.progress_lbl.winfo_exists():
            self.progress_lbl.configure(text=text, fg=color)

    def _select(self, idx):
        self.current_idx = idx
        # actualizar botones de perfil activos
        for p, b in self.profile_btns.items():
            if p == self.profile:
                b.configure(bg=PROFILE_COLORS[p], fg="#FFFFFF")
            else:
                b.configure(bg=C["card2"], fg=C["muted"])
        self._build_sidebar()
        hh = HOUSEHOLDS[idx]
        self.lbl_id.configure(text=hh["id"])
        self.lbl_name.configure(text=f"{hh['nombre']}  ·  {hh['edad']} años")
        self.lbl_comp.configure(text=hh["composicion"])
        self.lbl_desc.configure(text=hh["desc"])
        pos = self.filtered_idx.index(idx)+1 if idx in self.filtered_idx else 0
        self.lbl_nav.configure(text=f"{pos}/{len(self.filtered_idx)}")
        if hh["perfiles"]:
            self.lbl_profiles.configure(text=f"Perfiles activos: {'  '.join(hh['perfiles'])}")
        else:
            self.lbl_profiles.configure(text="Sin perfil de vulnerabilidad activo")
        for w in self.content.winfo_children():
            w.destroy()
        self._canvas.yview_moveto(0)
        if self.phase == 1:
            self._render_phase1(hh)
        else:
            self._render_phase2(hh)

    def _current_weights(self):
        if self.live_weights:
            raw = {k: max(0.001, self.live_weights[k].get()) for k in PROFILES[self.profile]["weight_keys"]}
            t = sum(raw.values()) or 1
            return {k: v/t for k, v in raw.items()}
        return self.opt_weights or PROFILES[self.profile]["init_weights"].copy()

    # ── Auto-asignar (demo) ──────────────────────────────────────────────────
    def _auto_assign(self, animated=False):
        if animated:
            self._auto_step(0)
        else:
            for hh in HOUSEHOLDS:
                self.expert_labels[hh["id"]] = hh["gt"][self.profile]
            n = len(self.expert_labels)
            self._set_progress(f"{n}/{len(HOUSEHOLDS)} etiquetados\n¡Listo!", C["ok"])
            self._select(self.current_idx)

    def _auto_step(self, i):
        if i >= len(HOUSEHOLDS):
            self._set_progress(f"{len(HOUSEHOLDS)}/{len(HOUSEHOLDS)} etiquetados\n¡Listo!", C["ok"])
            self._select(0)
            return
        hh = HOUSEHOLDS[i]
        self.expert_labels[hh["id"]] = hh["gt"][self.profile]
        self.current_idx = i
        self.filtered_idx = list(range(len(HOUSEHOLDS)))  # reset filtro durante demo
        self._select(i)
        self._set_progress(f"Auto-demo: {i+1}/{len(HOUSEHOLDS)}", C["accent"])
        self.after(120, lambda: self._auto_step(i + 1))

    def _set_expert(self, hid, val):
        was_unlabeled = hid not in self.expert_labels
        self.expert_labels[hid] = val
        n = len(self.expert_labels)
        nt = len(HOUSEHOLDS)
        self._set_progress(f"{n}/{nt} etiquetados" + ("\n¡Listo!" if n==nt else ""),
                           C["ok"] if n==nt else C["muted"])
        if was_unlabeled and self.current_idx in self.filtered_idx:
            pos = self.filtered_idx.index(self.current_idx)
            if pos < len(self.filtered_idx) - 1:
                self._select(self.filtered_idx[pos + 1])
                return
        self._select(self.current_idx)

    def _run_optimization(self):
        if len(self.expert_labels) < 5:
            self._set_progress("Necesitas ≥ 5 hogares etiquetados.", C["warn"])
            return
        self._set_progress("Optimizando…", C["accent"])
        self.update()
        full = {hh["id"]: self.expert_labels.get(hh["id"], hh["gt"][self.profile]) for hh in HOUSEHOLDS}
        self.opt_weights = optimize_weights(full, self.profile)
        self.phase = 2
        self.live_weights = {k: tk.DoubleVar(value=round(self.opt_weights[k]*100, 1))
                             for k in PROFILES[self.profile]["weight_keys"]}
        self._select(self.current_idx)

    def _back_to_phase1(self):
        self.phase = 1
        self.live_weights = None
        self._select(self.current_idx)

    # ─────────────────────────────────────────────────────────────────────────
    # FASE 1
    # ─────────────────────────────────────────────────────────────────────────
    def _render_phase1(self, hh):
        self.content.configure(bg=C["bg"])
        self._canvas.configure(bg=C["bg"])
        px = 20

        # Resumen multi-perfil (mejora G)
        self._render_profile_summary(self.content, bg=C["bg"], px=px)

        tk.Label(self.content, text="Indicadores",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(14, 6))

        keys = PROFILES[self.profile]["display_keys"]
        grid = tk.Frame(self.content, bg=C["bg"])
        grid.pack(fill="x", padx=px)
        ncols = 4
        for c in range(ncols):
            grid.columnconfigure(c, weight=1)
        for idx_i, k in enumerate(keys):
            self._ind_card(grid, k, hh, idx_i // ncols, idx_i % ncols, ncols)

        # Validación experto
        tk.Label(self.content, text="Validación experto",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(20, 6))
        vcard = tk.Frame(self.content, bg=C["card"],
                         highlightbackground=C["border"], highlightthickness=1)
        vcard.pack(fill="x", padx=px, pady=(0, 16))
        vc = tk.Frame(vcard, bg=C["card"])
        vc.pack(fill="x", padx=16, pady=14)
        tk.Label(vc, text=PROFILES[self.profile]["question"],
                 font=("Helvetica Neue", 11), bg=C["card"], fg=C["text"]).pack(anchor="w")
        tk.Label(vc, text="Etiqueta usada para optimizar los pesos del modelo.",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", pady=(2, 10))
        brow = tk.Frame(vc, bg=C["card"])
        brow.pack(anchor="w")
        cur = self.expert_labels.get(hh["id"])
        for val, lbl, bg_a, fg_a in [
            (1, f"SÍ – vulnerable {self.profile}", C["danger_dim"], C["danger"]),
            (0, "NO – no vulnerable",              C["ok_dim"],     C["ok"]),
        ]:
            active = cur == val
            tk.Button(brow, text=lbl,
                      font=("Helvetica Neue", 11, "bold" if active else "normal"),
                      bg=bg_a if active else C["card2"],
                      fg=fg_a if active else C["muted"],
                      highlightbackground=fg_a if active else C["border"],
                      highlightthickness=2 if active else 1,
                      relief="flat", cursor="hand2", padx=18, pady=8,
                      command=lambda v=val, hid=hh["id"]: self._set_expert(hid, v)
                      ).pack(side="left", padx=(0, 10))
        n_lbl = len(self.expert_labels); nt = len(HOUSEHOLDS)
        status = f"{n_lbl}/{nt} hogares etiquetados"
        if n_lbl == nt: status += "  ·  ¡Listo para optimizar!"
        tk.Label(vc, text=status, font=("Helvetica Neue", 9),
                 bg=C["card"], fg=C["ok"] if n_lbl==nt else C["muted"]).pack(anchor="w", pady=(10, 0))

    def _render_profile_summary(self, parent, bg, px):
        """Mejora G: resumen comparativo entre perfiles según ground_truth."""
        n_p1 = sum(1 for h in HOUSEHOLDS if h["gt"]["P1"] == 1)
        n_p2 = sum(1 for h in HOUSEHOLDS if h["gt"]["P2"] == 1)
        n_both = sum(1 for h in HOUSEHOLDS if h["gt"]["P1"] == 1 and h["gt"]["P2"] == 1)
        n_none = sum(1 for h in HOUSEHOLDS if h["gt"]["P1"] == 0 and h["gt"]["P2"] == 0)
        n_only1 = n_p1 - n_both
        n_only2 = n_p2 - n_both

        card = tk.Frame(parent, bg=C["card"],
                        highlightbackground=C["border"], highlightthickness=1)
        card.pack(fill="x", padx=px, pady=(16, 0))
        ci = tk.Frame(card, bg=C["card"])
        ci.pack(fill="x", padx=16, pady=10)
        tk.Label(ci, text="Resumen de la población (etiqueta de referencia)",
                 font=("Helvetica Neue", 10, "bold"), bg=C["card"], fg=C["text"]).pack(anchor="w")
        row = tk.Frame(ci, bg=C["card"])
        row.pack(fill="x", pady=(8, 0))
        cells = [
            (f"{n_p1}", "vulnerables P1", PROFILE_COLORS["P1"]),
            (f"{n_p2}", "vulnerables P2", PROFILE_COLORS["P2"]),
            (f"{n_both}", "P1 y P2", C["accent2"]),
            (f"{n_only1}", "solo P1", C["muted"]),
            (f"{n_only2}", "solo P2", C["muted"]),
            (f"{n_none}", "ninguno", C["ok"]),
        ]
        for val, lbl, col in cells:
            cell = tk.Frame(row, bg=C["card"])
            cell.pack(side="left", expand=True, fill="x")
            tk.Label(cell, text=val, font=("Helvetica Neue", 20, "bold"),
                     bg=C["card"], fg=col).pack()
            tk.Label(cell, text=lbl, font=("Helvetica Neue", 8),
                     bg=C["card"], fg=C["muted"]).pack()

    def _ind_card(self, parent, k, hh, row, col, ncols):
        d = INDICATOR_DEFS[k]
        is_pri = d["role"] == "primario"
        is_risk = d["risk"](hh)
        rc  = C["danger"] if is_risk else C["ok"]
        bbg = C["badge_pri"] if is_pri else C["badge_sec"]
        bfg = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]
        value = d["display"](hh)
        note = d["note"]
        source = d["source"]

        f = tk.Frame(parent, bg=C["card"],
                     highlightbackground=rc if is_risk else C["border"], highlightthickness=1)
        f.grid(row=row, column=col, padx=(0,6) if col < ncols-1 else 0, pady=(0,6), sticky="nsew")
        inn = tk.Frame(f, bg=C["card"])
        inn.pack(fill="both", expand=True, padx=10, pady=8)
        top = tk.Frame(inn, bg=C["card"])
        top.pack(fill="x")
        badge = tk.Label(top, text=k, font=("Helvetica Neue", 8, "bold"),
                         bg=bbg, fg=bfg, padx=5, pady=1)
        badge.pack(side="left")
        tk.Label(top, text="PRI" if is_pri else "SEC",
                 font=("Helvetica Neue", 7), bg=C["card"], fg=bfg).pack(side="left", padx=(5, 0))
        # icono info → tooltip (mejora F)
        info = tk.Label(top, text="ⓘ", font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"], cursor="hand2")
        info.pack(side="right")
        Tooltip(info, f"{d['long']}\n\n{d['definition']}\n\nFuente: {source}")

        tk.Label(inn, text=d["name"], font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=C["text"], anchor="w").pack(fill="x", pady=(3, 0))
        tk.Label(inn, text=value, font=("Helvetica Neue", 16, "bold"),
                 bg=C["card"], fg=rc, anchor="w").pack(fill="x", pady=(1, 0))
        tk.Label(inn, text=note, font=("Helvetica Neue", 8),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")
        tk.Frame(inn, bg=C["border"], height=1).pack(fill="x", pady=(5, 3))
        tk.Label(inn, text=source, font=("Helvetica Neue", 7),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")

    # ─────────────────────────────────────────────────────────────────────────
    # FASE 2
    # ─────────────────────────────────────────────────────────────────────────
    def _render_phase2(self, hh):
        bg = C["phase2_bg"]
        self.content.configure(bg=bg)
        self._canvas.configure(bg=bg)
        px = 20
        w = self._current_weights()
        s = score(hh, w, self.profile)
        pct = int(s * 100)
        sc, sd, sl = self._score_style(pct)

        # ── Banner score ─────────────────────────────────────────────────────
        banner = tk.Frame(self.content, bg=sd, highlightbackground=sc, highlightthickness=1)
        banner.pack(fill="x", padx=px, pady=(18, 10))
        bi = tk.Frame(banner, bg=sd); bi.pack(fill="x", padx=18, pady=14)
        tk.Label(bi, text=f"VULNERABILIDAD {self.profile} · SCORE",
                 font=("Helvetica Neue", 9, "bold"), bg=sd, fg=sc).pack(anchor="w")
        row_s = tk.Frame(bi, bg=sd); row_s.pack(fill="x", pady=(4, 0))
        self._score_lbl = tk.Label(row_s, text=f"{pct}%", font=("Helvetica Neue", 40, "bold"), bg=sd, fg=sc)
        self._score_lbl.pack(side="left")
        self._score_level_lbl = tk.Label(row_s, text=f"  {sl}", font=("Helvetica Neue", 22, "bold"), bg=sd, fg=sc)
        self._score_level_lbl.pack(side="left")
        # marca de decisión según umbral
        pred = "VULNERABLE" if s >= self.threshold else "NO VULNERABLE"
        self._pred_lbl = tk.Label(row_s, text=f"   → clasificado: {pred}",
                                  font=("Helvetica Neue", 11), bg=sd, fg=sc)
        self._pred_lbl.pack(side="left")
        bar_outer = tk.Frame(bi, bg=C["border"], height=8); bar_outer.pack(fill="x", pady=(10, 0))
        self._bar_inner = tk.Frame(bar_outer, bg=sc, height=8)
        self._bar_inner.place(x=0, y=0, relwidth=min(1.0, s))
        self._banner_frame, self._banner_inner = banner, bi

        # ── Métricas (mejora A) ──────────────────────────────────────────────
        self._render_metrics(self.content, w, bg, px)

        # ── Umbral ajustable (mejora B) ──────────────────────────────────────
        thr_card = tk.Frame(self.content, bg=C["phase2_card"],
                            highlightbackground=C["border"], highlightthickness=1)
        thr_card.pack(fill="x", padx=px, pady=(0, 10))
        tci = tk.Frame(thr_card, bg=C["phase2_card"]); tci.pack(fill="x", padx=16, pady=10)
        tk.Label(tci, text="Umbral de decisión", font=("Helvetica Neue", 10, "bold"),
                 bg=C["phase2_card"], fg=C["text"]).pack(side="left")
        self._thr_var = tk.DoubleVar(value=self.threshold * 100)
        tk.Scale(tci, variable=self._thr_var, from_=10, to=90, resolution=1,
                 orient="horizontal", length=240,
                 bg=C["phase2_card"], fg=C["text"], troughcolor=C["slider_bg"],
                 activebackground=C["accent"], highlightthickness=0, bd=0, sliderrelief="flat",
                 command=lambda v: self._on_threshold_change()).pack(side="left", padx=(10, 0))
        self._thr_lbl = tk.Label(tci, text=f"{int(self.threshold*100)}%",
                                 font=("Helvetica Neue", 11, "bold"),
                                 bg=C["phase2_card"], fg=C["accent"], width=5)
        self._thr_lbl.pack(side="left", padx=(8, 0))
        tk.Label(tci, text="score ≥ umbral → clasificado vulnerable",
                 font=("Helvetica Neue", 8), bg=C["phase2_card"], fg=C["muted"]).pack(side="left", padx=(10, 0))

        # ── Indicadores con contribución ─────────────────────────────────────
        tk.Label(self.content, text="Indicadores · contribución al score",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(8, 6))
        for k in PROFILES[self.profile]["display_keys"]:
            self._ind_row_phase2(self.content, hh, k, w, bg, px)

        # ── Pesos (sliders) ──────────────────────────────────────────────────
        tk.Label(self.content, text="Pesos del modelo",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20, 6))
        wcard = tk.Frame(self.content, bg=C["phase2_card"],
                         highlightbackground=C["accent2"], highlightthickness=1)
        wcard.pack(fill="x", padx=px, pady=(0, 10))
        wci = tk.Frame(wcard, bg=C["phase2_card"]); wci.pack(fill="x", padx=16, pady=14)
        tk.Label(wci, text="Calculados por SLSQP (scipy) · log-loss sobre etiquetas experto. Ajusta con los sliders.",
                 font=("Helvetica Neue", 9), bg=C["phase2_card"], fg=C["muted"]).pack(anchor="w", pady=(0, 10))
        self._w_val_lbls = {}; self._w_delta_lbls = {}
        for k in PROFILES[self.profile]["weight_keys"]:
            self._weight_slider_row(wci, k, hh)

        # ── Tabla de hogares ─────────────────────────────────────────────────
        tk.Label(self.content, text="Todos los hogares · score actual",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20, 6))
        tcard = tk.Frame(self.content, bg=C["phase2_card"],
                         highlightbackground=C["border"], highlightthickness=1)
        tcard.pack(fill="x", padx=px, pady=(0, 20))
        tci2 = tk.Frame(tcard, bg=C["phase2_card"]); tci2.pack(fill="x", padx=14, pady=12)
        self._all_score_labels = {}; self._all_bar_frames = {}; self._all_check_lbls = {}
        for h in HOUSEHOLDS:
            self._table_row(tci2, h, w)

    def _score_style(self, pct):
        if pct >= 65:   return C["danger"], C["danger_dim"], "ALTA"
        elif pct >= 40: return C["warn"],   C["warn_dim"],   "MEDIA"
        else:           return C["ok"],      C["ok_dim"],     "BAJA"

    def _render_metrics(self, parent, w, bg, px):
        m = compute_metrics(w, self.profile, self.expert_labels, self.threshold)
        card = tk.Frame(parent, bg=C["phase2_card"],
                        highlightbackground=C["accent"], highlightthickness=1)
        card.pack(fill="x", padx=px, pady=(0, 10))
        ci = tk.Frame(card, bg=C["phase2_card"]); ci.pack(fill="x", padx=16, pady=12)
        tk.Label(ci, text="Calidad del modelo (sobre etiquetas experto)",
                 font=("Helvetica Neue", 10, "bold"), bg=C["phase2_card"], fg=C["text"]).pack(anchor="w")
        row = tk.Frame(ci, bg=C["phase2_card"]); row.pack(fill="x", pady=(8, 0))
        self._metric_lbls = {}
        for key, label in [("accuracy","Exactitud"),("precision","Precisión"),
                           ("recall","Sensibilidad"),("f1","F1")]:
            cell = tk.Frame(row, bg=C["phase2_card"]); cell.pack(side="left", expand=True, fill="x")
            val_lbl = tk.Label(cell, text=f"{m[key]*100:.0f}%", font=("Helvetica Neue", 18, "bold"),
                               bg=C["phase2_card"], fg=C["accent"])
            val_lbl.pack()
            tk.Label(cell, text=label, font=("Helvetica Neue", 8),
                     bg=C["phase2_card"], fg=C["muted"]).pack()
            self._metric_lbls[key] = val_lbl
        # matriz de confusión compacta
        cm = tk.Frame(ci, bg=C["phase2_card"]); cm.pack(anchor="w", pady=(10, 0))
        self._cm_lbls = {}
        for key, label, col in [("tp","VP",C["ok"]),("fp","FP",C["warn"]),
                               ("fn","FN",C["danger"]),("tn","VN",C["muted"])]:
            cell = tk.Frame(cm, bg=C["phase2_card"]); cell.pack(side="left", padx=(0, 14))
            l = tk.Label(cell, text=str(m[key]), font=("Helvetica Neue", 13, "bold"),
                         bg=C["phase2_card"], fg=col)
            l.pack(side="left")
            tk.Label(cell, text=f" {label}", font=("Helvetica Neue", 9),
                     bg=C["phase2_card"], fg=C["muted"]).pack(side="left")
            self._cm_lbls[key] = l

    def _table_row(self, parent, h, w):
        hs = score(h, w, self.profile); hpct = int(hs * 100)
        hc = C["danger"] if hpct >= 65 else (C["warn"] if hpct >= 40 else C["ok"])
        lbl = self.expert_labels.get(h["id"], h["gt"][self.profile])
        lbl_col = C["danger"] if lbl == 1 else C["ok"]
        lbl_txt = "vuln." if lbl == 1 else "no vuln."
        is_cur = h["id"] == HOUSEHOLDS[self.current_idx]["id"]
        row_bg = C["sel"] if is_cur else C["phase2_card"]
        row_f = tk.Frame(parent, bg=row_bg,
                         highlightbackground=C["accent"] if is_cur else C["border"],
                         highlightthickness=1 if is_cur else 0)
        row_f.pack(fill="x", pady=2)
        ri = tk.Frame(row_f, bg=row_bg); ri.pack(fill="x", padx=10, pady=5)
        tk.Label(ri, text=h["id"], font=("Helvetica Neue", 9, "bold"),
                 bg=row_bg, fg=C["muted"], width=8).pack(side="left")
        tk.Label(ri, text=h["nombre"], font=("Helvetica Neue", 9),
                 bg=row_bg, fg=C["text"], width=22, anchor="w").pack(side="left")
        pf = " ".join(h["perfiles"][:3]) if h["perfiles"] else "—"
        tk.Label(ri, text=pf, font=("Helvetica Neue", 8),
                 bg=row_bg, fg=C["accent2"], width=12).pack(side="left")
        tk.Label(ri, text=lbl_txt, font=("Helvetica Neue", 9),
                 bg=row_bg, fg=lbl_col, width=8).pack(side="left")
        bf = tk.Frame(ri, bg=C["border"], height=10, width=120); bf.pack(side="left", padx=(4, 0))
        bf.pack_propagate(False)
        bfill = tk.Frame(bf, bg=hc, height=10); bfill.place(x=0, y=0, width=int(120*min(1.0, hs)))
        self._all_bar_frames[h["id"]] = (bf, bfill)
        slbl = tk.Label(ri, text=f"{hpct}%", font=("Helvetica Neue", 10, "bold"),
                        bg=row_bg, fg=hc, width=5)
        slbl.pack(side="left", padx=(5, 0))
        self._all_score_labels[h["id"]] = (slbl, row_bg)
        correct = (lbl == 1 and hs >= self.threshold) or (lbl == 0 and hs < self.threshold)
        chk = tk.Label(ri, text="✓" if correct else "✗", font=("Helvetica Neue", 12, "bold"),
                       bg=row_bg, fg=C["ok"] if correct else C["danger"])
        chk.pack(side="left", padx=(3, 0))
        self._all_check_lbls[h["id"]] = (chk, row_bg)

    def _ind_row_phase2(self, parent, hh, k, weights, bg, px):
        d = INDICATOR_DEFS[k]
        is_risk = d["risk"](hh)
        rc = C["danger"] if is_risk else C["ok"]
        rd = C["danger_dim"] if is_risk else C["phase2_card"]
        is_derived = d.get("derived", False)
        wk = PROFILES[self.profile]["weight_keys"]
        contrib = (weights.get(k, 0) * d["norm"](hh)) if (k in wk and not is_derived) else 0
        total_w = sum(weights.values()) or 1
        contrib_pct = int((contrib / total_w) * 100)

        row_f = tk.Frame(parent, bg=rd if is_risk else C["phase2_card"],
                         highlightbackground=rc if is_risk else C["border"], highlightthickness=1)
        row_f.pack(fill="x", padx=px, pady=(0, 5))
        ri = tk.Frame(row_f, bg=rd if is_risk else C["phase2_card"]); ri.pack(fill="x", padx=14, pady=8)
        is_pri = d["role"] == "primario"
        bbg = C["badge_pri"] if is_pri else C["badge_sec"]
        bfg = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]
        left = tk.Frame(ri, bg=ri["bg"]); left.pack(side="left")
        tk.Label(left, text=k, font=("Helvetica Neue", 8, "bold"),
                 bg=bbg, fg=bfg, padx=5, pady=1).pack(anchor="w")
        tk.Label(left, text=d["name"], font=("Helvetica Neue", 9),
                 bg=ri["bg"], fg=C["muted"]).pack(anchor="w", pady=(2, 0))
        tk.Label(ri, text=d["display"](hh), font=("Helvetica Neue", 15, "bold"),
                 bg=ri["bg"], fg=rc, width=12, anchor="w").pack(side="left", padx=(14, 0))
        tk.Label(ri, text=d["note"], font=("Helvetica Neue", 9),
                 bg=ri["bg"], fg=C["muted"], width=22, anchor="w").pack(side="left")
        if not is_derived:
            cb = tk.Frame(ri, bg=C["border"], height=8, width=100); cb.pack(side="left", padx=(6, 0))
            cb.pack_propagate(False)
            tk.Frame(cb, bg=rc, height=8, width=min(100, int(100*min(1.0, contrib*4)))).place(x=0, y=0)
            tk.Label(ri, text=f"+{contrib_pct}%", font=("Helvetica Neue", 9, "bold"),
                     bg=ri["bg"], fg=rc, width=5).pack(side="left", padx=(5, 0))
        else:
            tk.Label(ri, text="(derivado de I1)", font=("Helvetica Neue", 8),
                     bg=ri["bg"], fg=C["muted"]).pack(side="left", padx=(8, 0))

    def _weight_slider_row(self, parent, k, hh):
        d = INDICATOR_DEFS[k]
        row = tk.Frame(parent, bg=C["phase2_card"]); row.pack(fill="x", pady=3)
        tk.Label(row, text=d["long"], font=("Helvetica Neue", 10),
                 bg=C["phase2_card"], fg=C["text"], width=40, anchor="w").pack(side="left")
        tk.Scale(row, variable=self.live_weights[k], from_=0.1, to=60.0, resolution=0.1,
                 orient="horizontal", length=170,
                 bg=C["phase2_card"], fg=C["text"], troughcolor=C["slider_bg"],
                 activebackground=C["accent2"], highlightthickness=0, bd=0, sliderrelief="flat",
                 command=lambda v, hh=hh: self._on_weight_change(hh)).pack(side="left", padx=(6, 0))
        raw = {k2: max(0.001, self.live_weights[k2].get()) for k2 in PROFILES[self.profile]["weight_keys"]}
        t = sum(raw.values()) or 1
        nv = raw[k] / t
        lv = tk.Label(row, text=f"{nv:.3f}", font=("Helvetica Neue", 10, "bold"),
                      bg=C["phase2_card"], fg=C["accent2"], width=6)
        lv.pack(side="left", padx=(5, 0))
        self._w_val_lbls[k] = lv
        delta = nv - self.opt_weights.get(k, 0)
        dl = tk.Label(row, text=f"{'↑' if delta>0.0005 else ('↓' if delta<-0.0005 else '·')} {abs(delta):.3f}",
                      font=("Helvetica Neue", 9), bg=C["phase2_card"],
                      fg=C["warn"] if abs(delta) > 0.01 else C["muted"], width=8)
        dl.pack(side="left", padx=(4, 0))
        self._w_delta_lbls[k] = (dl, self.opt_weights.get(k, 0))

    def _refresh_live(self, hh):
        """Recalcula banner, métricas y tabla con los pesos/umbral actuales."""
        w = self._current_weights()
        s = score(hh, w, self.profile); pct = int(s * 100)
        sc, sd, sl = self._score_style(pct)
        if hasattr(self, "_score_lbl") and self._score_lbl.winfo_exists():
            self._score_lbl.configure(text=f"{pct}%", fg=sc, bg=sd)
            self._score_level_lbl.configure(text=f"  {sl}", fg=sc, bg=sd)
            pred = "VULNERABLE" if s >= self.threshold else "NO VULNERABLE"
            self._pred_lbl.configure(text=f"   → clasificado: {pred}", fg=sc, bg=sd)
            self._banner_inner.configure(bg=sd)
            self._banner_frame.configure(bg=sd, highlightbackground=sc)
            self._bar_inner.configure(bg=sc); self._bar_inner.place(relwidth=min(1.0, s))
        # pesos
        if hasattr(self, "_w_val_lbls"):
            raw = {k: max(0.001, self.live_weights[k].get()) for k in PROFILES[self.profile]["weight_keys"]}
            t = sum(raw.values()) or 1
            for k in PROFILES[self.profile]["weight_keys"]:
                nv = raw[k] / t
                if k in self._w_val_lbls and self._w_val_lbls[k].winfo_exists():
                    self._w_val_lbls[k].configure(text=f"{nv:.3f}")
                if k in self._w_delta_lbls:
                    dl, opt_v = self._w_delta_lbls[k]
                    if dl.winfo_exists():
                        dd = nv - opt_v
                        dl.configure(text=f"{'↑' if dd>0.0005 else ('↓' if dd<-0.0005 else '·')} {abs(dd):.3f}",
                                     fg=C["warn"] if abs(dd) > 0.01 else C["muted"])
        # métricas
        m = compute_metrics(w, self.profile, self.expert_labels, self.threshold)
        if hasattr(self, "_metric_lbls"):
            for key in ("accuracy","precision","recall","f1"):
                if self._metric_lbls[key].winfo_exists():
                    self._metric_lbls[key].configure(text=f"{m[key]*100:.0f}%")
        if hasattr(self, "_cm_lbls"):
            for key in ("tp","fp","fn","tn"):
                if self._cm_lbls[key].winfo_exists():
                    self._cm_lbls[key].configure(text=str(m[key]))
        # tabla
        if hasattr(self, "_all_score_labels"):
            for h in HOUSEHOLDS:
                hs = score(h, w, self.profile); hpct = int(hs * 100)
                hc = C["danger"] if hpct >= 65 else (C["warn"] if hpct >= 40 else C["ok"])
                if h["id"] in self._all_score_labels:
                    slbl, _ = self._all_score_labels[h["id"]]
                    if slbl.winfo_exists(): slbl.configure(text=f"{hpct}%", fg=hc)
                if h["id"] in self._all_bar_frames:
                    bf, bfill = self._all_bar_frames[h["id"]]
                    if bfill.winfo_exists():
                        bfill.configure(bg=hc); bfill.place(width=int(120*min(1.0, hs)))
                if h["id"] in self._all_check_lbls:
                    chk, rbg = self._all_check_lbls[h["id"]]
                    lbl = self.expert_labels.get(h["id"], h["gt"][self.profile])
                    correct = (lbl == 1 and hs >= self.threshold) or (lbl == 0 and hs < self.threshold)
                    if chk.winfo_exists():
                        chk.configure(text="✓" if correct else "✗", fg=C["ok"] if correct else C["danger"])

    def _on_weight_change(self, hh):
        self._refresh_live(hh)
        self._build_sidebar()

    def _on_threshold_change(self):
        self.threshold = self._thr_var.get() / 100.0
        if hasattr(self, "_thr_lbl") and self._thr_lbl.winfo_exists():
            self._thr_lbl.configure(text=f"{int(self.threshold*100)}%")
        self._refresh_live(HOUSEHOLDS[self.current_idx])

    # ── Export (mejora D) ────────────────────────────────────────────────────
    def _export_dialog(self):
        w = self._current_weights()
        m = compute_metrics(w, self.profile, self.expert_labels, self.threshold)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default = f"sociarem_{self.profile}_{ts}.json"
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=default,
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv")])
        if not path:
            return
        rows = []
        for h in HOUSEHOLDS:
            s = score(h, w, self.profile)
            lbl = self.expert_labels.get(h["id"], h["gt"][self.profile])
            rows.append({
                "id": h["id"], "nombre": h["nombre"],
                "perfiles": ",".join(h["perfiles"]),
                "score": round(s, 4),
                "pred": 1 if s >= self.threshold else 0,
                "etiqueta_experto": lbl,
                "ground_truth": h["gt"][self.profile],
            })
        if path.lower().endswith(".csv"):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader(); writer.writerows(rows)
        else:
            payload = {
                "perfil": self.profile,
                "perfil_nombre": PROFILES[self.profile]["name"],
                "timestamp": datetime.now().isoformat(),
                "umbral_decision": self.threshold,
                "pesos": w,
                "metricas": m,
                "hogares": rows,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        self._set_progress(f"Guardado:\n{path.split('/')[-1]}", C["ok"])


if __name__ == "__main__":
    app = App()
    app.mainloop()