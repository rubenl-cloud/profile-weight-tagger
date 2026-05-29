"""
SOCIAREM – P1 Vulnerabilidad Económica Estructural
Proof of Concept · Piloto Messina

Fase 1: revisión de indicadores por hogar + etiquetado experto
Fase 2: pesos optimizados + sliders interactivos + scores en vivo
"""

import tkinter as tk
import math

C = {
    "bg":           "#0F1117",
    "card":         "#1A1D27",
    "card2":        "#21253A",
    "border":       "#2A2E45",
    "accent":       "#4F8EF7",
    "accent2":      "#7C5FD4",
    "text":         "#E8EAF0",
    "muted":        "#7A7F9A",
    "ok":           "#3DD68C",
    "warn":         "#F5A623",
    "danger":       "#E05C5C",
    "ok_dim":       "#1A3D2B",
    "warn_dim":     "#3A2C10",
    "danger_dim":   "#3A1A1A",
    "badge_pri":    "#1C2E54",
    "badge_pri_fg": "#4F8EF7",
    "badge_sec":    "#221C3A",
    "badge_sec_fg": "#A78BFA",
    "sel":          "#1E2A4A",
    "phase2_bg":    "#0A0E1A",
    "phase2_card":  "#141828",
    "slider_bg":    "#1E2235",
}

