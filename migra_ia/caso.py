"""Expediente del caso: identificacion y trazabilidad (Secciones 2, 5 y 13).

Cada usuario, planta, maquina, activo, evidencia, diagnostico y recomendacion
dispone de un identificador unico. El expediente se guarda en disco como JSON
para conservar el historial y demostrar que informacion sustento cada decision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from . import config


def _ahora() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _sello() -> str:
    """Sello corto y ordenable para construir identificadores unicos."""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]


@dataclass
class Caso:
    """Expediente de un caso de diagnostico / migracion."""

    case_id: str = ""
    agente_version: str = config.AGENTE_VERSION
    creado: str = field(default_factory=_ahora)
    actualizado: str = field(default_factory=_ahora)

    # Datos capturados por seccion del cuestionario: {"A01": {...}, ...}
    respuestas: dict = field(default_factory=dict)
    # Activos registrados (PLC, modulos, HMI, variadores, instrumentos)
    activos: list = field(default_factory=list)
    # Evidencias (fotos, manuales, planos, respaldos)
    evidencias: list = field(default_factory=list)
    # Datos criticos faltantes (Seccion 11)
    datos_faltantes: list = field(default_factory=list)
    # Resultado del motor de riesgo (Seccion 6)
    riesgo: dict | None = None
    # Recomendaciones e informes emitidos
    recomendaciones: list = field(default_factory=list)
    informes: list = field(default_factory=list)
    # Banderas de seguridad (p. ej. revision obligatoria por especialista)
    banderas: list = field(default_factory=list)
    # Solicitudes de intervencion pendientes de aprobacion humana (via web)
    aprobaciones_pendientes: list = field(default_factory=list)
    # Registro de auditoria: toda accion queda trazada
    auditoria: list = field(default_factory=list)

    _contadores: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    def __post_init__(self) -> None:
        if not self.case_id:
            self.case_id = f"CAS-{datetime.now().year}-{_sello()[-6:]}"

    def _nuevo_id(self, prefijo: str) -> str:
        n = self._contadores.get(prefijo, 0) + 1
        self._contadores[prefijo] = n
        return f"{prefijo}-{datetime.now().year}-{n:06d}"

    def _tocar(self, accion: str, detalle: dict | None = None) -> None:
        self.actualizado = _ahora()
        self.auditoria.append(
            {"ts": self.actualizado, "accion": accion, "detalle": detalle or {}}
        )

    # ------------------------------------------------------------------ #
    def guardar_respuesta(
        self,
        seccion: str,
        codigo: str,
        pregunta: str,
        valor,
        nivel_confianza: str = "confianza_media",
        fuente: str = "",
    ) -> None:
        self.respuestas[codigo] = {
            "seccion": seccion,
            "pregunta": pregunta,
            "valor": valor,
            "nivel_confianza": nivel_confianza,
            "fuente": fuente,
            "ts": _ahora(),
        }
        self._tocar("guardar_respuesta", {"codigo": codigo})

    def registrar_activo(self, activo: dict) -> str:
        aid = self._nuevo_id("AST")
        registro = {"id": aid, "ts": _ahora(), **activo}
        self.activos.append(registro)
        self._tocar("registrar_activo", {"id": aid, "tipo": activo.get("tipo")})
        return aid

    def registrar_evidencia(self, evidencia: dict) -> str:
        eid = self._nuevo_id("EVD")
        registro = {"id": eid, "ts": _ahora(), **evidencia}
        self.evidencias.append(registro)
        self._tocar("registrar_evidencia", {"id": eid})
        return eid

    def registrar_dato_faltante(self, descripcion: str, impacto: str = "") -> None:
        self.datos_faltantes.append(
            {"descripcion": descripcion, "impacto": impacto, "ts": _ahora()}
        )
        self._tocar("registrar_dato_faltante", {"descripcion": descripcion})

    def registrar_bandera(self, texto: str) -> None:
        if texto not in [b["texto"] for b in self.banderas]:
            self.banderas.append({"texto": texto, "ts": _ahora()})
            self._tocar("registrar_bandera", {"texto": texto})

    def guardar_riesgo(self, resultado: dict) -> None:
        self.riesgo = {"ts": _ahora(), **resultado}
        self._tocar("guardar_riesgo", {"puntuacion": resultado.get("puntuacion")})

    def registrar_recomendacion(self, rec: dict) -> str:
        rid = self._nuevo_id("REC")
        registro = {"id": rid, "ts": _ahora(), "human_approval": False, **rec}
        self.recomendaciones.append(registro)
        self._tocar("registrar_recomendacion", {"id": rid})
        return rid

    def registrar_informe(self, ruta: str, resumen: str = "") -> str:
        iid = self._nuevo_id("INF")
        self.informes.append(
            {"id": iid, "ruta": ruta, "resumen": resumen, "ts": _ahora()}
        )
        self._tocar("registrar_informe", {"id": iid, "ruta": ruta})
        return iid

    # ------------------------------------------------------------------ #
    def resumen(self) -> dict:
        """Estado compacto del expediente para que el agente lo consulte."""
        return {
            "case_id": self.case_id,
            "respuestas_registradas": sorted(self.respuestas.keys()),
            "num_activos": len(self.activos),
            "activos": [
                {"id": a["id"], "tipo": a.get("tipo"), "descripcion": a.get("descripcion")}
                for a in self.activos
            ],
            "num_evidencias": len(self.evidencias),
            "datos_faltantes": [d["descripcion"] for d in self.datos_faltantes],
            "banderas": [b["texto"] for b in self.banderas],
            "aprobaciones_pendientes": self.aprobaciones_pendientes,
            "riesgo": self.riesgo,
            "num_recomendaciones": len(self.recomendaciones),
            "num_informes": len(self.informes),
        }

    def ruta_archivo(self) -> Path:
        return config.DIR_CASOS / f"{self.case_id}.json"

    def guardar(self) -> Path:
        ruta = self.ruta_archivo()
        datos = asdict(self)
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        return ruta

    @classmethod
    def cargar(cls, case_id: str) -> "Caso":
        ruta = config.DIR_CASOS / f"{case_id}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return cls(**datos)
