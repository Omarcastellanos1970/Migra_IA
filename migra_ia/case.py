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


def M(key: str) -> str:
    """Mensaje de este modulo en el idioma de esta peticion."""
    from . import config
    return config.messages().get(key, key)



def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _stamp() -> str:
    """Sello corto y ordenable para construir identificadores unicos."""
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]


def _brand_parts(text: str) -> set[str]:
    """Nombres por los que se conoce una marca, normalizados.

    El catalogo escribe 'Rockwell Automation / Allen-Bradley' o 'Emerson (legado
    GE Fanuc / GE Intelligent Platforms)'. Se parte por '/' y por los parentesis
    para que cualquiera de esos nombres identifique al mismo fabricante.
    """
    crudo = (text or "").replace("(", "/").replace(")", "/")
    partes = {" ".join(p.split()).strip().lower() for p in crudo.split("/")}
    return {p for p in partes if len(p) >= 3}


def _same_brand(a: str, b: str) -> bool:
    """True si dos textos designan al mismo fabricante.

    Sin esto, elegir la CPU nueva del propio fabricante se contaria como cambio
    de marca y activaria las variantes que no corresponden (pasos 21 y 22).
    """
    pa, pb = _brand_parts(a), _brand_parts(b)
    if not pa or not pb:
        return False
    if pa & pb:
        return True
    return any(x in y or y in x for x in pa for y in pb)


