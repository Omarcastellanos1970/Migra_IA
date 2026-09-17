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

from migra_ia import config, interactive, scoring
from migra_ia.case import Case
from migra_ia.prompt import build_system_prompt, initial_user_message
from migra_ia.core import run_turn, new_client

app = Flask(__name__)

# Sesiones en memoria: case_id -> {"messages": [...], "case": Caso, "lang": str}.
# El expediente se persiste en disco; el historial de conversacion vive mientras
# el servidor este activo (suficiente para el prototipo).
SESIONES: dict[str, dict] = {}


# --------------------------------------------------------------------------- #
# Idioma: de la PETICION, no del proceso
# --------------------------------------------------------------------------- #
# El servidor atiende a la vez a quien eligio espaniol y a quien eligio ingles.
# El idioma llega en el cuerpo de la peticion o en la query, se fija para este
# hilo y se suelta al terminar. Un caso ya abierto conserva el suyo: una
# conversacion no cambia de idioma a mitad, que seria justo la mezcla que el
# proyecto no admite.
def _request_language() -> str:
    data = request.get_json(silent=True) or {}
    cid = data.get("case_id")
    if cid and cid in SESIONES and SESIONES[cid].get("lang"):
        return SESIONES[cid]["lang"]
    pedido = (data.get("lang") or request.args.get("lang") or "").strip().lower()
    if pedido in config.available_languages():
        return pedido
    return config.DEFAULT_LANGUAGE


@app.before_request
def _set_language():
    request.migra_lang_token = config.set_language(_request_language())


@app.teardown_request
def _unset_language(_exc=None):
    token = getattr(request, "migra_lang_token", None)
    if token is not None:
        config.reset_language(token)

def _hay_credencial() -> bool:
    """Si ESTE servidor puede hablar con el modelo.

    Una clave ausente no es un fallo: es la demo publica gratis, tal como la
    describe render.yaml. Lo que no vale es ofrecer el modo real y reventar al
    pulsarlo con un mensaje que manda editar un .env que el visitante no tiene.
    """
    import os

    return bool((os.environ.get("ANTHROPIC_API_KEY") or "").strip())


_CLIENT = None


def _shown(resumen: dict) -> dict:
    """El expediente con lo que el panel necesita para PINTARLO.

    La clasificacion se guarda con su valor canonico ---es el que va al
    expediente y el que comparan las reglas--- asi que aqui se le anade su
    etiqueta en el idioma de la peticion, y la pagina muestra esa.
    """
    if not isinstance(resumen, dict):
        return resumen
    riesgo = resumen.get("risk")
    if isinstance(riesgo, dict) and riesgo.get("classification"):
        resumen = dict(resumen)
        resumen["risk"] = dict(riesgo)
        resumen["risk"]["label"] = scoring.risk_label(riesgo["classification"])
    return resumen


def _client():
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = new_client()
    return _CLIENT


@app.route("/")
def index():
    return render_template(
        "index.html",
        agent=config.AGENT_NAME,
        version=config.AGENT_VERSION,
        lang=config.language(),
        languages=config.available_languages(),
        ui=config.ui(),
        con_api=_hay_credencial(),
    )


@app.post("/api/nuevo")
def new_case():
    data = request.get_json(force=True, silent=True) or {}
    is_interactive = bool(data.get("interactivo"))

    case = Case()
    case.save()

    # Demo interactiva: no usa la API. LEE cada respuesta del usuario y hace
    # trabajar al motor real con ella, de modo que el resultado es suyo.
    if is_interactive:
        apertura = interactive.start()
        SESIONES[case.case_id] = {
            "messages": [], "case": case, "interactivo": True,
            "status": apertura["status"], "lang": config.language(),
        }
        return jsonify(case_id=case.case_id, text=apertura["text"],
                       actions=[], summary=_shown(case.summary()),
                       interactive=True)

    if not _hay_credencial():
        # Se dice lo que pasa, no se intenta y se falla.
        return jsonify(error=config.ui()["real_needs_key"]), 503

    messages: list[dict] = [{"role": "user", "content": initial_user_message()}]
    try:
        res = run_turn(_client(), build_system_prompt(), messages, case)
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=_error_msg(exc)), 500
    SESIONES[case.case_id] = {"messages": messages, "case": case,
                              "lang": config.language()}
    return jsonify(
        case_id=case.case_id,
        text=res["text"],
        actions=res["acciones"],
        summary=_shown(res["resumen"]),
    )


@app.post("/api/mensaje")
def message():
    data = request.get_json(force=True, silent=True) or {}
    cid = data.get("case_id")
    user_text = (data.get("mensaje") or "").strip()

    ses = SESIONES.get(cid)
    if ses is None:
        return jsonify(error=config.ui()["err_case_expired"]), 404
    if not user_text:
        return jsonify(error=config.ui()["err_empty_message"]), 400

    # Demo interactiva: cada respuesta entra al expediente y mueve el motor.
    # Las claves se traducen aqui, en la frontera HTTP, igual que en el modo
    # con API: dentro el motor habla de `acciones` y `resumen`, y la pagina
    # lee `actions` y `summary`. Devolver el paso tal cual dejaba `d.summary`
    # sin definir y el panel derecho no se actualizaba en toda la demo.
    if ses.get("interactivo"):
        step = interactive.answer(ses["case"], user_text, ses.get("status"))
        ses["status"] = step.pop("status", ses.get("status"))
        return jsonify(text=step["text"], actions=step["acciones"],
                       summary=_shown(step["resumen"]), fin=step["fin"],
                       interactive=True)

    ses["messages"].append({"role": "user", "content": user_text})
    try:
        res = run_turn(_client(), build_system_prompt(), ses["messages"], ses["case"])
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=_error_msg(exc)), 500
    return jsonify(text=res["text"], actions=res["acciones"],
                   summary=_shown(res["resumen"]))


@app.get("/api/resumen/<case_id>")
def summary(case_id: str):
    ses = SESIONES.get(case_id)
    if ses is not None:
        return jsonify(ses["case"].summary())
    try:
        return jsonify(Case.load(case_id).summary())
    except Exception:  # noqa: BLE001
        return jsonify(error=config.ui()["err_case_not_found"]), 404


def _error_msg(exc: Exception) -> str:
    name = type(exc).__name__
    if "Authentication" in name or "api_key" in str(exc).lower():
        return config.ui()["err_no_credential"]
    return f"{name}: {exc}"


if __name__ == "__main__":
    print(config.WELCOME_MESSAGE)
    print(config.ui()["console_open"])
    app.run(host="127.0.0.1", port=5000, debug=False)
