"""Motor de evaluacion de obsolescencia (Seccion 6 del documento de diseno).

Cada factor recibe una puntuacion de 0 a 100 (mayor = mas riesgo). El total es
la suma ponderada segun los pesos iniciales del documento. Los pesos son
ajustables durante la validacion del prototipo.
"""

from __future__ import annotations

from dataclasses import dataclass

# Pesos iniciales (Seccion 6). Suma = 1.0
WEIGHTS: dict[str, float] = {
    "estado_ciclo_vida": 0.20,
    "disponibilidad_repuestos": 0.15,
    "soporte_fabricante": 0.15,
    "disponibilidad_software": 0.10,
    "disponibilidad_respaldo": 0.15,
    "compatibilidad_sistemas": 0.10,
    "historial_fallas": 0.05,
    "criticidad_productiva": 0.10,
}

FACTOR_LABELS: dict[str, str] = {
    "estado_ciclo_vida": "Estado del ciclo de vida",
    "disponibilidad_repuestos": "Disponibilidad de repuestos",
    "soporte_fabricante": "Soporte del fabricante",
    "disponibilidad_software": "Disponibilidad del software",
    "disponibilidad_respaldo": "Disponibilidad de respaldo",
    "compatibilidad_sistemas": "Compatibilidad con sistemas actuales",
    "historial_fallas": "Historial de fallas",
    "criticidad_productiva": "Criticidad productiva",
}


@dataclass
class RiskResult:
    score: float
    classification: str
    factor_detail: list[dict]

    def to_dict(self) -> dict:
        return {
            "puntuacion": self.score,
            "classification": self.classification,
            "detalle_factores": self.factor_detail,
        }


def classify(score: float) -> str:
    """Traduce una puntuacion 0-100 a su clasificacion textual (Seccion 6)."""
    if score <= 20:
        return "Riesgo bajo"
    if score <= 40:
        return "Riesgo moderado"
    if score <= 60:
        return "Riesgo importante"
    if score <= 80:
        return "Riesgo alto"
    return "Riesgo critico"


def compute_risk(factors: dict[str, dict]) -> RiskResult:
    """Calcula el riesgo de obsolescencia ponderado.

    `factores` es un dict con claves de PESOS. Cada valor es un dict con:
        - "value": puntuacion 0-100 del factor (mayor = mas riesgo)
        - "justificacion": texto que explica la puntuacion (obligatorio)

    Los factores no provistos se omiten y los pesos se renormalizan sobre los
    factores disponibles, para no penalizar por informacion faltante. El
    conjunto de factores usados se reporta en el detalle.
    """
    detail: list[dict] = []
    suma_pesos = 0.0
    suma_ponderada = 0.0

    for key, peso in WEIGHTS.items():
        entry = factors.get(key)
        if entry is None:
            detail.append(
                {
                    "factor": FACTOR_LABELS[key],
                    "key": key,
                    "peso": peso,
                    "value": None,
                    "justificacion": "Sin datos suficientes (no incluido en el calculo).",
                }
            )
            continue

        value = float(entry.get("value", 0))
        value = max(0.0, min(100.0, value))  # acotar 0-100
        justif = str(entry.get("justificacion", "")).strip() or "(sin justificacion)"

        suma_pesos += peso
        suma_ponderada += peso * value
        detail.append(
            {
                "factor": FACTOR_LABELS[key],
                "key": key,
                "peso": peso,
                "value": value,
                "justificacion": justif,
            }
        )

    if suma_pesos == 0:
        score = 0.0
    else:
        score = round(suma_ponderada / suma_pesos, 1)

    return RiskResult(
        score=score,
        classification=classify(score),
        factor_detail=detail,
    )