HOUSEHOLDS = [
    # ── VULNERABILIDAD CRÍTICA (I1 muy bajo, múltiples señales) ──────────────
    {"id": "HOG-01", "nombre": "Rosa M.",             "edad": 67, "composicion": "Pensionista, vive sola",
     "desc": "Pensionista mínima. Piso de alquiler antiguo. Concentrador O₂ nocturno.",
     "I1": 530,  "I3": 18.2, "I4": 1, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-02", "nombre": "Carmela V.",          "edad": 81, "composicion": "Anciana sola, tutela Fundación",
     "desc": "Pensión social mínima. Deuda histórica con comercializadora. Sin microcrédito.",
     "I1": 460,  "I3": 24.1, "I4": 1, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-03", "nombre": "Fatima O.",           "edad": 34, "composicion": "Madre sola, 2 hijos menores",
     "desc": "Trabajo informal, ingresos irregulares. Corte de luz hace 8 meses.",
     "I1": 490,  "I3": 22.7, "I4": 1, "I11": 0, "I12": 1, "ground_truth": 1},
    {"id": "HOG-04", "nombre": "Vincenzo P.",         "edad": 74, "composicion": "Solo, pensión invalidez",
     "desc": "Pensión de invalidez parcial. Piso propio en mal estado. Corte hace 3 meses.",
     "I1": 510,  "I3": 21.3, "I4": 1, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-05", "nombre": "Amina B.",            "edad": 28, "composicion": "Madre sola, 3 hijos pequeños",
     "desc": "Recién llegada. Trabajo en negro esporádico. Sin ninguna ayuda formal registrada.",
     "I1": 380,  "I3": 29.4, "I4": 1, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-06", "nombre": "Concetta e figli",    "edad": 39, "composicion": "Madre sola, 3 hijos",
     "desc": "Renta de ciudadanía (RdC) activa. Alta carga energética por piso deficiente.",
     "I1": 640,  "I3": 19.5, "I4": 1, "I11": 1, "I12": 1, "ground_truth": 1},
    {"id": "HOG-07", "nombre": "Pietrina e Rocco A.", "edad": 78, "composicion": "Pareja ancianos, ambos dependientes",
     "desc": "Dos pensiones sociales. Piso sin calefacción central. Tutela parcial del municipio.",
     "I1": 490,  "I3": 26.8, "I4": 0, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-08", "nombre": "Moussa D.",           "edad": 31, "composicion": "Solo, solicitante asilo",
     "desc": "Acogida temporal. Sin ingresos propios. Centro de acogida cubre alojamiento.",
     "I1": 290,  "I3": 31.0, "I4": 0, "I11": 1, "I12": 1, "ground_truth": 1},

    # ── VULNERABILIDAD ALTA ───────────────────────────────────────────────────
    {"id": "HOG-09", "nombre": "Antonio e Grazia B.", "edad": 72, "composicion": "Pareja jubilados",
     "desc": "Dos pensiones mínimas combinadas. Sin deudas energéticas. Reciben bonus gas.",
     "I1": 820,  "I3": 11.4, "I4": 0, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-10", "nombre": "Marco e Lucia F.",    "edad": 45, "composicion": "Pareja, 1 hijo",
     "desc": "Desempleo reciente. ISEE actualizado. Sin cortes aún pero deuda acumulada.",
     "I1": 710,  "I3": 14.8, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-11", "nombre": "Nadia T.",            "edad": 44, "composicion": "Sola, desempleada larga duración",
     "desc": "ISEE bajo, sin ayudas formales. Sin cortes pero riesgo latente alto.",
     "I1": 580,  "I3": 16.3, "I4": 0, "I11": 0, "I12": 1, "ground_truth": 1},
    {"id": "HOG-12", "nombre": "Giuseppina R.",       "edad": 62, "composicion": "Sola, ex-trabajadora informal",
     "desc": "Sin pensión aún. Pequeños trabajos de limpieza. Calefacción de gas muy cara en invierno.",
     "I1": 670,  "I3": 17.1, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-13", "nombre": "Djamila K.",          "edad": 36, "composicion": "Pareja, 2 hijos, marido en paro",
     "desc": "Ingresos solo de ella, contrato temporal. Bonus energia activo. Riesgo de impago.",
     "I1": 760,  "I3": 15.9, "I4": 0, "I11": 1, "I12": 1, "ground_truth": 1},
    {"id": "HOG-14", "nombre": "Rosario e Maria C.",  "edad": 68, "composicion": "Pareja pensionistas, 1 hijo discapacitado en casa",
     "desc": "Hijo adulto con discapacidad severa. Pensiones combinadas bajas. Gasto eléctrico muy alto.",
     "I1": 780,  "I3": 20.4, "I4": 0, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-15", "nombre": "Leila M.",            "edad": 42, "composicion": "Sola, 1 hijo adolescente",
     "desc": "Separada recientemente. Alquiler nuevo, ingresos reducidos. Primer impago hace 2 meses.",
     "I1": 690,  "I3": 18.7, "I4": 1, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-16", "nombre": "Calogero F.",         "edad": 55, "composicion": "Solo, desempleo estructural",
     "desc": "Nunca ha tenido contrato indefinido. Economía sumergida. Sin acceso a ayudas por falta de ISEE actualizado.",
     "I1": 610,  "I3": 13.2, "I4": 1, "I11": 0, "I12": 0, "ground_truth": 1},

    # ── VULNERABILIDAD MEDIA-ALTA (sobre umbral pero con señales de riesgo) ──
    {"id": "HOG-17", "nombre": "Salvatore C.",        "edad": 58, "composicion": "Solo, trabajador precario",
     "desc": "Ingresos bajos pero estables. Gasto energético moderado. Sin ayudas formales.",
     "I1": 850,  "I3":  8.9, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-18", "nombre": "Piero e Claudia M.",  "edad": 48, "composicion": "Pareja, 2 hijos adolescentes",
     "desc": "Ambos con trabajo precario. ISEE sobre umbral pero carga energética elevada.",
     "I1": 1120, "I3": 13.6, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-19", "nombre": "Sonia P.",            "edad": 33, "composicion": "Sola, contrato parcial",
     "desc": "Trabajo media jornada. ISEE sobre umbral por poco. Sin deudas. Situación frágil.",
     "I1": 1080, "I3": 11.2, "I4": 0, "I11": 0, "I12": 1, "ground_truth": 0},
    {"id": "HOG-20", "nombre": "Filippo e Serena R.", "edad": 52, "composicion": "Pareja, trabajo temporal",
     "desc": "Ambos con contratos estacionales. ISEE alto en temporada pero ingresos intermitentes.",
     "I1": 1150, "I3":  9.8, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-21", "nombre": "Domenico A.",         "edad": 61, "composicion": "Solo, pensión anticipada",
     "desc": "Pensión anticipada media. Piso en propiedad. Gasto energético contenido.",
     "I1": 1200, "I3":  7.4, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-22", "nombre": "Ylenia e Marco T.",   "edad": 38, "composicion": "Pareja, sin hijos, ambos empleados",
     "desc": "Ingresos dobles pero ISEE elevado por bienes inmobiliarios declarados. Gasto energético normal.",
     "I1": 1380, "I3":  6.9, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-23", "nombre": "Antonino L.",         "edad": 47, "composicion": "Solo, autónomo irregular",
     "desc": "Autónomo con ingresos muy variables. Año bueno: ISEE alto. Año malo: impago energía.",
     "I1": 1090, "I3": 12.1, "I4": 1, "I11": 0, "I12": 1, "ground_truth": 1},
    {"id": "HOG-24", "nombre": "Bruna C.",            "edad": 70, "composicion": "Sola, pensión media",
     "desc": "Pensión media suficiente pero piso antiguo con alto consumo. Sin deudas.",
     "I1": 1100, "I3": 14.3, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-25", "nombre": "Ivan e Olena S.",     "edad": 43, "composicion": "Pareja inmigrante, 1 hijo",
     "desc": "Ucranianos. Trabajo estable de él, ella cuidadora informal no remunerada. ISEE por encima del umbral.",
     "I1": 1060, "I3": 10.8, "I4": 0, "I11": 0, "I12": 1, "ground_truth": 0},

    # ── CASOS AMBIGUOS / FRONTERA ─────────────────────────────────────────────
    {"id": "HOG-26", "nombre": "Carmelo e Ida B.",    "edad": 65, "composicion": "Pareja, jubilación parcial",
     "desc": "Pensión parcial y pequeño negocio. ISEE justo en el umbral. Carga energética moderada.",
     "I1": 1040, "I3": 10.1, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-27", "nombre": "Tiziana F.",          "edad": 50, "composicion": "Sola, cuidadora familiar no remunerada",
     "desc": "Cuida a su madre con Alzheimer. Sin ingresos propios. ISEE bajo por economía familiar.",
     "I1": 720,  "I3":  9.3, "I4": 0, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-28", "nombre": "Gaetano P.",          "edad": 35, "composicion": "Solo, ex-recluso, reinserción",
     "desc": "Salido del sistema penitenciario hace 6 meses. Trabajo de reinserción. Sin historial crediticio.",
     "I1": 680,  "I3":  8.1, "I4": 0, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-29", "nombre": "Lucia e figli",       "edad": 41, "composicion": "Madre sola, 1 hijo con TEA",
     "desc": "Trabajo a tiempo parcial para cuidar a hijo con autismo. RdC activa. Carga eléctrica alta.",
     "I1": 730,  "I3": 16.8, "I4": 0, "I11": 1, "I12": 1, "ground_truth": 1},
    {"id": "HOG-30", "nombre": "Sebastiano M.",       "edad": 26, "composicion": "Solo, NEET",
     "desc": "Ni estudia ni trabaja. Vive con ayuda de familiares. Sin ISEE propio declarado.",
     "I1": 420,  "I3":  7.2, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-31", "nombre": "Grazia e Luigi C.",   "edad": 55, "composicion": "Pareja, ambos con trabajo estacional",
     "desc": "Ingresos buenos en verano (turismo), muy bajos en invierno. ISEE promedio engañoso.",
     "I1": 970,  "I3": 12.4, "I4": 1, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-32", "nombre": "Youssef A.",          "edad": 38, "composicion": "Solo, trabajador agrícola",
     "desc": "Trabajo agrícola estacional. Alojamiento en cortijo incluido. ISEE bajo pero necesidades básicas cubiertas.",
     "I1": 560,  "I3":  6.4, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-33", "nombre": "Paola N.",            "edad": 59, "composicion": "Sola, enferma crónica",
     "desc": "Fibromialgia severa. Incapacidad parcial reconocida. Gasto sanitario alto que reduce renta disponible.",
     "I1": 800,  "I3": 17.9, "I4": 0, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-34", "nombre": "Emanuele e Sandra R.","edad": 51, "composicion": "Pareja, hijos independientes",
     "desc": "Ambos con trabajo a tiempo parcial. ISEE limítrofe. Situación estable.",
     "I1": 1050, "I3":  9.1, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},

    # ── SIN VULNERABILIDAD ECONÓMICA (sobre umbral, situación estable) ────────
    {"id": "HOG-35", "nombre": "Giuseppe N.",         "edad": 29, "composicion": "Solo, empleado",
     "desc": "Contrato fijo reciente. ISEE sobre umbral. Situación estabilizándose.",
     "I1": 940,  "I3":  7.2, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-36", "nombre": "Roberta e Franco L.", "edad": 44, "composicion": "Pareja, 2 hijos, clase media",
     "desc": "Ambos empleados fijos. Piso en propiedad. Gasto energético controlado.",
     "I1": 1680, "I3":  5.8, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-37", "nombre": "Mario T.",            "edad": 53, "composicion": "Solo, funcionario",
     "desc": "Funcionario municipal. Ingresos estables. Sin ninguna señal de vulnerabilidad.",
     "I1": 1540, "I3":  4.9, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-38", "nombre": "Daniela e Luca P.",   "edad": 37, "composicion": "Pareja joven, ambos empleados",
     "desc": "Ambos con contratos indefinidos recientes. Piso de alquiler moderno. Sin deudas.",
     "I1": 1420, "I3":  6.1, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-39", "nombre": "Silvana R.",          "edad": 66, "composicion": "Sola, pensión media-alta",
     "desc": "Pensión de empleada bancaria. Piso propio pagado. Gasto energético moderado.",
     "I1": 1310, "I3":  7.3, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-40", "nombre": "Carmelo G.",          "edad": 41, "composicion": "Solo, profesional liberal",
     "desc": "Abogado con clientela estable. ISEE alto. Sin ninguna señal de riesgo.",
     "I1": 2100, "I3":  3.2, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-41", "nombre": "Nunzia e Aldo C.",    "edad": 60, "composicion": "Pareja, pensiones medias",
     "desc": "Jubilados con pensiones dignas. Piso en propiedad. Viajes frecuentes.",
     "I1": 1750, "I3":  5.1, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-42", "nombre": "Federica M.",         "edad": 32, "composicion": "Sola, ingeniería",
     "desc": "Contrato indefinido en empresa privada. Sin cargas. Ahorro mensual positivo.",
     "I1": 1890, "I3":  4.4, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-43", "nombre": "Orazio e Valeria B.", "edad": 49, "composicion": "Pareja, empresa familiar pequeña",
     "desc": "Negocio de hostelería estable. Ingresos buenos. Sin deudas energéticas.",
     "I1": 1600, "I3":  6.7, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},

    # ── CASOS ESPECIALES / PARADOJAS ─────────────────────────────────────────
    {"id": "HOG-44", "nombre": "Roberto A.",          "edad": 48, "composicion": "Solo, desahucio reciente",
     "desc": "ISEE aparentemente alto (año anterior bueno) pero desahuciado hace 2 meses. Ahora en albergue.",
     "I1": 1100, "I3": 22.0, "I4": 1, "I11": 1, "I12": 0, "ground_truth": 1},
    {"id": "HOG-45", "nombre": "Antonella e figli",   "edad": 43, "composicion": "Madre sola, 4 hijos",
     "desc": "ISEE bajo por escala de equivalencia. En términos absolutos los ingresos son razonables para el número de miembros.",
     "I1": 740,  "I3": 11.3, "I4": 0, "I11": 1, "I12": 1, "ground_truth": 1},
    {"id": "HOG-46", "nombre": "Enzo F.",             "edad": 57, "composicion": "Solo, ex-adicción, recuperación",
     "desc": "En programa de recuperación. Trabajo protegido. ISEE bajo pero situación mejorando.",
     "I1": 620,  "I3":  9.7, "I4": 0, "I11": 1, "I12": 1, "ground_truth": 1},
    {"id": "HOG-47", "nombre": "Miriam e Abebe T.",   "edad": 35, "composicion": "Pareja con permiso de residencia reciente",
     "desc": "Ambos trabajando pero sin historial ISEE consolidado. Carga energética alta en piso compartido.",
     "I1": 870,  "I3": 13.8, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-48", "nombre": "Lina V.",             "edad": 77, "composicion": "Anciana sola, heredera",
     "desc": "ISEE alto por patrimonio inmobiliario heredado, pero pensión social mínima. Liquidez muy baja.",
     "I1": 1250, "I3": 19.6, "I4": 1, "I11": 0, "I12": 0, "ground_truth": 1},
    {"id": "HOG-49", "nombre": "Cristian e Alina P.", "edad": 30, "composicion": "Pareja joven, recién llegados",
     "desc": "Rumaneses. Trabajan en logística. ISEE sobre umbral pero sin red de apoyo ni acceso a microcrédito.",
     "I1": 1130, "I3":  8.3, "I4": 0, "I11": 0, "I12": 0, "ground_truth": 0},
    {"id": "HOG-50", "nombre": "Tancredi M.",         "edad": 24, "composicion": "Solo, estudiante trabajador",
     "desc": "Estudia y trabaja. Ingresos bajos pero temporales. Sin cargas familiares. Trayectoria ascendente.",
     "I1": 760,  "I3":  8.8, "I4": 0, "I11": 0, "I12": 1, "ground_truth": 0},
]

