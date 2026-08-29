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


def _partes_marca(texto: str) -> set[str]:
    """Nombres por los que se conoce una marca, normalizados.

    El catalogo escribe 'Rockwell Automation / Allen-Bradley' o 'Emerson (legado
    GE Fanuc / GE Intelligent Platforms)'. Se parte por '/' y por los parentesis
    para que cualquiera de esos nombres identifique al mismo fabricante.
    """
    crudo = (texto or "").replace("(", "/").replace(")", "/")
    partes = {" ".join(p.split()).strip().lower() for p in crudo.split("/")}
    return {p for p in partes if len(p) >= 3}


def _misma_marca(a: str, b: str) -> bool:
    """True si dos textos designan al mismo fabricante.

    Sin esto, elegir la CPU nueva del propio fabricante se contaria como cambio
    de marca y activaria las variantes que no corresponden (pasos 21 y 22).
    """
    pa, pb = _partes_marca(a), _partes_marca(b)
    if not pa or not pb:
        return False
    if pa & pb:
        return True
    return any(x in y or y in x for x in pa for y in pb)


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
    # Equipo anclado: ficha del catalogo de fabricantes para el PLC/CPU del caso.
    # Fija marca, familia y generacion para que toda la asesoria se refiera a ESE
    # equipo y no a un ejemplo por defecto.
    equipo_identificado: dict | None = None
    # Resultado del motor de riesgo (Seccion 6)
    riesgo: dict | None = None
    # Modo guia del procedimiento de 50 pasos. Se abre cuando se decide cambiar la
    # CPU y guarda el disparador, la CPU destino elegida, las variantes que aplican
    # (cambio de marca, sin respaldo) y el estado de cada paso.
    migracion: dict | None = None
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

    def fijar_equipo(self, identificacion: dict) -> None:
        """Ancla el equipo del caso a una ficha del catalogo de fabricantes.

        Solo se sustituye una identificacion previa si la nueva es mas precisa
        (modelo exacto > familia > marca): asi, registrar despues un modulo de E/S
        o una HMI no borra la CPU ya identificada.
        """
        orden = {"modelo_exacto": 3, "familia": 2, "marca": 1}
        nuevo = orden.get(identificacion.get("estado", ""), 0)
        if nuevo == 0:
            return
        actual = orden.get((self.equipo_identificado or {}).get("estado", ""), 0)
        if nuevo >= actual:
            self.equipo_identificado = identificacion
            self._tocar(
                "fijar_equipo",
                {"marca": identificacion.get("marca"),
                 "familia": identificacion.get("familia"),
                 "estado": identificacion.get("estado")},
            )

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
    # Modo guia: procedimiento de migracion de 50 pasos
    # ------------------------------------------------------------------ #
    def iniciar_migracion(self, disparador: str, motivo: str = "",
                          decidido_por: str = "usuario") -> dict:
        """Abre el modo guia. Es idempotente: no reinicia un avance ya empezado."""
        if self.migracion and self.migracion.get("activa"):
            self.migracion.setdefault("disparadores", [])
            if disparador not in self.migracion["disparadores"]:
                self.migracion["disparadores"].append(disparador)
                self._tocar("migracion_disparador", {"disparador": disparador})
            return self.migracion
        self.migracion = {
            "activa": True,
            "abierta": _ahora(),
            "disparadores": [disparador],
            "motivo": motivo,
            "decidido_por": decidido_por,
            "destino": None,
            "cambio_marca": False,
            "sin_respaldo": False,
            "pasos": {},
        }
        self._tocar("iniciar_migracion",
                    {"disparador": disparador, "decidido_por": decidido_por})
        return self.migracion

    def declarar_sin_respaldo(self, sin_respaldo: bool = True) -> None:
        """Marca que no hay programa de origen recuperable (contrasena, sin acceso)."""
        if not self.migracion:
            self.iniciar_migracion("sin_acceso_al_programa",
                                   "Declarado sin respaldo verificado")
        self.migracion["sin_respaldo"] = bool(sin_respaldo)
        self._tocar("declarar_sin_respaldo", {"sin_respaldo": bool(sin_respaldo)})

    def fijar_destino(self, marca: str, familia: str, modelo: str = "",
                      justificacion: str = "", fuente: str = "") -> dict:
        """Registra la CPU destino elegida (paso 13) y deduce si cambia la marca."""
        if not self.migracion:
            self.iniciar_migracion("decision_del_usuario", "Eleccion de CPU destino")
        origen = (self.equipo_identificado or {}).get("marca") or ""
        cambio = bool(origen) and not _misma_marca(marca, origen)
        self.migracion["destino"] = {
            "marca": marca,
            "familia": familia,
            "modelo": modelo,
            "justificacion": justificacion,
            "fuente": fuente,
            "ts": _ahora(),
        }
        self.migracion["cambio_marca"] = cambio
        self._tocar("fijar_destino",
                    {"marca": marca, "familia": familia, "cambio_marca": cambio})
        return self.migracion["destino"]

    def marcar_paso(self, clave, estado: str, nota: str = "",
                    evidencia: list | None = None) -> dict:
        """Registra el estado de un paso del procedimiento, con su marca de tiempo.

        `clave` es '1'..'50' del documento original o 'P1'..'P7' de la extension
        de construccion del programa: no se fuerza a entero.
        """
        if not self.migracion:
            self.iniciar_migracion("decision_del_usuario", "Avance del procedimiento")
        texto = str(clave).strip()
        c = texto if not texto.isdigit() else str(int(texto))
        registro = {
            "estado": estado,
            "nota": nota,
            "evidencia": evidencia or [],
            "ts": _ahora(),
        }
        self.migracion.setdefault("pasos", {})[c] = registro
        self._tocar("marcar_paso", {"paso": c, "estado": estado})
        return registro

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
            "equipo_identificado": (
                {
                    "marca": self.equipo_identificado.get("marca"),
                    "familia": self.equipo_identificado.get("familia"),
                    "modelo": self.equipo_identificado.get("modelo_identificado"),
                    "etapa": self.equipo_identificado.get("etapa"),
                    "estado_identificacion": self.equipo_identificado.get("estado"),
                }
                if self.equipo_identificado
                else None
            ),
            "num_evidencias": len(self.evidencias),
            "datos_faltantes": [d["descripcion"] for d in self.datos_faltantes],
            "banderas": [b["texto"] for b in self.banderas],
            "aprobaciones_pendientes": self.aprobaciones_pendientes,
            "riesgo": self.riesgo,
            "migracion": self._resumen_migracion(),
            "num_recomendaciones": len(self.recomendaciones),
            "num_informes": len(self.informes),
        }

    def _resumen_migracion(self) -> dict | None:
        """Avance del procedimiento de 50 pasos, si el modo guia esta abierto."""
        if not self.migracion or not self.migracion.get("activa"):
            return None
        pasos = self.migracion.get("pasos", {}) or {}
        cerrados = [c for c, r in pasos.items()
                    if r.get("estado") in ("completado", "no_aplica")]
        # Ordena 1..50 antes que P1..P7, sin romper con las claves no numericas.
        cerrados.sort(key=lambda c: (0, int(c)) if c.isdigit() else (1, c))
        return {
            "activa": True,
            "disparadores": self.migracion.get("disparadores", []),
            "destino": self.migracion.get("destino"),
            "cambio_marca": self.migracion.get("cambio_marca", False),
            "sin_respaldo": self.migracion.get("sin_respaldo", False),
            "pasos_cerrados": cerrados,
            "avance": f"{len(cerrados)} de 57",
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
