"""
SOCIAREM – P1 Vulnerabilidad Económica Estructural
Proof of Concept · Piloto Messina

Indicadores P1 disponibles en Messina:
  Primarios : I1 (ISEE €/mes), I2 (bajo umbral pobreza %)
  Secundarios: I3 (carga energética %), I4 (impago binario),
               I11 (ayudas binario), I12 (microcrédito binario),
               I21 (ahorros líquidos: meses de renta cubiertos),
               I25 (estabilidad administrativa: años de residencia)

50 hogares mezclando perfiles P1–P6
"""

import tkinter as tk
import math

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
    "p1": "#4F8EF7", "p2": "#F5A623", "p3": "#E05C5C",
    "p4": "#A78BFA", "p5": "#3DD68C", "p6": "#F06292",
}

# ── perfil badge colors ───────────────────────────────────────────────────────
PROFILE_COLORS = {
    "P1": "#4F8EF7", "P2": "#F5A623", "P3": "#E05C5C",
    "P4": "#A78BFA", "P5": "#3DD68C", "P6": "#F06292",
}

# ── 50 hogares · mezcla de perfiles P1–P6 ───────────────────────────────────
# Campos:
#   I1  : ISEE mensual €/mes
#   I3  : carga energética %
#   I4  : impago/corte últimos 12m (0/1)
#   I11 : recibe ayudas (0/1)
#   I12 : acceso microcrédito (0/1)
#   I21 : meses de renta cubiertos por ahorros (0 = ninguno, 6 = 6 meses+)
#   I25 : años de residencia estable (0 = inestable, 10 = muy estable)
#   perfiles: lista de perfiles activos para mostrar context
#   ground_truth: etiqueta P1