@dataclass
class Case:
    """Expediente de un caso de diagnostico / migracion."""

    case_id: str = ""
    agent_version: str = config.AGENT_VERSION
    created: str = field(default_factory=_now)
    updated: str = field(default_factory=_now)

    # Datos capturados por seccion del cuestionario: {"A01": {...}, ...}
    answers: dict = field(default_factory=dict)
    # Activos registrados (PLC, modulos, HMI, variadores, instrumentos)
    assets: list = field(default_factory=list)
    # Evidencias (fotos, manuales, planos, respaldos)
    evidence_items: list = field(default_factory=list)
    # Datos criticos faltantes (Seccion 11)
    missing_data: list = field(default_factory=list)
    # Equipo anclado: ficha del catalogo de fabricantes para el PLC/CPU del caso.
    # Fija marca, familia y generacion para que toda la asesoria se refiera a ESE
    # equipo y no a un ejemplo por defecto.
    equipment_identified: dict | None = None
    # Resultado del motor de riesgo (Seccion 6)
    risk: dict | None = None
    # Modo guia del procedimiento de 50 pasos. Se abre cuando se decide cambiar la
    # CPU y guarda el disparador, la CPU destino elegida, las variantes que aplican
    # (cambio de marca, sin respaldo) y el estado de cada paso.
    migration: dict | None = None
    # Recomendaciones e informes emitidos
    recommendations: list = field(default_factory=list)
    reports: list = field(default_factory=list)
    # Banderas de seguridad (p. ej. revision obligatoria por especialista)
    flags: list = field(default_factory=list)
    # Solicitudes de intervencion pendientes de aprobacion humana (via web)
    pending_approvals: list = field(default_factory=list)
    # Registro de auditoria: toda accion queda trazada
    audit: list = field(default_factory=list)

    _counters: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    def __post_init__(self) -> None:
        if not self.case_id:
            self.case_id = f"CAS-{datetime.now().year}-{_stamp()[-6:]}"

    def _new_id(self, prefijo: str) -> str:
        n = self._counters.get(prefijo, 0) + 1
        self._counters[prefijo] = n
        return f"{prefijo}-{datetime.now().year}-{n:06d}"

    def _touch(self, action: str, detail: dict | None = None) -> None:
        self.updated = _now()
        self.audit.append(
            {"ts": self.updated, "accion": action, "detail": detail or {}}
        )

    # ------------------------------------------------------------------ #
    def save_answer(
        self,
        section: str,
        code: str,
        question: str,
        value,
        confidence_level: str = "confianza_media",
        source: str = "",
    ) -> None:
        self.answers[code] = {
            "section": section,
            "question": question,
            "value": value,
            "confidence_level": confidence_level,
            "source": source,
            "ts": _now(),
        }
        self._touch("guardar_respuesta", {"code": code})

    def register_asset(self, asset: dict) -> str:
        aid = self._new_id("AST")
        registro = {"id": aid, "ts": _now(), **asset}
        self.assets.append(registro)
        self._touch("register_asset", {"id": aid, "type": asset.get("type")})
        return aid

    def set_equipment(self, identification: dict) -> None:
        """Ancla el equipo del caso a una ficha del catalogo de fabricantes.

        Solo se sustituye una identificacion previa si la nueva es mas precisa
        (modelo exacto > familia > marca): asi, registrar despues un modulo de E/S
        o una HMI no borra la CPU ya identificada.
        """
        order = {"modelo_exacto": 3, "family": 2, "brand": 1}
        nuevo = order.get(identification.get("status", ""), 0)
        if nuevo == 0:
            return
        actual = order.get((self.equipment_identified or {}).get("status", ""), 0)
        if nuevo >= actual:
            self.equipment_identified = identification
            self._touch(
                "fijar_equipo",
                {"brand": identification.get("brand"),
                 "family": identification.get("family"),
                 "status": identification.get("status")},
            )

    def register_evidence(self, evidence: dict) -> str:
        eid = self._new_id("EVD")
        registro = {"id": eid, "ts": _now(), **evidence}
        self.evidence_items.append(registro)
        self._touch("register_evidence", {"id": eid})
        return eid

    def register_missing_data(self, description: str, impacto: str = "") -> None:
        self.missing_data.append(
            {"description": description, "impacto": impacto, "ts": _now()}
        )
        self._touch("register_missing_data", {"description": description})

    def register_flag(self, text: str) -> None:
        if text not in [b["text"] for b in self.flags]:
            self.flags.append({"text": text, "ts": _now()})
            self._touch("registrar_bandera", {"text": text})

    def save_risk(self, resultado: dict) -> None:
        self.risk = {"ts": _now(), **resultado}
        self._touch("guardar_riesgo", {"puntuacion": resultado.get("puntuacion")})

    def register_recommendation(self, rec: dict) -> str:
        rid = self._new_id("REC")
        registro = {"id": rid, "ts": _now(), "human_approval": False, **rec}
        self.recommendations.append(registro)
        self._touch("registrar_recomendacion", {"id": rid})
        return rid

    def register_report(self, path: str, summary: str = "") -> str:
        iid = self._new_id("INF")
        self.reports.append(
            {"id": iid, "route": path, "resumen": summary, "ts": _now()}
        )
        self._touch("registrar_informe", {"id": iid, "route": path})
        return iid

    # ------------------------------------------------------------------ #
    # Modo guia: procedimiento de migracion de 50 pasos
    # ------------------------------------------------------------------ #
    def start_migration(self, trigger: str, motivo: str = "",
                          decided_by: str = "usuario") -> dict:
        """Abre el modo guia. Es idempotente: no reinicia un avance ya empezado."""
        if self.migration and self.migration.get("activa"):
            self.migration.setdefault("triggers", [])
            if trigger not in self.migration["triggers"]:
                self.migration["triggers"].append(trigger)
                self._touch("migracion_disparador", {"trigger": trigger})
            return self.migration
        self.migration = {
            "activa": True,
            "abierta": _now(),
            "triggers": [trigger],
            "motivo": motivo,
            "decidido_por": decided_by,
            "destino": None,
            "cambio_marca": False,
            "sin_respaldo": False,
            "steps": {},
        }
        self._touch("iniciar_migracion",
                    {"trigger": trigger, "decidido_por": decided_by})
        return self.migration

    def declare_without_backup(self, without_backup: bool = True) -> None:
        """Marca que no hay programa de origen recuperable (contrasena, sin acceso)."""
        if not self.migration:
            self.start_migration("sin_acceso_al_programa",
                                   M("cs002"))
        self.migration["sin_respaldo"] = bool(without_backup)
        self._touch("declarar_sin_respaldo", {"sin_respaldo": bool(without_backup)})

    def set_target(self, brand: str, family: str, modelo: str = "",
                      justification: str = "", source: str = "") -> dict:
        """Registra la CPU destino elegida (paso 13) y deduce si cambia la marca."""
        if not self.migration:
            self.start_migration("decision_del_usuario", M("cs003"))
        origin = (self.equipment_identified or {}).get("brand") or ""
        cambio = bool(origin) and not _same_brand(brand, origin)
        self.migration["destino"] = {
            "brand": brand,
            "family": family,
            "model": modelo,
            "justificacion": justification,
            "source": source,
            "ts": _now(),
        }
        self.migration["cambio_marca"] = cambio
        self._touch("fijar_destino",
                    {"brand": brand, "family": family, "cambio_marca": cambio})
        return self.migration["destino"]

    def mark_step(self, key, status: str, note: str = "",
                    evidence: list | None = None) -> dict:
        """Registra el estado de un paso del procedimiento, con su marca de tiempo.

        `clave` es '1'..'50' del documento original o 'P1'..'P7' de la extension
        de construccion del programa: no se fuerza a entero.
        """
        if not self.migration:
            self.start_migration("decision_del_usuario", M("cs004"))
        text = str(key).strip()
        c = text if not text.isdigit() else str(int(text))
        registro = {
            "status": status,
            "note": note,
            "evidence": evidence or [],
            "ts": _now(),
        }
        self.migration.setdefault("steps", {})[c] = registro
        self._touch("marcar_paso", {"step": c, "status": status})
        return registro

    # ------------------------------------------------------------------ #
    def summary(self) -> dict:
        """Estado compacto del expediente para que el agente lo consulte."""
        return {
            "case_id": self.case_id,
            "respuestas_registradas": sorted(self.answers.keys()),
            "num_activos": len(self.assets),
            "assets": [
                {"id": a["id"], "type": a.get("type"), "description": a.get("description")}
                for a in self.assets
            ],
            "equipment_identified": (
                {
                    "brand": self.equipment_identified.get("brand"),
                    "family": self.equipment_identified.get("family"),
                    "model": self.equipment_identified.get("modelo_identificado"),
                    "stage": self.equipment_identified.get("stage"),
                    "estado_identificacion": self.equipment_identified.get("status"),
                }
                if self.equipment_identified
                else None
            ),
            "num_evidencias": len(self.evidence_items),
            "missing_data": [d["description"] for d in self.missing_data],
            "flags": [b["text"] for b in self.flags],
            "aprobaciones_pendientes": self.pending_approvals,
            "risk": self.risk,
            "migration": self._migration_summary(),
            "num_recomendaciones": len(self.recommendations),
            "num_informes": len(self.reports),
        }

    def _migration_summary(self) -> dict | None:
        """Avance del procedimiento de 50 pasos, si el modo guia esta abierto."""
        if not self.migration or not self.migration.get("activa"):
            return None
        steps = self.migration.get("steps", {}) or {}
        cerrados = [c for c, r in steps.items()
                    if r.get("status") in ("completado", "no_aplica")]
        # Ordena 1..50 antes que P1..P7, sin romper con las claves no numericas.
        cerrados.sort(key=lambda c: (0, int(c)) if c.isdigit() else (1, c))
        return {
            "activa": True,
            "triggers": self.migration.get("triggers", []),
            "destino": self.migration.get("destino"),
            "cambio_marca": self.migration.get("cambio_marca", False),
            "sin_respaldo": self.migration.get("sin_respaldo", False),
            "pasos_cerrados": cerrados,
            "avance": f"{len(cerrados)}{M('cs001')}",
        }

    def file_path(self) -> Path:
        return config.CASES_DIR / f"{self.case_id}.json"

    def save(self) -> Path:
        path = self.file_path()
        data = asdict(self)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, case_id: str) -> "Caso":
        path = config.CASES_DIR / f"{case_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)
