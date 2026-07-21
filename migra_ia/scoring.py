"""Motor de evaluacion de obsolescencia (Seccion 6 del documento de diseno).

Cada factor recibe una puntuacion de 0 a 100 (mayor = mas riesgo). El total es
la suma ponderada segun los pesos iniciales del documento. Los pesos son
ajustables durante la validacion del prototipo.
"""

from __future__ import annotations

from dataclasses import dataclass

# Pesos iniciales (Seccion 6). Suma = 1.0
PESOS: dict[str, float] = {
    "estado_ciclo_vida": 0.20,
    "disponibilidad_repuestos": 0.15,
    "soporte_fabricante": 0.15,
    "disponibilidad_software": 0.10,
    "disponibilidad_respaldo": 0.15,
    "compatibilidad_sistemas": 0.10,
    "historial_fallas": 0.05,
    "criticidad_productiva": 0.10,
}

ETIQUETAS_FACTOR: dict[str, str] = {
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
class ResultadoRiesgo:
    puntuacion: float
    clasificacion: str
    detalle_factores: list[dict]

    def to_dict(self) -> dict:
        return {
            "puntuacion": self.puntuacion,
            "clasificacion": self.clasificacion,
            "detalle_factores": self.detalle_factores,
        }


def clasificar(puntuacion: float) -> str:
    """Traduce una puntuacion 0-100 a su clasificacion textual (Seccion 6)."""
    if puntuacion <= 20:
        return "Riesgo bajo"
    if puntuacion <= 40:
        return "Riesgo moderado"
    if puntuacion <= 60:
        return "Riesgo importante"
    if puntuacion <= 80:
        return "Riesgo alto"
    return "Riesgo critico"


def calcular_riesgo(factores: dict[str, dict]) -> ResultadoRiesgo:
    """Calcula el riesgo de obsolescencia ponderado.

    `factores` es un dict con claves de PESOS. Cada valor es un dict con:
        - "valor": puntuacion 0-100 del factor (mayor = mas riesgo)
        - "justificacion": texto que explica la puntuacion (obligatorio)

    Los factores no provistos se omiten y los pesos se renormalizan sobre los
    factores disponibles, para no penalizar por informacion faltante. El
    conjunto de factores usados se reporta en el detalle.
    """
    detalle: list[dict] = []
    suma_pesos = 0.0
    suma_ponderada = 0.0

    for clave, peso in PESOS.items():
        entrada = factores.get(clave)
        if entrada is None:
            detalle.append(
                {
                    "factor": ETIQUETAS_FACTOR[clave],
                    "clave": clave,
                    "peso": peso,
                    "valor": None,
                    "justificacion": "Sin datos suficientes (no incluido en el calculo).",
                }
            )
            continue

        valor = float(entrada.get("valor", 0))
        valor = max(0.0, min(100.0, valor))  # acotar 0-100
        justif = str(entrada.get("justificacion", "")).strip() or "(sin justificacion)"

        suma_pesos += peso
        suma_ponderada += peso * valor
        detalle.append(
            {
                "factor": ETIQUETAS_FACTOR[clave],
                "clave": clave,
                "peso": peso,
                "valor": valor,
                "justificacion": justif,
            }
        )

    if suma_pesos == 0:
        puntuacion = 0.0
    else:
        puntuacion = round(suma_ponderada / suma_pesos, 1)

    return ResultadoRiesgo(
        puntuacion=puntuacion,
        clasificacion=clasificar(puntuacion),
        detalle_factores=detalle,
    )