HOUSEHOLDS = [
    # ── PERFIL P1 dominante ──────────────────────────────────────────────────
    {"id":"HOG-01","nombre":"Rosa M.","edad":67,"composicion":"Pensionista, sola",
     "desc":"Pensión mínima. Concentrador O₂ nocturno. Piso antiguo de alquiler.",
     "I1":530,"I3":18.2,"I4":1,"I11":1,"I12":0,"I21":0,"I25":12,"perfiles":["P1","P4"],"ground_truth":1},
    {"id":"HOG-02","nombre":"Carmela V.","edad":81,"composicion":"Anciana sola, tutela Fundación",
     "desc":"Pensión social mínima. Deuda histórica con comercializadora.",
     "I1":460,"I3":24.1,"I4":1,"I11":1,"I12":0,"I21":0,"I25":20,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-03","nombre":"Fatima O.","edad":34,"composicion":"Madre sola, 2 hijos menores",
     "desc":"Trabajo informal. Corte de luz hace 8 meses. Sin ayudas formales.",
     "I1":490,"I3":22.7,"I4":1,"I11":0,"I12":1,"I21":0,"I25":2,"perfiles":["P1","P6"],"ground_truth":1},
    {"id":"HOG-04","nombre":"Amina B.","edad":28,"composicion":"Madre sola, 3 hijos pequeños",
     "desc":"Recién llegada. Trabajo en negro esporádico. Sin ayuda formal registrada.",
     "I1":380,"I3":29.4,"I4":1,"I11":0,"I12":0,"I21":0,"I25":1,"perfiles":["P1","P5","P6"],"ground_truth":1},
    {"id":"HOG-05","nombre":"Marco e Lucia F.","edad":45,"composicion":"Pareja, 1 hijo",
     "desc":"Desempleo reciente. Sin cortes aún pero deuda acumulada.",
     "I1":710,"I3":14.8,"I4":0,"I11":0,"I12":0,"I21":1,"I25":8,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-06","nombre":"Concetta e figli","edad":39,"composicion":"Madre sola, 3 hijos",
     "desc":"RdC activa. Alta carga energética por piso deficiente.",
     "I1":640,"I3":19.5,"I4":1,"I11":1,"I12":1,"I21":0,"I25":6,"perfiles":["P1","P2"],"ground_truth":1},
    {"id":"HOG-07","nombre":"Nadia T.","edad":44,"composicion":"Sola, desempleada larga duración",
     "desc":"ISEE bajo, sin ayudas formales. Sin cortes pero riesgo latente.",
     "I1":580,"I3":16.3,"I4":0,"I11":0,"I12":1,"I21":0,"I25":5,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-08","nombre":"Leila M.","edad":42,"composicion":"Sola, 1 hijo adolescente",
     "desc":"Separada recientemente. Primer impago hace 2 meses. Sin microcrédito.",
     "I1":690,"I3":18.7,"I4":1,"I11":0,"I12":0,"I21":0,"I25":4,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-09","nombre":"Calogero F.","edad":55,"composicion":"Solo, desempleo estructural",
     "desc":"Nunca contrato indefinido. Economía sumergida. Sin ISEE actualizado.",
     "I1":610,"I3":13.2,"I4":1,"I11":0,"I12":0,"I21":0,"I25":9,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-10","nombre":"Nadia T. (variante)","edad":38,"composicion":"Sola, trabajo precario",
     "desc":"ISEE limítrofe. Ahorros mínimos (1 mes). Sin cortes.",
     "I1":820,"I3":10.8,"I4":0,"I11":1,"I12":0,"I21":1,"I25":7,"perfiles":["P1"],"ground_truth":1},

    # ── PERFIL P2 dominante (vivienda) ───────────────────────────────────────
    {"id":"HOG-11","nombre":"Piero e Claudia M.","edad":48,"composicion":"Pareja, 2 hijos adolescentes",
     "desc":"ISEE razonable pero piso con humedades graves. Alta carga energética.",
     "I1":1120,"I3":13.6,"I4":0,"I11":0,"I12":0,"I21":2,"I25":10,"perfiles":["P2"],"ground_truth":0},
    {"id":"HOG-12","nombre":"Bruna C.","edad":70,"composicion":"Sola, pensión media",
     "desc":"Pensión suficiente pero piso sin aislamiento. Sin deudas.",
     "I1":1100,"I3":14.3,"I4":0,"I11":0,"I12":0,"I21":3,"I25":25,"perfiles":["P2"],"ground_truth":0},
    {"id":"HOG-13","nombre":"Rosario e Maria C.","edad":68,"composicion":"Pareja, 1 hijo discapacitado en casa",
     "desc":"Hijo adulto con discapacidad severa. Gasto eléctrico muy alto. Piso deficiente.",
     "I1":780,"I3":20.4,"I4":0,"I11":1,"I12":0,"I21":1,"I25":18,"perfiles":["P1","P2","P4"],"ground_truth":1},
    {"id":"HOG-14","nombre":"Antonino L.","edad":47,"composicion":"Solo, autónomo irregular",
     "desc":"Año bueno: ISEE alto. Año malo: impago energía. Piso viejo con humedades.",
     "I1":1090,"I3":12.1,"I4":1,"I11":0,"I12":1,"I21":1,"I25":6,"perfiles":["P2","P1"],"ground_truth":1},
    {"id":"HOG-15","nombre":"Giuseppina R.","edad":62,"composicion":"Sola, ex-trabajadora informal",
     "desc":"Sin pensión aún. Piso propio en muy mal estado. Calefacción inexistente.",
     "I1":670,"I3":17.1,"I4":0,"I11":0,"I12":0,"I21":0,"I25":15,"perfiles":["P1","P2"],"ground_truth":1},

    # ── PERFIL P3 dominante (pobreza energética oculta) ──────────────────────
    {"id":"HOG-16","nombre":"Vincenzo P.","edad":74,"composicion":"Solo, pensión invalidez",
     "desc":"Consumo anormalmente bajo para el tamaño del piso. Se abriga en vez de calefactar.",
     "I1":510,"I3":8.1,"I4":1,"I11":1,"I12":0,"I21":0,"I25":22,"perfiles":["P3","P1"],"ground_truth":1},
    {"id":"HOG-17","nombre":"Pietrina e Rocco A.","edad":78,"composicion":"Pareja ancianos dependientes",
     "desc":"Dos pensiones sociales. Consumen muy poco pero no por eficiencia.",
     "I1":490,"I3":6.8,"I4":0,"I11":1,"I12":0,"I21":0,"I25":30,"perfiles":["P3","P1"],"ground_truth":1},
    {"id":"HOG-18","nombre":"Sebastiano M.","edad":26,"composicion":"Solo, NEET",
     "desc":"Sin trabajo ni estudios. Consumo mínimo. Vive con ayuda familiar informal.",
     "I1":420,"I3":7.2,"I4":0,"I11":0,"I12":0,"I21":0,"I25":3,"perfiles":["P3","P1","P6"],"ground_truth":1},
    {"id":"HOG-19","nombre":"Paola N.","edad":59,"composicion":"Sola, enfermedad crónica",
     "desc":"Fibromialgia. Incapacidad parcial. Consume poco pero es por restricción voluntaria forzada.",
     "I1":800,"I3":9.3,"I4":0,"I11":1,"I12":0,"I21":1,"I25":11,"perfiles":["P3","P4"],"ground_truth":1},

    # ── PERFIL P4 dominante (dependencia eléctrica / fragilidad) ─────────────
    {"id":"HOG-20","nombre":"Lucia e figli","edad":41,"composicion":"Madre sola, 1 hijo con TEA",
     "desc":"Trabajo media jornada para cuidar a hijo con autismo. Alta carga eléctrica.",
     "I1":730,"I3":16.8,"I4":0,"I11":1,"I12":1,"I21":0,"I25":7,"perfiles":["P4","P1"],"ground_truth":1},
    {"id":"HOG-21","nombre":"Enzo F.","edad":57,"composicion":"Solo, diálisis 3 veces/semana",
     "desc":"Paciente renal en diálisis domiciliaria. Máquina consume mucho. ISEE bajo.",
     "I1":600,"I3":25.3,"I4":0,"I11":1,"I12":0,"I21":0,"I25":14,"perfiles":["P4","P1"],"ground_truth":1},
    {"id":"HOG-22","nombre":"Carmelo e figli","edad":45,"composicion":"Pareja, 1 hijo con parálisis cerebral",
     "desc":"Cuidados intensivos en casa. ISEE razonable. Dependencia eléctrica crítica.",
     "I1":1050,"I3":18.6,"I4":0,"I11":1,"I12":0,"I21":2,"I25":10,"perfiles":["P4"],"ground_truth":0},
    {"id":"HOG-23","nombre":"Tiziana F.","edad":50,"composicion":"Sola, cuidadora no remunerada",
     "desc":"Cuida a madre con Alzheimer. Sin ingresos propios. ISEE bajo.",
     "I1":720,"I3":9.3,"I4":0,"I11":1,"I12":0,"I21":0,"I25":8,"perfiles":["P1","P4"],"ground_truth":1},

    # ── PERFIL P5 dominante (territorial / acceso) ───────────────────────────
    {"id":"HOG-24","nombre":"Youssef A.","edad":38,"composicion":"Solo, trabajador agrícola",
     "desc":"Trabajo agrícola estacional. ISEE bajo. Alojamiento en cortijo sin red estable.",
     "I1":560,"I3":6.4,"I4":0,"I11":0,"I12":0,"I21":0,"I25":2,"perfiles":["P5","P1"],"ground_truth":1},
    {"id":"HOG-25","nombre":"Moussa D.","edad":31,"composicion":"Solo, solicitante asilo",
     "desc":"Centro de acogida temporal. Sin ingresos propios. Barrera institucional total.",
     "I1":290,"I3":31.0,"I4":0,"I11":1,"I12":1,"I21":0,"I25":1,"perfiles":["P5","P1","P6"],"ground_truth":1},
    {"id":"HOG-26","nombre":"Cristian e Alina P.","edad":30,"composicion":"Pareja, recién llegados",
     "desc":"Rumaneses. ISEE sobre umbral pero sin red de apoyo ni acceso a servicios.",
     "I1":1130,"I3":8.3,"I4":0,"I11":0,"I12":0,"I21":1,"I25":1,"perfiles":["P5"],"ground_truth":0},
    {"id":"HOG-27","nombre":"Ivan e Olena S.","edad":43,"composicion":"Pareja inmigrante, 1 hijo",
     "desc":"Ucranianos. Trabajo estable de él. ISEE sobre umbral pero sin historial.",
     "I1":1060,"I3":10.8,"I4":0,"I11":0,"I12":1,"I21":1,"I25":2,"perfiles":["P5"],"ground_truth":0},

    # ── PERFIL P6 dominante (socio-comunitario) ──────────────────────────────
    {"id":"HOG-28","nombre":"Gaetano P.","edad":35,"composicion":"Solo, ex-recluso, reinserción",
     "desc":"6 meses fuera del sistema penitenciario. Sin historial crediticio ni red social.",
     "I1":680,"I3":8.1,"I4":0,"I11":1,"I12":0,"I21":0,"I25":1,"perfiles":["P6","P1"],"ground_truth":1},
    {"id":"HOG-29","nombre":"Lina V.","edad":77,"composicion":"Anciana sola, heredera inmobiliaria",
     "desc":"ISEE alto por patrimonio heredado pero pensión mínima y aislamiento social total.",
     "I1":1250,"I3":19.6,"I4":1,"I11":0,"I12":0,"I21":0,"I25":30,"perfiles":["P6","P1"],"ground_truth":1},
    {"id":"HOG-30","nombre":"Djamila K.","edad":36,"composicion":"Pareja, 2 hijos, marido en paro",
     "desc":"Sola con ingresos. Red social débil. Bonus energía activo. Riesgo de impago.",
     "I1":760,"I3":15.9,"I4":0,"I11":1,"I12":1,"I21":0,"I25":5,"perfiles":["P1","P6"],"ground_truth":1},
    {"id":"HOG-31","nombre":"Miriam e Abebe T.","edad":35,"composicion":"Pareja, 1 hijo",
     "desc":"Trabajo estable ambos. Sin ISEE consolidado. Red comunitaria nula.",
     "I1":870,"I3":13.8,"I4":0,"I11":0,"I12":0,"I21":1,"I25":2,"perfiles":["P6"],"ground_truth":1},

    # ── CASOS AMBIGUOS / FRONTERA ────────────────────────────────────────────
    {"id":"HOG-32","nombre":"Carmelo e Ida B.","edad":65,"composicion":"Pareja, jubilación parcial",
     "desc":"ISEE justo en el umbral. Pequeño negocio. Situación estable pero frágil.",
     "I1":1040,"I3":10.1,"I4":0,"I11":0,"I12":0,"I21":2,"I25":20,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-33","nombre":"Grazia e Luigi C.","edad":55,"composicion":"Pareja, trabajo estacional",
     "desc":"Ingresos buenos en verano, muy bajos en invierno. ISEE promedio engañoso.",
     "I1":970,"I3":12.4,"I4":1,"I11":0,"I12":0,"I21":1,"I25":15,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-34","nombre":"Roberto A.","edad":48,"composicion":"Solo, desahucio reciente",
     "desc":"ISEE alto el año anterior. Desahuciado hace 2 meses. Ahora en albergue.",
     "I1":1100,"I3":22.0,"I4":1,"I11":1,"I12":0,"I21":0,"I25":0,"perfiles":["P1","P5"],"ground_truth":1},
    {"id":"HOG-35","nombre":"Antonella e figli","edad":43,"composicion":"Madre sola, 4 hijos",
     "desc":"ISEE bajo por escala equivalencia. En valor absoluto los ingresos son razonables.",
     "I1":740,"I3":11.3,"I4":0,"I11":1,"I12":1,"I21":1,"I25":8,"perfiles":["P1"],"ground_truth":1},
    {"id":"HOG-36","nombre":"Tancredi M.","edad":24,"composicion":"Solo, estudiante trabajador",
     "desc":"ISEE bajo pero trayectoria ascendente. Sin cargas familiares.",
     "I1":760,"I3":8.8,"I4":0,"I11":0,"I12":1,"I21":2,"I25":2,"perfiles":[],"ground_truth":0},
    {"id":"HOG-37","nombre":"Emanuele e Sandra R.","edad":51,"composicion":"Pareja, hijos independientes",
     "desc":"Trabajo a tiempo parcial ambos. ISEE limítrofe. Situación estable.",
     "I1":1050,"I3":9.1,"I4":0,"I11":0,"I12":0,"I21":3,"I25":14,"perfiles":[],"ground_truth":0},

    # ── SIN VULNERABILIDAD ──────────────────────────────────────────────────
    {"id":"HOG-38","nombre":"Salvatore C.","edad":58,"composicion":"Solo, trabajador precario",
     "desc":"Ingresos bajos pero estables. Gasto moderado. Sin señales de riesgo.",
     "I1":850,"I3":8.9,"I4":0,"I11":0,"I12":0,"I21":2,"I25":10,"perfiles":[],"ground_truth":0},
    {"id":"HOG-39","nombre":"Giuseppe N.","edad":29,"composicion":"Solo, empleado",
     "desc":"Contrato fijo reciente. Situación estabilizándose.",
     "I1":940,"I3":7.2,"I4":0,"I11":0,"I12":0,"I21":3,"I25":3,"perfiles":[],"ground_truth":0},
    {"id":"HOG-40","nombre":"Roberta e Franco L.","edad":44,"composicion":"Pareja, 2 hijos, clase media",
     "desc":"Ambos empleados fijos. Piso en propiedad. Gasto controlado.",
     "I1":1680,"I3":5.8,"I4":0,"I11":0,"I12":0,"I21":6,"I25":12,"perfiles":[],"ground_truth":0},
    {"id":"HOG-41","nombre":"Mario T.","edad":53,"composicion":"Solo, funcionario",
     "desc":"Funcionario municipal. Sin ninguna señal de vulnerabilidad.",
     "I1":1540,"I3":4.9,"I4":0,"I11":0,"I12":0,"I21":6,"I25":15,"perfiles":[],"ground_truth":0},
    {"id":"HOG-42","nombre":"Daniela e Luca P.","edad":37,"composicion":"Pareja joven, empleados",
     "desc":"Contratos indefinidos recientes. Piso de alquiler moderno. Sin deudas.",
     "I1":1420,"I3":6.1,"I4":0,"I11":0,"I12":0,"I21":4,"I25":4,"perfiles":[],"ground_truth":0},
    {"id":"HOG-43","nombre":"Silvana R.","edad":66,"composicion":"Sola, pensión media-alta",
     "desc":"Pensión de empleada bancaria. Piso propio pagado.",
     "I1":1310,"I3":7.3,"I4":0,"I11":0,"I12":0,"I21":6,"I25":25,"perfiles":[],"ground_truth":0},
    {"id":"HOG-44","nombre":"Carmelo G.","edad":41,"composicion":"Solo, profesional liberal",
     "desc":"Abogado con clientela estable. Sin ninguna señal de riesgo.",
     "I1":2100,"I3":3.2,"I4":0,"I11":0,"I12":0,"I21":6,"I25":8,"perfiles":[],"ground_truth":0},
    {"id":"HOG-45","nombre":"Nunzia e Aldo C.","edad":60,"composicion":"Pareja, pensiones medias",
     "desc":"Jubilados con pensiones dignas. Piso en propiedad.",
     "I1":1750,"I3":5.1,"I4":0,"I11":0,"I12":0,"I21":6,"I25":28,"perfiles":[],"ground_truth":0},
    {"id":"HOG-46","nombre":"Federica M.","edad":32,"composicion":"Sola, ingeniería",
     "desc":"Contrato indefinido. Sin cargas. Ahorro mensual positivo.",
     "I1":1890,"I3":4.4,"I4":0,"I11":0,"I12":0,"I21":6,"I25":5,"perfiles":[],"ground_truth":0},
    {"id":"HOG-47","nombre":"Sonia P.","edad":33,"composicion":"Sola, contrato parcial",
     "desc":"Media jornada. ISEE sobre umbral por poco. Sin deudas.",
     "I1":1080,"I3":11.2,"I4":0,"I11":0,"I12":1,"I21":2,"I25":5,"perfiles":[],"ground_truth":0},
    {"id":"HOG-48","nombre":"Domenico A.","edad":61,"composicion":"Solo, pensión anticipada",
     "desc":"Pensión anticipada media. Piso en propiedad. Gasto contenido.",
     "I1":1200,"I3":7.4,"I4":0,"I11":0,"I12":0,"I21":4,"I25":18,"perfiles":[],"ground_truth":0},
    {"id":"HOG-49","nombre":"Filippo e Serena R.","edad":52,"composicion":"Pareja, trabajo temporal",
     "desc":"Contratos estacionales. ISEE alto en temporada. Sin señales de riesgo.",
     "I1":1150,"I3":9.8,"I4":0,"I11":0,"I12":0,"I21":3,"I25":10,"perfiles":[],"ground_truth":0},
    {"id":"HOG-50","nombre":"Orazio e Valeria B.","edad":49,"composicion":"Pareja, hostelería",
     "desc":"Negocio estable. Ingresos buenos. Sin deudas.",
     "I1":1600,"I3":6.7,"I4":0,"I11":0,"I12":0,"I21":6,"I25":12,"perfiles":[],"ground_truth":0},
]