IND_KEYS   = ["I1", "I2", "I3", "I4", "I11", "I12"]
IND_NAMES  = {
    "I1":  "Renta neta equiv.",
    "I2":  "Bajo umbral pobreza",
    "I3":  "Carga energética",
    "I4":  "Impago / corte",
    "I11": "Recibe ayudas sociales",
    "I12": "Acceso a microcrédito",
}
IND_LONG = {
    "I1":  "I1 – Renta neta mensual equivalente",
    "I2":  "I2 – Hogar bajo umbral de pobreza relativa",
    "I3":  "I3 – Carga energética del hogar",
    "I4":  "I4 – Impago o corte de suministro",
    "I11": "I11 – Acceso a ayudas sociales o energéticas",
    "I12": "I12 – Acceso a microcrédito / apoyo comunitario",
}
INIT_WEIGHTS = {"I1": 0.30, "I2": 0.25, "I3": 0.20, "I4": 0.10, "I11": 0.10, "I12": 0.05}


def ind_norm(hh, k):
    if k == "I1":  return max(0.0, min(1.0, (1200 - hh["I1"]) / 800))
    if k == "I2":  return max(0.0, min(1.0, (1050 - hh["I1"]) / 1050))
    if k == "I3":  return max(0.0, min(1.0, (hh["I3"] - 5) / 25))
    if k == "I4":  return float(hh["I4"])
    if k == "I11": return float(hh["I11"])
    if k == "I12": return 1.0 - float(hh["I12"])
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
        self.geometry("1140x780")
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.phase = 1               # 1 = etiquetado, 2 = ajuste pesos
        self.current_idx = 0
        self.expert_labels = {}
        self.opt_weights = None
        self.live_weights = None     # DoubleVars en fase 2
        self._build()
        self._select(0)

    # ── layout fijo ──────────────────────────────────────────────────────────
    def _build(self):
        # sidebar
        self.sidebar = tk.Frame(self, bg=C["card"], width=228)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # área derecha
        self.right = tk.Frame(self, bg=C["bg"])
        self.right.pack(side="left", fill="both", expand=True)

        # header
        self.hdr = tk.Frame(self.right, bg=C["card"], height=86)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)
        self.lbl_id    = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"])
        self.lbl_name  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 17, "bold"), bg=C["card"], fg=C["text"])
        self.lbl_comp  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 11), bg=C["card"], fg=C["muted"])
        self.lbl_desc  = tk.Label(self.hdr, text="", font=("Helvetica Neue", 9),  bg=C["card"], fg=C["muted"],
                                  wraplength=640, justify="left")
        self.lbl_id.place(x=22, y=10)
        self.lbl_name.place(x=22, y=24)
        self.lbl_comp.place(x=22, y=50)
        self.lbl_desc.place(x=22, y=66)
        nav = tk.Frame(self.hdr, bg=C["card"])
        nav.place(relx=1.0, x=-14, y=30, anchor="ne")
        tk.Button(nav, text="←", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2", command=lambda: self._select((self.current_idx-1)%len(HOUSEHOLDS))).pack(side="left")
        self.lbl_nav = tk.Label(nav, text="", font=("Helvetica Neue", 10), bg=C["card"], fg=C["muted"])
        self.lbl_nav.pack(side="left", padx=4)
        tk.Button(nav, text="→", font=("Helvetica Neue", 13), bg=C["card"], fg=C["accent"],
                  relief="flat", cursor="hand2", command=lambda: self._select((self.current_idx+1)%len(HOUSEHOLDS))).pack(side="left")

        tk.Frame(self.right, bg=C["border"], height=1).pack(fill="x")

        # canvas scroll
        self._canvas = tk.Canvas(self.right, bg=C["bg"], highlightthickness=0)
        vsb = tk.Scrollbar(self.right, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(self._canvas, bg=C["bg"])
        self._cwin = self._canvas.create_window((0,0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda e: (
            self._canvas.configure(scrollregion=self._canvas.bbox("all")),
            self._canvas.itemconfig(self._cwin, width=self._canvas.winfo_width())
        ))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._cwin, width=e.width))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._canvas.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind("<Button-5>",   lambda e: self._canvas.yview_scroll(1, "units"))
        self.content.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
        self.content.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"))
        self.content.bind("<Button-5>",   lambda e: self._canvas.yview_scroll(1, "units"))

        def _bind_main_scroll(widget):
            widget.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
            widget.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>",   lambda e: self._canvas.yview_scroll(1, "units"))
        self._bind_main_scroll = _bind_main_scroll

    def _build_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()

        # ── Cabecera fija ─────────────────────────────────────────────────────
        top = tk.Frame(self.sidebar, bg=C["card"])
        top.pack(side="top", fill="x")

        tk.Label(top, text="SOCIAREM", font=("Helvetica Neue", 11, "bold"),
                 bg=C["card"], fg=C["accent"]).pack(anchor="w", padx=16, pady=(18,0))
        tk.Label(top, text="Piloto Messina · P1",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(0,10))
        tk.Frame(top, bg=C["border"], height=1).pack(fill="x")

        phase_txt = "FASE 1 · Etiquetado" if self.phase == 1 else "FASE 2 · Ajuste de pesos"
        phase_col = C["accent"] if self.phase == 1 else C["accent2"]
        tk.Label(top, text=phase_txt, font=("Helvetica Neue", 9, "bold"),
                 bg=C["card"], fg=phase_col).pack(anchor="w", padx=16, pady=(8,4))
        tk.Label(top, text="Hogares", font=("Helvetica Neue", 8, "bold"),
                 bg=C["card"], fg=C["muted"]).pack(anchor="w", padx=16, pady=(0,4))

        # ── Pie fijo (botón optimizar / volver) ───────────────────────────────
        bottom = tk.Frame(self.sidebar, bg=C["card"])
        bottom.pack(side="bottom", fill="x")
        tk.Frame(bottom, bg=C["border"], height=1).pack(fill="x")

        if self.phase == 1:
            self.opt_btn = tk.Button(
                bottom, text="⚡  Optimizar pesos",
                font=("Helvetica Neue", 10, "bold"),
                bg=C["accent2"], fg=C["text"],
                relief="flat", cursor="hand2", padx=12, pady=7,
                command=self._run_optimization
            )
            self.opt_btn.pack(fill="x", padx=8, pady=(6,4))
            self.progress_lbl = tk.Label(bottom, text="",
                                         font=("Helvetica Neue", 9),
                                         bg=C["card"], fg=C["muted"], wraplength=196)
            self.progress_lbl.pack(anchor="w", padx=12, pady=(0,8))
        else:
            tk.Button(
                bottom, text="← Volver a fase 1",
                font=("Helvetica Neue", 9),
                bg=C["card2"], fg=C["muted"],
                relief="flat", cursor="hand2", padx=10, pady=5,
                command=self._back_to_phase1
            ).pack(fill="x", padx=8, pady=6)

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
            sb_canvas.itemconfig(sb_win, width=sb_canvas.winfo_width())
        ))
        sb_canvas.bind("<Configure>", lambda e: sb_canvas.itemconfig(sb_win, width=e.width))

        # scroll con rueda solo cuando el cursor está sobre la sidebar
        def _sb_scroll(e):
            sb_canvas.yview_scroll(-1 * (e.delta // 120), "units")
        def _sb_scroll_up(e):
            sb_canvas.yview_scroll(-1, "units")
        def _sb_scroll_down(e):
            sb_canvas.yview_scroll(1, "units")

        sb_canvas.bind("<MouseWheel>", _sb_scroll)
        sb_canvas.bind("<Button-4>",   _sb_scroll_up)
        sb_canvas.bind("<Button-5>",   _sb_scroll_down)
        sb_frame.bind("<MouseWheel>",  _sb_scroll)
        sb_frame.bind("<Button-4>",    _sb_scroll_up)
        sb_frame.bind("<Button-5>",    _sb_scroll_down)

        self.sidebar_btns = []
        for i, hh in enumerate(HOUSEHOLDS):
            extra = ""
            dot_col = C["muted"]
            if self.phase == 2 and self.opt_weights:
                s = score(hh, self._current_weights())
                pct = int(s * 100)
                extra = f"  {pct}%"
                dot_col = C["danger"] if pct >= 65 else (C["warn"] if pct >= 40 else C["ok"])
            elif self.phase == 1:
                lbl = self.expert_labels.get(hh["id"])
                if lbl == 1:   dot_col = C["danger"]
                elif lbl == 0: dot_col = C["ok"]

            fg_col = dot_col if self.expert_labels.get(hh["id"]) is not None else C["text"]
            btn = tk.Button(
                sb_frame,
                text=f"{hh['id']}  {hh['nombre']}{extra}",
                font=("Helvetica Neue", 9),
                anchor="w", padx=10, pady=5,
                relief="flat", cursor="hand2",
                bg=C["sel"] if i == self.current_idx else C["card"],
                fg=fg_col,
                activebackground=C["sel"], activeforeground=C["text"],
                command=lambda idx=i: self._select(idx)
            )
            btn.pack(fill="x", padx=4)
            # propagar scroll desde los botones también
            btn.bind("<MouseWheel>", _sb_scroll)
            btn.bind("<Button-4>",   _sb_scroll_up)
            btn.bind("<Button-5>",   _sb_scroll_down)
            self.sidebar_btns.append(btn)

    # ── navegación ────────────────────────────────────────────────────────────
    def _select(self, idx):
        self.current_idx = idx
        self._build_sidebar()
        hh = HOUSEHOLDS[idx]
        self.lbl_id.configure(text=hh["id"])
        self.lbl_name.configure(text=f"{hh['nombre']}  ·  {hh['edad']} años")
        self.lbl_comp.configure(text=hh["composicion"])
        self.lbl_desc.configure(text=hh["desc"])
        self.lbl_nav.configure(text=f"{idx+1}/{len(HOUSEHOLDS)}")
        for w in self.content.winfo_children():
            w.destroy()
        if self.phase == 1:
            self._render_phase1(hh)
        else:
            self._render_phase2(hh)

    def _propagate_scroll(self, widget):
        """Propaga el scroll del canvas principal a todos los widgets hijos."""
        widget.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
        widget.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"))
        widget.bind("<Button-5>",   lambda e: self._canvas.yview_scroll(1, "units"))
        for child in widget.winfo_children():
            self._propagate_scroll(child)


        if self.live_weights:
            raw = {k: max(0.001, self.live_weights[k].get()) for k in IND_KEYS}
            t = sum(raw.values()) or 1
            return {k: v/t for k, v in raw.items()}
        return self.opt_weights or INIT_WEIGHTS.copy()

    # ─────────────────────────────────────────────────────────────────────────
    # FASE 1
    # ─────────────────────────────────────────────────────────────────────────
    def _render_phase1(self, hh):
        px = 20

        # Indicadores
        tk.Label(self.content, text="Indicadores",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(18,6))

        grid = tk.Frame(self.content, bg=C["bg"])
        grid.pack(fill="x", padx=px)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        indicators = [
            ("I1",  "Renta neta equiv.",     "primario",
             f"{hh['I1']} €/mes",   "< 780 €/mes → riesgo",      hh["I1"] < 780,       "DS2 · ISEE"),
            ("I2",  "Bajo umbral pobreza",   "primario",
             f"{int(hh['I1'] / 1050 * 100)} % del umbral",  "umbral: 1.050 €/mes equiv.",  hh["I1"] < 1050,  "DS2 · ISEE"),
            ("I3",  "Carga energética",      "secundario",
             f"{hh['I3']:.1f} %",  "> 10 % → alto riesgo",       hh["I3"] > 10,        "DS4 · DS14 · facturas"),
            ("I4",  "Impago / corte",        "secundario",
             "SÍ" if hh["I4"] else "NO",     "Últimos 12 meses",       bool(hh["I4"]),       "DS8 · autodeclaración"),
            ("I11", "Recibe ayudas",         "secundario",
             "SÍ" if hh["I11"] else "NO",    "Bonus energía / RdC",    bool(hh["I11"]),      "DS8 · Fundación Messina"),
            ("I12", "Acceso a microcrédito", "secundario",
             "SÍ" if hh["I12"] else "NO",    "Apoyo financiero comun.", bool(hh["I12"]),      "DS7 · DS27 · ONG"),
        ]
        for i, (iid, name, role, value, note, is_risk, source) in enumerate(indicators):
            self._ind_card(grid, iid, name, role, value, note, is_risk, source, i//3, i%3)

        # Validación experto
        tk.Label(self.content, text="Validación experto",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", padx=px, pady=(20,6))

        vcard = tk.Frame(self.content, bg=C["card"],
                         highlightbackground=C["border"], highlightthickness=1)
        vcard.pack(fill="x", padx=px, pady=(0,16))
        vc = tk.Frame(vcard, bg=C["card"])
        vc.pack(fill="x", padx=16, pady=14)

        tk.Label(vc, text="¿Este hogar presenta vulnerabilidad P1 · económica estructural?",
                 font=("Helvetica Neue", 11), bg=C["card"], fg=C["text"]).pack(anchor="w")
        tk.Label(vc, text="La etiqueta experto se usa para optimizar los pesos del modelo.",
                 font=("Helvetica Neue", 9), bg=C["card"], fg=C["muted"]).pack(anchor="w", pady=(2,10))

        brow = tk.Frame(vc, bg=C["card"])
        brow.pack(anchor="w")
        cur = self.expert_labels.get(hh["id"])
        for val, lbl, bg_a, fg_a in [
            (1, "SÍ – vulnerable P1",   C["danger_dim"], C["danger"]),
            (0, "NO – no vulnerable",   C["ok_dim"],     C["ok"]),
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
                      ).pack(side="left", padx=(0,10))

        n_lbl = len(self.expert_labels)
        n_total = len(HOUSEHOLDS)
        status = f"{n_lbl}/{n_total} hogares etiquetados"
        scol = C["ok"] if n_lbl == n_total else C["muted"]
        if n_lbl == n_total:
            status += "  ·  ¡Listo para optimizar!"
        tk.Label(vc, text=status, font=("Helvetica Neue", 9),
                 bg=C["card"], fg=scol).pack(anchor="w", pady=(10,0))

        self._propagate_scroll(self.content)

    def _ind_card(self, parent, iid, name, role, value, note, is_risk, source, row, col):
        is_pri = role == "primario"
        rc  = C["danger"] if is_risk else C["ok"]
        rdim= C["danger_dim"] if is_risk else C["ok_dim"]
        bbg = C["badge_pri"] if is_pri else C["badge_sec"]
        bfg = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]

        f = tk.Frame(parent, bg=C["card"],
                     highlightbackground=rc if is_risk else C["border"],
                     highlightthickness=1)
        f.grid(row=row, column=col,
               padx=(0,8) if col < 2 else 0, pady=(0,8), sticky="nsew")
        inn = tk.Frame(f, bg=C["card"])
        inn.pack(fill="both", expand=True, padx=12, pady=10)

        top = tk.Frame(inn, bg=C["card"])
        top.pack(fill="x")
        tk.Label(top, text=iid, font=("Helvetica Neue", 9, "bold"),
                 bg=bbg, fg=bfg, padx=6, pady=2).pack(side="left")
        tk.Label(top, text="PRIMARIO" if is_pri else "SECUNDARIO",
                 font=("Helvetica Neue", 8), bg=C["card"], fg=bfg).pack(side="left", padx=(6,0))

        tk.Label(inn, text=name, font=("Helvetica Neue", 10, "bold"),
                 bg=C["card"], fg=C["text"], anchor="w").pack(fill="x", pady=(4,0))
        tk.Label(inn, text=value, font=("Helvetica Neue", 22, "bold"),
                 bg=C["card"], fg=rc, anchor="w").pack(fill="x", pady=(2,0))
        tk.Label(inn, text=note, font=("Helvetica Neue", 9),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")
        tk.Frame(inn, bg=C["border"], height=1).pack(fill="x", pady=(6,4))
        tk.Label(inn, text=source, font=("Helvetica Neue", 8),
                 bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")

    def _set_expert(self, hid, val):
        was_unlabeled = hid not in self.expert_labels
        self.expert_labels[hid] = val
        n = len(self.expert_labels)
        if hasattr(self, "progress_lbl"):
            self.progress_lbl.configure(
                text=f"{n}/{len(HOUSEHOLDS)} etiquetados" + ("\n¡Listo!" if n == len(HOUSEHOLDS) else ""),
                fg=C["ok"] if n == len(HOUSEHOLDS) else C["muted"]
            )
        if was_unlabeled and self.current_idx < len(HOUSEHOLDS) - 1:
            self._select(self.current_idx + 1)
        else:
            self._select(self.current_idx)

    def _run_optimization(self):
        if len(self.expert_labels) < 5:
            self.progress_lbl.configure(
                text="Necesitas ≥ 5 hogares etiquetados.", fg=C["warn"])
            return
        self.progress_lbl.configure(text="Optimizando…", fg=C["accent"])
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
        # Crear DoubleVars para sliders (0–100, representan peso*100 pre-normalización)
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

        # ── Score banner ─────────────────────────────────────────────────────
        banner = tk.Frame(self.content, bg=sd,
                          highlightbackground=sc, highlightthickness=1)
        banner.pack(fill="x", padx=px, pady=(18,10))
        bi = tk.Frame(banner, bg=sd)
        bi.pack(fill="x", padx=18, pady=14)

        tk.Label(bi, text="VULNERABILIDAD P1 · SCORE",
                 font=("Helvetica Neue", 9, "bold"), bg=sd, fg=sc).pack(anchor="w")
        row_s = tk.Frame(bi, bg=sd)
        row_s.pack(fill="x", pady=(4,0))

        self._score_lbl = tk.Label(row_s, text=f"{pct}%",
                                   font=("Helvetica Neue", 40, "bold"), bg=sd, fg=sc)
        self._score_lbl.pack(side="left")
        self._score_level_lbl = tk.Label(row_s, text=f"  {sl}",
                                         font=("Helvetica Neue", 22, "bold"), bg=sd, fg=sc)
        self._score_level_lbl.pack(side="left")

        # barra
        bar_outer = tk.Frame(bi, bg=C["border"], height=8)
        bar_outer.pack(fill="x", pady=(10,0))
        self._bar_inner = tk.Frame(bar_outer, bg=sc, height=8)
        self._bar_inner.place(x=0, y=0, relwidth=min(1.0, s))

        # guardar refs para update live
        self._banner_frame = banner
        self._banner_inner = bi
        self._score_color  = sc
        self._score_dim    = sd

        # ── Indicadores con peso visual ───────────────────────────────────────
        tk.Label(self.content, text="Indicadores · contribución al score",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(6,6))

        ind_data = [
            ("I1",  f"{hh['I1']} €/mes",           hh["I1"] < 780,  "< 780 €/mes → riesgo"),
            ("I2",  f"{int(hh['I1'] / 1050 * 100)} % umbral",  hh["I1"] < 1050,   "umbral: 1.050 €/mes"),
            ("I3",  f"{hh['I3']:.1f} %",            hh["I3"] > 10,   "> 10 % → riesgo"),
            ("I4",  "SÍ" if hh["I4"] else "NO",    bool(hh["I4"]),  "Últimos 12 meses"),
            ("I11", "SÍ" if hh["I11"] else "NO",   bool(hh["I11"]), "Bonus energía / RdC"),
            ("I12", "SÍ" if hh["I12"] else "NO",   bool(hh["I12"]), "Apoyo financiero comun."),
        ]
        self._contrib_bars = {}
        for iid, val, is_risk, note in ind_data:
            self._ind_row_phase2(self.content, hh, iid, val, is_risk, note, w, bg, px)

        # ── Panel de pesos ────────────────────────────────────────────────────
        tk.Label(self.content, text="Pesos del modelo",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20,6))

        wcard = tk.Frame(self.content, bg=C["phase2_card"],
                         highlightbackground=C["accent2"], highlightthickness=1)
        wcard.pack(fill="x", padx=px, pady=(0,10))
        wci = tk.Frame(wcard, bg=C["phase2_card"])
        wci.pack(fill="x", padx=16, pady=14)

        tk.Label(wci,
                 text="Pesos calculados por SLSQP (scipy) · log-loss sobre etiquetas experto. Ajusta con los sliders.",
                 font=("Helvetica Neue", 9), bg=C["phase2_card"], fg=C["muted"]).pack(anchor="w", pady=(0,10))

        for k in IND_KEYS:
            self._weight_slider_row(wci, k, hh, bg)

        # ── Tabla todos los hogares ───────────────────────────────────────────
        tk.Label(self.content, text="Todos los hogares · score actual",
                 font=("Helvetica Neue", 12, "bold"),
                 bg=bg, fg=C["text"]).pack(anchor="w", padx=px, pady=(20,6))

        tcard = tk.Frame(self.content, bg=C["phase2_card"],
                         highlightbackground=C["border"], highlightthickness=1)
        tcard.pack(fill="x", padx=px, pady=(0,20))
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
            lbl_txt = "vulnerable" if lbl == 1 else "no vuln."
            is_cur = h["id"] == HOUSEHOLDS[self.current_idx]["id"]

            row_bg = C["sel"] if is_cur else C["phase2_card"]
            row_f = tk.Frame(tci, bg=row_bg,
                             highlightbackground=C["accent"] if is_cur else C["border"],
                             highlightthickness=1 if is_cur else 0)
            row_f.pack(fill="x", pady=2)
            ri = tk.Frame(row_f, bg=row_bg)
            ri.pack(fill="x", padx=10, pady=6)

            tk.Label(ri, text=h["id"], font=("Helvetica Neue", 9, "bold"),
                     bg=row_bg, fg=C["muted"], width=8).pack(side="left")
            tk.Label(ri, text=h["nombre"], font=("Helvetica Neue", 10),
                     bg=row_bg, fg=C["text"], width=24, anchor="w").pack(side="left")
            tk.Label(ri, text=lbl_txt, font=("Helvetica Neue", 9),
                     bg=row_bg, fg=lbl_col, width=10).pack(side="left")

            # barra mini
            bf = tk.Frame(ri, bg=C["border"], height=10, width=140)
            bf.pack(side="left", padx=(6,0))
            bf.pack_propagate(False)
            bfill = tk.Frame(bf, bg=hc, height=10)
            bfill.place(x=0, y=0, width=int(140 * min(1.0, hs)))
            self._all_bar_frames[h["id"]] = (bf, bfill)

            slbl = tk.Label(ri, text=f"{hpct}%", font=("Helvetica Neue", 10, "bold"),
                            bg=row_bg, fg=hc, width=5)
            slbl.pack(side="left", padx=(6,0))
            self._all_score_labels[h["id"]] = (slbl, row_bg)

            correct = (lbl == 1 and hs >= 0.5) or (lbl == 0 and hs < 0.5)
            tk.Label(ri, text="✓" if correct else "✗",
                     font=("Helvetica Neue", 12, "bold"),
                     bg=row_bg, fg=C["ok"] if correct else C["danger"]).pack(side="left", padx=(4,0))

        self._propagate_scroll(self.content)

    def _ind_row_phase2(self, parent, hh, iid, val, is_risk, note, weights, bg, px):
        rc = C["danger"] if is_risk else C["ok"]
        rd = C["danger_dim"] if is_risk else C["ok_dim"]
        contrib = weights[iid] * ind_norm(hh, iid)
        total_w = sum(weights.values()) or 1
        contrib_pct = int((contrib / total_w) * 100)

        row_f = tk.Frame(parent, bg=rd if is_risk else C["phase2_card"],
                         highlightbackground=rc if is_risk else C["border"],
                         highlightthickness=1)
        row_f.pack(fill="x", padx=px, pady=(0,5))
        ri = tk.Frame(row_f, bg=rd if is_risk else C["phase2_card"])
        ri.pack(fill="x", padx=14, pady=9)

        # nombre + badge
        left = tk.Frame(ri, bg=ri["bg"])
        left.pack(side="left")
        is_pri = iid in ("I1", "I2")
        bbg = C["badge_pri"] if is_pri else C["badge_sec"]
        bfg = C["badge_pri_fg"] if is_pri else C["badge_sec_fg"]
        tk.Label(left, text=iid, font=("Helvetica Neue", 8, "bold"),
                 bg=bbg, fg=bfg, padx=5, pady=1).pack(anchor="w")
        tk.Label(left, text=IND_NAMES[iid], font=("Helvetica Neue", 9),
                 bg=ri["bg"], fg=C["muted"]).pack(anchor="w", pady=(2,0))

        # valor
        tk.Label(ri, text=val, font=("Helvetica Neue", 18, "bold"),
                 bg=ri["bg"], fg=rc, width=10, anchor="w").pack(side="left", padx=(16,0))

        # nota
        tk.Label(ri, text=note, font=("Helvetica Neue", 9),
                 bg=ri["bg"], fg=C["muted"], width=24, anchor="w").pack(side="left")

        # contribución al score
        cb_outer = tk.Frame(ri, bg=C["border"], height=8, width=120)
        cb_outer.pack(side="left", padx=(8,0))
        cb_outer.pack_propagate(False)
        cb_fill = tk.Frame(cb_outer, bg=rc, height=8)
        cb_fill.place(x=0, y=0, width=min(120, int(120 * min(1.0, contrib * 3))))

        tk.Label(ri, text=f"+{contrib_pct}%", font=("Helvetica Neue", 9, "bold"),
                 bg=ri["bg"], fg=rc, width=6).pack(side="left", padx=(6,0))

    def _weight_slider_row(self, parent, k, hh, bg):
        row = tk.Frame(parent, bg=C["phase2_card"])
        row.pack(fill="x", pady=4)

        # nombre
        tk.Label(row, text=IND_LONG[k], font=("Helvetica Neue", 10),
                 bg=C["phase2_card"], fg=C["text"], width=36, anchor="w").pack(side="left")

        # slider
        sl = tk.Scale(row, variable=self.live_weights[k],
                      from_=0.1, to=60.0, resolution=0.1,
                      orient="horizontal", length=200,
                      bg=C["phase2_card"], fg=C["text"],
                      troughcolor=C["slider_bg"], activebackground=C["accent2"],
                      highlightthickness=0, bd=0, sliderrelief="flat",
                      command=lambda val, hh=hh: self._on_weight_change(hh))
        sl.pack(side="left", padx=(8,0))

        # valor normalizado
        raw = {k2: max(0.001, self.live_weights[k2].get()) for k2 in IND_KEYS}
        t = sum(raw.values()) or 1
        norm_val = raw[k] / t
        self._w_val_lbl = tk.Label(row, text=f"{norm_val:.3f}",
                                    font=("Helvetica Neue", 10, "bold"),
                                    bg=C["phase2_card"], fg=C["accent2"], width=6)
        self._w_val_lbl.pack(side="left", padx=(6,0))
        # guardar ref al label para actualizar
        if not hasattr(self, "_w_val_lbls"):
            self._w_val_lbls = {}
        self._w_val_lbls[k] = self._w_val_lbl

        # delta vs optimizado
        opt_v = self.opt_weights[k]
        delta = norm_val - opt_v
        dtxt = f"{'↑' if delta > 0.0005 else ('↓' if delta < -0.0005 else '·')} {abs(delta):.3f}"
        dcol = C["warn"] if abs(delta) > 0.01 else C["muted"]
        dlbl = tk.Label(row, text=dtxt, font=("Helvetica Neue", 9),
                        bg=C["phase2_card"], fg=dcol, width=8)
        dlbl.pack(side="left", padx=(4,0))
        if not hasattr(self, "_w_delta_lbls"):
            self._w_delta_lbls = {}
        self._w_delta_lbls[k] = (dlbl, opt_v)

    def _on_weight_change(self, hh):
        """Actualiza score banner, etiquetas de peso y tabla de hogares en vivo."""
        w = self._current_weights()
        s = score(hh, w)
        pct = int(s * 100)

        if pct >= 65:   sc, sd, sl = C["danger"], C["danger_dim"], "ALTA"
        elif pct >= 40: sc, sd, sl = C["warn"],   C["warn_dim"],   "MEDIA"
        else:           sc, sd, sl = C["ok"],      C["ok_dim"],     "BAJA"

        # actualizar banner
        if hasattr(self, "_score_lbl"):
            self._score_lbl.configure(text=f"{pct}%", fg=sc, bg=sd)
            self._score_level_lbl.configure(text=f"  {sl}", fg=sc, bg=sd)
            self._banner_inner.configure(bg=sd)
            self._banner_frame.configure(bg=sd, highlightbackground=sc)
            if hasattr(self, "_bar_inner"):
                self._bar_inner.configure(bg=sc)
                self._bar_inner.place(relwidth=min(1.0, s))

        # actualizar etiquetas peso normalizado + delta
        if hasattr(self, "_w_val_lbls"):
            raw = {k: max(0.001, self.live_weights[k].get()) for k in IND_KEYS}
            t = sum(raw.values()) or 1
            for k in IND_KEYS:
                nv = raw[k] / t
                if k in self._w_val_lbls:
                    self._w_val_lbls[k].configure(text=f"{nv:.3f}")
                if hasattr(self, "_w_delta_lbls") and k in self._w_delta_lbls:
                    dlbl, opt_v = self._w_delta_lbls[k]
                    delta = nv - opt_v
                    dtxt = f"{'↑' if delta > 0.0005 else ('↓' if delta < -0.0005 else '·')} {abs(delta):.3f}"
                    dcol = C["warn"] if abs(delta) > 0.01 else C["muted"]
                    dlbl.configure(text=dtxt, fg=dcol)

        # actualizar tabla de todos los hogares
        if hasattr(self, "_all_score_labels"):
            for h in HOUSEHOLDS:
                hs = score(h, w)
                hpct = int(hs * 100)
                hc = C["danger"] if hpct >= 65 else (C["warn"] if hpct >= 40 else C["ok"])
                if h["id"] in self._all_score_labels:
                    slbl, row_bg = self._all_score_labels[h["id"]]
                    slbl.configure(text=f"{hpct}%", fg=hc)
                if h["id"] in self._all_bar_frames:
                    bf, bfill = self._all_bar_frames[h["id"]]
                    bfill.configure(bg=hc)
                    bfill.place(width=int(140 * min(1.0, hs)))

        # actualizar sidebar mini-scores
        self._build_sidebar()


if __name__ == "__main__":
    app = App()
    app.mainloop()