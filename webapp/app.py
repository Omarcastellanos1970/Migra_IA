"""App web de MIGRA-IA (Flask).

Interfaz de chat en el navegador: el usuario ingresa la informacion del equipo y
la IA lo orienta paso a paso hacia la solucion (reparacion, repuesto, hardware
equivalente o migracion). Reutiliza el mismo motor que el CLI.

Ejecutar:
    python -m webapp.app
    # luego abrir http://127.0.0.1:5000
"""

from __future__ import annotations

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001
    pass

from flask import Flask, request, jsonify, render_template

from migra_ia import config, demo
from migra_ia.caso import Caso
from migra_ia.prompt import construir_system_prompt, MENSAJE_INICIAL_USUARIO
from migra_ia.nucleo import ejecutar_turno, nuevo_cliente

app = Flask(__name__)

SYSTEM = construir_system_prompt()

# Sesiones en memoria: case_id -> {"messages": [...], "caso": Caso}.
# El expediente se persiste en disco; el historial de conversacion vive mientras
# el servidor este activo (suficiente para el prototipo).
SESIONES: dict[str, dict] = {}

_CLIENTE = None


def _cliente():
    global _CLIENTE
    if _CLIENTE is None:
        _CLIENTE = nuevo_cliente()
    return _CLIENTE


@app.route("/")
def index():
    return render_template(
        "index.html", agente=config.AGENTE_NOMBRE, version=config.AGENTE_VERSION
    )


@app.post("/api/nuevo")
def nuevo_caso():
    data = request.get_json(force=True, silent=True) or {}
    es_demo = bool(data.get("demo"))

    caso = Caso()
    caso.guardar()

    # Modo demostracion: no usa la API, recorre un caso de ejemplo con el motor real.
    if es_demo:
        paso = demo.ejecutar_paso(caso, 0)
        SESIONES[caso.case_id] = {"messages": [], "caso": caso, "demo": True, "demo_idx": 1}
        return jsonify(case_id=caso.case_id, **paso)

    messages: list[dict] = [{"role": "user", "content": MENSAJE_INICIAL_USUARIO}]
    try:
        res = ejecutar_turno(_cliente(), SYSTEM, messages, caso)
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=_msg_error(exc)), 500
    SESIONES[caso.case_id] = {"messages": messages, "caso": caso, "demo": False}
    return jsonify(
        case_id=caso.case_id,
        texto=res["texto"],
        acciones=res["acciones"],
        resumen=res["resumen"],
    )


@app.post("/api/mensaje")
def mensaje():
    data = request.get_json(force=True, silent=True) or {}
    cid = data.get("case_id")
    texto_usuario = (data.get("mensaje") or "").strip()

    ses = SESIONES.get(cid)
    if ses is None:
        return jsonify(error="Caso no encontrado o sesion expirada. Abre un caso nuevo."), 404
    if not texto_usuario:
        return jsonify(error="Mensaje vacio."), 400

    # Modo demostracion: avanza el guion sin llamar a la API.
    if ses.get("demo"):
        idx = ses.get("demo_idx", 1)
        paso = demo.ejecutar_paso(ses["caso"], idx)
        ses["demo_idx"] = idx + 1
        return jsonify(**paso)

    ses["messages"].append({"role": "user", "content": texto_usuario})
    try:
        res = ejecutar_turno(_cliente(), SYSTEM, ses["messages"], ses["caso"])
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=_msg_error(exc)), 500
    return jsonify(texto=res["texto"], acciones=res["acciones"], resumen=res["resumen"])


@app.get("/api/resumen/<case_id>")
def resumen(case_id: str):
    ses = SESIONES.get(case_id)
    if ses is not None:
        return jsonify(ses["caso"].resumen())
    try:
        return jsonify(Caso.cargar(case_id).resumen())
    except Exception:  # noqa: BLE001
        return jsonify(error="Caso no encontrado."), 404


def _msg_error(exc: Exception) -> str:
    nombre = type(exc).__name__
    if "Authentication" in nombre or "api_key" in str(exc).lower():
        return (
            "No hay credencial valida de Anthropic. Configura ANTHROPIC_API_KEY "
            "en el archivo .env (ver .env.example)."
        )
    return f"{nombre}: {exc}"


if __name__ == "__main__":
    print(config.MENSAJE_BIENVENIDA)
    print("\nAbre http://127.0.0.1:5000 en tu navegador.\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