IND_KEYS = ["I1", "I3", "I4", "I11", "I12", "I21", "I25"]
IND_NAMES = {
    "I1":  "Renta neta equiv.",
    "I3":  "Carga energética",
    "I4":  "Impago / corte",
    "I11": "Recibe ayudas",
    "I12": "Microcrédito",
    "I21": "Ahorros líquidos",
    "I25": "Estabilidad residencial",
}
IND_LONG = {
    "I1":  "I1 – Renta neta mensual equivalente",
    "I3":  "I3 – Carga energética del hogar",
    "I4":  "I4 – Impago o corte de suministro",
    "I11": "I11 – Acceso a ayudas sociales/energéticas",
    "I12": "I12 – Acceso a microcrédito/apoyo comunitario",
    "I21": "I21 – Ahorros líquidos o activos realizables",
    "I25": "I25 – Estabilidad administrativa y residencial",
}
INIT_WEIGHTS = {"I1":0.28,"I3":0.18,"I4":0.15,"I11":0.12,"I12":0.10,"I21":0.10,"I25":0.07}


def ind_norm(hh, k):
    if k == "I1":  return max(0.0, min(1.0, (1200 - hh["I1"]) / 800))
    if k == "I3":  return max(0.0, min(1.0, (hh["I3"] - 5) / 25))
    if k == "I4":  return float(hh["I4"])
    if k == "I11": return float(hh["I11"])
    if k == "I12": return 1.0 - float(hh["I12"])           # sin microcrédito = más vulnerable
    if k == "I21": return max(0.0, min(1.0, (3 - hh["I21"]) / 3))  # 0 meses=1.0, 3+=0.0
    if k == "I25": return max(0.0, min(1.0, (5 - hh["I25"]) / 5))  # 0 años=1.0, 5+=0.0
    return 0.0

def score(hh, weights):
    total_w = sum(weights.values()) or 1
    return sum(weights[k] * ind_norm(hh, k) for k in IND_KEYS) / total_w

def optimize_weights(expert_labels):
    try:
        from scipy.optimize import minimize
        import numpy as np
    except ImportError:
        return INIT_WEIGHTS.copy()
    keys = IND_KEYS
    def loss(w_arr):
        w = {k: max(1e-4, w_arr[i]) for i, k in enumerate(keys)}
        total = 0.0
        for hh in HOUSEHOLDS:
            label = expert_labels.get(hh["id"], hh["ground_truth"])
            s = max(1e-7, min(1 - 1e-7, score(hh, w)))
            total -= label * math.log(s) + (1 - label) * math.log(1 - s)
        return total
    w0 = np.array([INIT_WEIGHTS[k] for k in keys])
    res = minimize(loss, w0, method="SLSQP",
                   bounds=[(0.001, 1.0)] * len(keys),
                   constraints=[{"type": "eq", "fun": lambda w: sum(w) - 1.0}],
                   options={"maxiter": 800, "ftol": 1e-10})
    if res.success:
        raw = {k: float(max(0.001, res.x[i])) for i, k in enumerate(keys)}
        t = sum(raw.values())
        return {k: v / t for k, v in raw.items()}
    return INIT_WEIGHTS.copy()


# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOCIAREM · P1 · Messina")
        self.geometry("1200x800")
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.phase = 1
        self.current_idx = 0
        self.expert_labels = {}
        self.opt_weights = None
        self.live_weights = None
        self._build()
        self._select(0)

    def _build(self):
        self.sidebar = tk.Frame(self, bg=C["card"], width=232)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        self.right = tk.Frame(self, bg=C["bg"])
        self.right.pack(side="left", fill="both", expand=True)

        self.hdr = tk.Frame(self.right, bg=C["card"], height=88)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        self.lbl_id    = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"])
        self.lbl_name  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 16, "bold"), bg=C["card"], fg=C["text"])
        self.lbl_comp  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"])
        self.lbl_desc  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"],
                                  wraplength=700, justify="left")
        self.lbl_profiles = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"])
        self.lbl_id.place(x=22, y=8)
        self.lbl_name.place(x=22, y=22)
        self.lbl_comp.place(x=22, y=47)
        self.lbl_desc.place(x=22, y=63)
        self.lbl_profiles.place(x=22, y=76)

        nav = tk.Frame(self.hdr, bg=C["card"])
        nav.place(relx=1.0, x=-14, y=30, anchor="ne")
        n = len(HOUSEHOLDS)
        tk.Button(nav, text="←", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2",
                  command=lambda: self._select((self.current_idx - 1) % n)).pack(side="left")
        self.lbl_nav = tk.Label(nav, text="", font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"])
        self.lbl_nav.pack(side="left", padx=4)
        tk.Button(nav, text="→", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2",
                  command=lambda: self._select((self.current_idx + 1) % n)).pack(side="left")

        tk.Frame(self.right, bg=C["border"], height=1).pack(fill="x")

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

    def _build_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()

        top = tk.Frame(self.sidebar, bg=C["card"])
        top.pack(side="top", fill="x")
        tk.Label(top, text="SOCIAREM", font=("Helvetica Neue", 11, "bold"),
                 bg=C["card"], fg=C["accent"]).pack(anchor="w", padx=16, pady=(18, 0))
        tk.Label(top, text="Piloto Messina · P1",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(0, 8))
        tk.Frame(top, bg=C["border"], height=1).pack(fill="x")
        phase_txt = "FASE 1 · Etiquetado" if self.phase == 1 else "FASE 2 · Ajuste de pesos"
        phase_col = C["accent"] if self.phase == 1 else C["accent2"]
        tk.Label(top, text=phase_txt, font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=phase_col).pack(anchor="w", padx=16, pady=(6, 2))
        tk.Label(top, text="Hogares", font=("Helvetica Neue", 8, "bold"),
                 bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(2, 4))

        bottom = tk.Frame(self.sidebar, bg=C["card"])
        bottom.pack(side="bottom", fill="x")
        tk.Frame(bottom, bg=C["border"], height=1).pack(fill="x")
        _app = self
        if self.phase == 1:
            tk.Button(bottom, text="⚡  Optimizar pesos",
                      font=("Helvetica Neue", 10, "bold"),
                      bg=C["accent2"], fg=C["text"],
                      relief="flat", cursor="hand2", padx=12, pady=7,
                      command=lambda a=_app: a._run_optimization()
                      ).pack(fill="x", padx=8, pady=(6, 4))
            self.progress_lbl = tk.Label(bottom,
                                         text=getattr(self, "_progress_text", ""),
                                         font=("Helvetica Neue", 9),
                                         bg=C["card"],
                                         fg=getattr(self, "_progress_color", C["muted"]),
                                         wraplength=196)
            self.progress_lbl.pack(anchor="w", padx=12, pady=(0, 8))
        else:
            tk.Button(bottom, text="← Volver a fase 1",
                      font=("Helvetica Neue", 9),
                      bg=C["card2"], fg=C["muted"],
                      relief="flat", cursor="hand2", padx=10, pady=5,
                      command=lambda a=_app: a._back_to_phase1()
                      ).pack(fill="x", padx=8, pady=6)

        sb_canvas = tk.Canvas(self.sidebar, bg=C["card"], highlightthickness=0)
        sb_vsb = tk.Scrollbar(self.sidebar, orient="vertical", command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_vsb.set)
        sb_vsb.pack(side="right", fill="y")
        sb_canvas.pack(side="left", fill="both", expand=True)
        sb_frame = tk.Frame(sb_canvas, bg=C["card"])
        sb_win = sb_canvas.create_window((0, 0), window=sb_frame, anchor="nw")
        sb_frame.bind("<Configure>", lambda e: (
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all")),
            sb_canvas.itemconfig(sb_win, width=sb_canvas.winfo_width())
        ))
        sb_canvas.bind("<Configure>", lambda e: sb_canvas.itemconfig(sb_win, width=e.width))

        def _sb_scroll(e):   sb_canvas.yview_scroll(-1*(e.delta//120), "units")
        def _sb_up(e):       sb_canvas.yview_scroll(-1, "units")
        def _sb_down(e):     sb_canvas.yview_scroll(1, "units")
        for widget in (sb_canvas, sb_frame):
            widget.bind("<MouseWheel>", _sb_scroll)
            widget.bind("<Button-4>",   _sb_up)
            widget.bind("<Button-5>",   _sb_down)

        app = self
        self.sidebar_btns = []
        for i, hh in enumerate(HOUSEHOLDS):
            extra, dot_col = "", C["muted"]
            if self.phase == 2 and self.opt_weights:
                w = self.opt_weights if not self.live_weights else {
                    k: max(0.001, self.live_weights[k].get()) for k in IND_KEYS}
                if self.live_weights:
                    t = sum(w.values()) or 1
                    w = {k: v/t for k, v in w.items()}
                s = score(hh, w)
                pct = int(s * 100)
                extra = f"  {pct}%"
                dot_col = C["danger"] if pct >= 65 else (C["warn"] if pct >= 40 else C["ok"])
            elif self.phase == 1:
                lbl = self.expert_labels.get(hh["id"])
                if lbl == 1:   dot_col = C["danger"]
                elif lbl == 0: dot_col = C["ok"]

            fg = dot_col if self.expert_labels.get(hh["id"]) is not None else C["text"]
            btn = tk.Button(
                sb_frame,
                text=f"{hh['id']}  {hh['nombre']}{extra}",
                font=("Helvetica Neue", 9), anchor="w", padx=10, pady=4,
                relief="flat", cursor="hand2",
                bg=C["sel"] if i == self.current_idx else C["card"],
                fg=fg, activebackground=C["sel"], activeforeground=C["text"],
                command=lambda idx=i, a=app: a._select(idx)
            )
            btn.pack(fill="x", padx=4)
            for ev, fn in [("<MouseWheel>", _sb_scroll), ("<Button-4>", _sb_up), ("<Button-5>", _sb_down)]:
                btn.bind(ev, fn)
            self.sidebar_btns.append(btn)

    def _set_progress(self, text, color):
        self._progress_text = text
        self._progress_color = color
        if hasattr(self, "progress_lbl") and self.progress_lbl.winfo_exists():
            self.progress_lbl.configure(text=text, fg=color)

    def _select(self, idx):
        self.current_idx = idx
        self._build_sidebar()
        hh = HOUSEHOLDS[idx]
        self.lbl_id.configure(text=hh["id"])
        self.lbl_name.configure(text=f"{hh['nombre']}  ·  {hh['edad']} años")
        self.lbl_comp.configure(text=hh["composicion"])
        self.lbl_desc.configure(text=hh["desc"])
        self.lbl_nav.configure(text=f"{idx+1}/{len(HOUSEHOLDS)}")
        # perfiles badge
        if hh["perfiles"]:
            badges = "  ".join(hh["perfiles"])
            self.lbl_profiles.configure(text=f"Perfiles: {badges}")
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
            raw = {k: max(0.001, self.live_weights[k].get()) for k in IND_KEYS}
            t = sum(raw.values()) or 1
            return {k: v/t for k, v in raw.items()}
        return self.opt_weights or INIT_WEIGHTS.copy()

    # ─────────────────────────────────────────────────────────────────────────
    # FASE 1
    # ─────────────────────────────────────────────────────────────────────────
    def _render_phase1(self, hh):
        self.content.configure(bg=C["bg"])
        self._canvas.configure(bg=C["bg"])
        px = 20

        tk.Label(self.content, text="Indicadores",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(18, 6))

        grid = tk.Frame(self.content, bg=C["bg"])
        grid.pack(fill="x", padx=px)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)
        grid.columnconfigure(3, weight=1)

        # I2 se deriva del ISEE: % del umbral (1050 €/mes)
        i2_pct = int(hh["I1"] / 1050 * 100)
        i21_txt = f"{hh['I21']} mes{'es' if hh['I21']!=1 else ''}" if hh["I21"] > 0 else "Ninguno"
        i25_txt = f"{hh['I25']} año{'s' if hh['I25']!=1 else ''}" if hh["I25"] > 0 else "< 1 año"

        indicators = [
            # iid, nombre, rol, valor display, nota umbral, es_riesgo, fuente
            ("I1",  "Renta neta equiv.",       "primario",
             f"{hh['I1']} €/mes", "< 780 €/mes → riesgo",      hh["I1"] < 780,    "DS2 · ISEE"),
            ("I2",  "Bajo umbral pobreza",      "primario",
             f"{i2_pct}% del umbral",  "umbral: 1.050 €/mes equiv.", hh["I1"] < 1050, "DS2 · ISEE"),
            ("I3",  "Carga energética",         "secundario",
             f"{hh['I3']:.1f}%",  "> 10% → riesgo",             hh["I3"] > 10,     "DS4 · DS14"),
            ("I4",  "Impago / corte",           "secundario",
             "SÍ" if hh["I4"] else "NO",  "Últimos 12 meses",  bool(hh["I4"]),    "DS8 · Fundación"),
            ("I11", "Recibe ayudas",            "secundario",
             "SÍ" if hh["I11"] else "NO", "Bonus energía / RdC", bool(hh["I11"]), "DS8 · DS3"),
            ("I12", "Microcrédito",             "secundario",
             "SÍ" if hh["I12"] else "NO", "Apoyo financiero comun.", not bool(hh["I12"]), "DS7 · DS27"),
            ("I21", "Ahorros líquidos",         "secundario",
             i21_txt, "< 1 mes → riesgo alto",   hh["I21"] < 1,      "DS2 · DS8"),
            ("I25", "Estabilidad residencial",  "secundario",
             i25_txt, "< 2 años → inestable",    hh["I25"] < 2,      "DS8"),
        ]
        for idx_i, (iid, name, role, value, note, is_risk, source) in enumerate(indicators):
            self._ind_card(grid, iid, name, role, value, note, is_risk, source, idx_i // 4, idx_i % 4)

        # Validación experto
        tk.Label(self.content, text="Validación experto",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(20, 6))

        vcard = tk.Frame(self.content, bg=C["card"],
                         highlightbackground=C["border"], highlightthickness=1)
        vcard.pack(fill="x", padx=px, pady=(0, 16))
        vc = tk.Frame(vcard, bg=C["card"])
        vc.pack(fill="x", padx=16, pady=14)

        tk.Label(vc, text="¿Este hogar presenta vulnerabilidad P1 · económica estructural?",
                 font=("Helvetica Neue", 11), bg=C["card"], fg=C["text"]).pack(anchor="w")
        tk.Label(vc, text="Etiqueta usada para optimizar pesos del modelo.",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", pady=(2, 10))

        brow = tk.Frame(vc, bg=C["card"])
        brow.pack(anchor="w")
        cur = self.expert_labels.get(hh["id"])
        for val, lbl, bg_a, fg_a in [
            (1, "SÍ – vulnerable P1",  C["danger_dim"], C["danger"]),
            (0, "NO – no vulnerable",  C["ok_dim"],     C["ok"]),
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

        n_lbl = len(self.expert_labels)
        n_total = len(HOUSEHOLDS)
        status = f"{n_lbl}/{n_total} hogares etiquetados"
        scol = C["ok"] if n_lbl == n_total else C["muted"]
        if n_lbl == n_total:
            status += "  ·  ¡Listo para optimizar!"
        tk.Label(vc, text=status, font=("Helvetica Neue", 9),
                 bg=C["card"], fg=scol).pack(anchor="w", pady=(10, 0))

    def _ind_card(self, parent, iid, name, role, value, note, is_risk, source, row, col):
        is_pri = role == "primario"
        rc   = C["danger"] if is_risk else C["ok"]
        rdim = C["danger_dim"] if is_risk else C["ok_dim"]
        bbg  = C["badge_pri"] if is_pri else C["badge_sec"]
        bfg  = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]

        f = tk.Frame(parent, bg=C["card"],
                     highlightbackground=rc if is_risk else C["border"],
                     highlightthickness=1)
        f.grid(row=row, column=col, padx=(0,6) if col < 3 else 0, pady=(0,6), sticky="nsew")
        inn = tk.Frame(f, bg=C["card"])
        inn.pack(fill="both", expand=True, padx=10, pady=8)

        top = tk.Frame(inn, bg=C["card"])
        top.pack(fill="x")
        tk.Label(top, text=iid, font=("Helvetica Neue", 8, "bold"),
                 bg=bbg, fg=bfg, padx=5, pady=1).pack(side="left")
        tk.Label(top, text="PRI" if is_pri else "SEC",
                 font=("Helvetica Neue", 7), bg=C["card"], fg=bfg).pack(side="left", padx=(5, 0))

        tk.Label(inn, text=name, font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=C["text"], anchor="w").pack(fill="x", pady=(3, 0))
        tk.Label(inn, text=value, font=("Helvetica Neue", 18, "bold"),
                 bg=C["card"], fg=rc, anchor="w").pack(fill="x", pady=(1, 0))
        tk.Label(inn, text=note, font=("Helvetica Neue", 8),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")
        tk.Frame(inn, bg=C["border"], height=1).pack(fill="x", pady=(5, 3))
        tk.Label(inn, text=source, font=("Helvetica Neue", 7),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")

    def _set_expert(self, hid, val):
        was_unlabeled = hid not in self.expert_labels
        self.expert_labels[hid] = val
        n = len(self.expert_labels)
        n_total = len(HOUSEHOLDS)
        txt = f"{n}/{n_total} etiquetados" + ("\n¡Listo!" if n == n_total else "")
        col = C["ok"] if n == n_total else C["muted"]
        self._set_progress(txt, col)
        if was_unlabeled and self.current_idx < n_total - 1:
            self._select(self.current_idx + 1)
        else:
            self._select(self.current_idx)

    def _run_optimization(self):
        if len(self.expert_labels) < 5:
            self._set_progress("Necesitas ≥ 5 hogares etiquetados.", C["warn"])
            return
        self._set_progress("Optimizando…", C["accent"])
        self.update()
        full = {hh["id"]: self.expert_labels.get(hh["id"], hh["ground_truth"]) for hh in HOUSEHOLDS}
        self.opt_weights = optimize_weights(full)
        self.phase = 2
        self._enter_phase2()

    def _back_to_phase1(self):
        self.phase = 1
        self.live_weights = None
        self._select(self.current_idx)

    # ─────────────────────────────────────────────────────────────────────────
    # FASE 2
    # ─────────────────────────────────────────────────────────────────────────
    def _enter_phase2(self):
        self.live_weights = {k: tk.DoubleVar(value=round(self.opt_weights[k] * 100, 1))
                             for k in IND_KEYS}
        self._select(self.current_idx)

    def _render_phase2(self, hh):
        bg = C["phase2_bg"]
        self.content.configure(bg=bg)
        self._canvas.configure(bg=bg)
        px = 20

        w = self._current_weights()
        s = score(hh, w)
        pct = int(s * 100)
        if pct >= 65:   sc, sd, sl = C["danger"], C["danger_dim"], "ALTA"
        elif pct >= 40: sc, sd, sl = C["warn"],   C["warn_dim"],   "MEDIA"
        else:           sc, sd, sl = C["ok"],      C["ok_dim"],     "BAJA"

        # Banner score
        banner = tk.Frame(self.content, bg=sd, highlightbackground=sc, highlightthickness=1)
        banner.pack(fill="x", padx=px, pady=(18, 10))
        bi = tk.Frame(banner, bg=sd)
        bi.pack(fill="x", padx=18, pady=14)
        tk.Label(bi, text="VULNERABILIDAD P1 · SCORE",
                 font=("Helvetica Neue", 9, "bold"), bg=sd, fg=sc).pack(anchor="w")
        row_s = tk.Frame(bi, bg=sd)
        row_s.pack(fill="x", pady=(4, 0))
        self._score_lbl = tk.Label(row_s, text=f"{pct}%",
                                   font=("Helvetica Neue", 40, "bold"), bg=sd, fg=sc)
        self._score_lbl.pack(side="left")
        self._score_level_lbl = tk.Label(row_s, text=f"  {sl}",
                                         font=("Helvetica Neue", 22, "bold"), bg=sd, fg=sc)
        self._score_level_lbl.pack(side="left")
        bar_outer = tk.Frame(bi, bg=C["border"], height=8)
        bar_outer.pack(fill="x", pady=(10, 0))
        self._bar_inner = tk.Frame(bar_outer, bg=sc, height=8)
        self._bar_inner.place(x=0, y=0, relwidth=min(1.0, s))
        self._banner_frame = banner
        self._banner_inner = bi

        # Indicadores con contribución
        i2_pct = int(hh["I1"] / 1050 * 100)
        i21_txt = f"{hh['I21']} mes{'es' if hh['I21']!=1 else ''}" if hh["I21"] > 0 else "Ninguno"
        i25_txt = f"{hh['I25']} año{'s' if hh['I25']!=1 else ''}" if hh["I25"] > 0 else "< 1 año"
        ind_data = [
            ("I1",  f"{hh['I1']} €/mes",      hh["I1"] < 780,    "< 780 €/mes → riesgo"),
            ("I2",  f"{i2_pct}% del umbral",   hh["I1"] < 1050,   "umbral: 1.050 €/mes"),
            ("I3",  f"{hh['I3']:.1f}%",        hh["I3"] > 10,     "> 10% → riesgo"),
            ("I4",  "SÍ" if hh["I4"] else "NO",  bool(hh["I4"]),  "Últimos 12 meses"),
            ("I11", "SÍ" if hh["I11"] else "NO", bool(hh["I11"]), "Bonus / RdC"),
            ("I12", "SÍ" if hh["I12"] else "NO", not bool(hh["I12"]), "Sin acceso = riesgo"),
            ("I21", i21_txt,                   hh["I21"] < 1,     "< 1 mes = riesgo"),
            ("I25", i25_txt,                   hh["I25"] < 2,     "< 2 años = inestable"),
        ]

        tk.Label(self.content, text="Indicadores · contribución al score",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(6, 6))

        for iid, val, is_risk, note in ind_data:
            self._ind_row_phase2(self.content, hh, iid, val, is_risk, note, w, bg, px)

        # Pesos
        tk.Label(self.content, text="Pesos del modelo",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20, 6))
        wcard = tk.Frame(self.content, bg=C["phase2_card"],
                         highlightbackground=C["accent2"], highlightthickness=1)
        wcard.pack(fill="x", padx=px, pady=(0, 10))
        wci = tk.Frame(wcard, bg=C["phase2_card"])
        wci.pack(fill="x", padx=16, pady=14)
        tk.Label(wci, text="Calculados por SLSQP (scipy) · log-loss sobre etiquetas experto. Ajusta con los sliders.",
                 font=("Helvetica Neue", 9), bg=C["phase2_card"], fg=C["muted"]).pack(anchor="w", pady=(0, 10))
        if not hasattr(self, "_w_val_lbls"):  self._w_val_lbls = {}
        if not hasattr(self, "_w_delta_lbls"): self._w_delta_lbls = {}
        for k in IND_KEYS:
            self._weight_slider_row(wci, k, hh)

        # Tabla hogares
        tk.Label(self.content, text="Todos los hogares · score actual",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20, 6))
        tcard = tk.Frame(self.content, bg=C["phase2_card"],
                         highlightbackground=C["border"], highlightthickness=1)
        tcard.pack(fill="x", padx=px, pady=(0, 20))
        tci = tk.Frame(tcard, bg=C["phase2_card"])
        tci.pack(fill="x", padx=14, pady=12)

        self._all_score_labels = {}
        self._all_bar_frames   = {}

        for h in HOUSEHOLDS:
            hs = score(h, w)
            hpct = int(hs * 100)
            hc = C["danger"] if hpct >= 65 else (C["warn"] if hpct >= 40 else C["ok"])
            lbl = self.expert_labels.get(h["id"], h["ground_truth"])
            lbl_col = C["danger"] if lbl == 1 else C["ok"]
            lbl_txt = "vuln." if lbl == 1 else "no vuln."
            is_cur = h["id"] == HOUSEHOLDS[self.current_idx]["id"]
            row_bg = C["sel"] if is_cur else C["phase2_card"]

            row_f = tk.Frame(tci, bg=row_bg,
                             highlightbackground=C["accent"] if is_cur else C["border"],
                             highlightthickness=1 if is_cur else 0)
            row_f.pack(fill="x", pady=2)
            ri = tk.Frame(row_f, bg=row_bg)
            ri.pack(fill="x", padx=10, pady=5)

            tk.Label(ri, text=h["id"], font=("Helvetica Neue", 9, "bold"),
                     bg=row_bg, fg=C["muted"], width=8).pack(side="left")
            tk.Label(ri, text=h["nombre"], font=("Helvetica Neue", 9),
                     bg=row_bg, fg=C["text"], width=22, anchor="w").pack(side="left")

            # perfiles badges
            pf_str = " ".join(h["perfiles"][:3]) if h["perfiles"] else "—"
            tk.Label(ri, text=pf_str, font=("Helvetica Neue", 8),
                     bg=row_bg, fg=C["accent2"], width=12).pack(side="left")

            tk.Label(ri, text=lbl_txt, font=("Helvetica Neue", 9),
                     bg=row_bg, fg=lbl_col, width=8).pack(side="left")
            bf = tk.Frame(ri, bg=C["border"], height=10, width=120)
            bf.pack(side="left", padx=(4, 0))
            bf.pack_propagate(False)
            bfill = tk.Frame(bf, bg=hc, height=10)
            bfill.place(x=0, y=0, width=int(120 * min(1.0, hs)))
            self._all_bar_frames[h["id"]] = (bf, bfill)
            slbl = tk.Label(ri, text=f"{hpct}%", font=("Helvetica Neue", 10, "bold"),
                            bg=row_bg, fg=hc, width=5)
            slbl.pack(side="left", padx=(5, 0))
            self._all_score_labels[h["id"]] = (slbl, row_bg)
            correct = (lbl == 1 and hs >= 0.5) or (lbl == 0 and hs < 0.5)
            tk.Label(ri, text="✓" if correct else "✗",
                     font=("Helvetica Neue", 12, "bold"),
                     bg=row_bg, fg=C["ok"] if correct else C["danger"]).pack(side="left", padx=(3, 0))

    def _ind_row_phase2(self, parent, hh, iid, val, is_risk, note, weights, bg, px):
        rc = C["danger"] if is_risk else C["ok"]
        rd = C["danger_dim"] if is_risk else C["phase2_card"]
        # I2 no tiene peso propio (derivado de I1), mostrarlo solo visualmente
        iid_w = iid if iid in IND_KEYS else "I1"
        contrib = weights.get(iid_w, 0) * ind_norm(hh, iid_w) if iid != "I2" else 0
        total_w = sum(weights.values()) or 1
        contrib_pct = int((contrib / total_w) * 100)

        row_f = tk.Frame(parent, bg=rd if is_risk else C["phase2_card"],
                         highlightbackground=rc if is_risk else C["border"],
                         highlightthickness=1)
        row_f.pack(fill="x", padx=px, pady=(0, 5))
        ri = tk.Frame(row_f, bg=rd if is_risk else C["phase2_card"])
        ri.pack(fill="x", padx=14, pady=8)

        is_pri = iid in ("I1", "I2")
        bbg = C["badge_pri"] if is_pri else C["badge_sec"]
        bfg = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]
        left = tk.Frame(ri, bg=ri["bg"])
        left.pack(side="left")
        tk.Label(left, text=iid, font=("Helvetica Neue", 8, "bold"),
                 bg=bbg, fg=bfg, padx=5, pady=1).pack(anchor="w")
        tk.Label(left, text=IND_NAMES.get(iid, iid), font=("Helvetica Neue", 9),
                 bg=ri["bg"], fg=C["muted"]).pack(anchor="w", pady=(2, 0))

        tk.Label(ri, text=val, font=("Helvetica Neue", 16, "bold"),
                 bg=ri["bg"], fg=rc, width=12, anchor="w").pack(side="left", padx=(14, 0))
        tk.Label(ri, text=note, font=("Helvetica Neue", 9),
                 bg=ri["bg"], fg=C["muted"], width=22, anchor="w").pack(side="left")

        if iid != "I2":
            cb_outer = tk.Frame(ri, bg=C["border"], height=8, width=100)
            cb_outer.pack(side="left", padx=(6, 0))
            cb_outer.pack_propagate(False)
            tk.Frame(cb_outer, bg=rc, height=8,
                     width=min(100, int(100 * min(1.0, contrib * 4)))).place(x=0, y=0)
            tk.Label(ri, text=f"+{contrib_pct}%", font=("Helvetica Neue", 9, "bold"),
                     bg=ri["bg"], fg=rc, width=5).pack(side="left", padx=(5, 0))
        else:
            tk.Label(ri, text="(derivado de I1)", font=("Helvetica Neue", 8),
                     bg=ri["bg"], fg=C["muted"]).pack(side="left", padx=(8, 0))

    def _weight_slider_row(self, parent, k, hh):
        row = tk.Frame(parent, bg=C["phase2_card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text=IND_LONG[k], font=("Helvetica Neue", 10),
                 bg=C["phase2_card"], fg=C["text"], width=38, anchor="w").pack(side="left")
        sl = tk.Scale(row, variable=self.live_weights[k],
                      from_=0.1, to=60.0, resolution=0.1,
                      orient="horizontal", length=180,
                      bg=C["phase2_card"], fg=C["text"],
                      troughcolor=C["slider_bg"], activebackground=C["accent2"],
                      highlightthickness=0, bd=0, sliderrelief="flat",
                      command=lambda val, hh=hh: self._on_weight_change(hh))
        sl.pack(side="left", padx=(6, 0))
        raw = {k2: max(0.001, self.live_weights[k2].get()) for k2 in IND_KEYS}
        t = sum(raw.values()) or 1
        nv = raw[k] / t
        lbl_v = tk.Label(row, text=f"{nv:.3f}", font=("Helvetica Neue", 10, "bold"),
                         bg=C["phase2_card"], fg=C["accent2"], width=6)
        lbl_v.pack(side="left", padx=(5, 0))
        self._w_val_lbls[k] = lbl_v
        delta = nv - self.opt_weights.get(k, 0)
        dlbl = tk.Label(row, text=f"{'↑' if delta>0.0005 else ('↓' if delta<-0.0005 else '·')} {abs(delta):.3f}",
                        font=("Helvetica Neue", 9), bg=C["phase2_card"],
                        fg=C["warn"] if abs(delta) > 0.01 else C["muted"], width=8)
        dlbl.pack(side="left", padx=(4, 0))
        self._w_delta_lbls[k] = (dlbl, self.opt_weights.get(k, 0))

    def _on_weight_change(self, hh):
        w = self._current_weights()
        s = score(hh, w)
        pct = int(s * 100)
        if pct >= 65:   sc, sd, sl = C["danger"], C["danger_dim"], "ALTA"
        elif pct >= 40: sc, sd, sl = C["warn"],   C["warn_dim"],   "MEDIA"
        else:           sc, sd, sl = C["ok"],      C["ok_dim"],     "BAJA"

        if hasattr(self, "_score_lbl") and self._score_lbl.winfo_exists():
            self._score_lbl.configure(text=f"{pct}%", fg=sc, bg=sd)
            self._score_level_lbl.configure(text=f"  {sl}", fg=sc, bg=sd)
            self._banner_inner.configure(bg=sd)
            self._banner_frame.configure(bg=sd, highlightbackground=sc)
            self._bar_inner.configure(bg=sc)
            self._bar_inner.place(relwidth=min(1.0, s))

        if hasattr(self, "_w_val_lbls"):
            raw = {k: max(0.001, self.live_weights[k].get()) for k in IND_KEYS}
            t = sum(raw.values()) or 1
            for k in IND_KEYS:
                nv = raw[k] / t
                if k in self._w_val_lbls and self._w_val_lbls[k].winfo_exists():
                    self._w_val_lbls[k].configure(text=f"{nv:.3f}")
                if k in self._w_delta_lbls:
                    dlbl, opt_v = self._w_delta_lbls[k]
                    if dlbl.winfo_exists():
                        delta = nv - opt_v
                        dtxt = f"{'↑' if delta>0.0005 else ('↓' if delta<-0.0005 else '·')} {abs(delta):.3f}"
                        dlbl.configure(text=dtxt, fg=C["warn"] if abs(delta)>0.01 else C["muted"])

        if hasattr(self, "_all_score_labels"):
            for h in HOUSEHOLDS:
                hs = score(h, w)
                hpct = int(hs * 100)
                hc = C["danger"] if hpct >= 65 else (C["warn"] if hpct >= 40 else C["ok"])
                if h["id"] in self._all_score_labels:
                    slbl, row_bg = self._all_score_labels[h["id"]]
                    if slbl.winfo_exists():
                        slbl.configure(text=f"{hpct}%", fg=hc)
                if h["id"] in self._all_bar_frames:
                    bf, bfill = self._all_bar_frames[h["id"]]
                    if bfill.winfo_exists():
                        bfill.configure(bg=hc)
                        bfill.place(width=int(120 * min(1.0, hs)))

        self._build_sidebar()


if __name__ == "__main__":
    app = App()
    app.mainloop()