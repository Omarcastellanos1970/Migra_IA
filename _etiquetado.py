"""Etiquetas de P1 y P2 para las nueve plataformas, y el formulario para los expertos.

POR QUE EXISTE
--------------
P1 y P2 necesitan una etiqueta de referencia. La buena es la de un panel de
ingenieros -asi lo declara el plan de evaluacion del paper- y hoy no esta
disponible. Este script hace dos cosas distintas y no las confunde:

  `provisional`  escribe data/etiquetas_p1_p2.json con un etiquetado derivado de
                 UNA REGLA ESCRITA, no de criterio humano. Sirve para que el
                 circuito completo corra de punta a punta y para que P2 deje de
                 estar bloqueado, NO para validar nada.

  `formulario`   escribe docs/formulario_etiquetado.md, que es lo que se le
                 manda a cada coautor. No lleva ninguna salida del motor ni el
                 etiquetado provisional: quien lo responde no ve la respuesta.

  `comparar`     lee los formularios devueltos y mide el acuerdo entre expertos
                 y su distancia contra la regla provisional.

LO QUE HAY QUE DECLARAR EN EL PAPER
-----------------------------------
Con etiqueta derivada de regla, P1 no es una prediccion: es la re-derivacion de
una definicion, y por eso la auditoria de fuga de _baseline.py deja fuera todas
las columnas de fecha. La etiqueta experta es lo que convierte P1 en un problema
de aprendizaje real. Mientras el campo `procedencia` del JSON diga
`provisional_regla`, ninguna cifra que salga de aqui puede presentarse como
validacion.

    python _etiquetado.py provisional
    python _etiquetado.py formulario
    python _etiquetado.py comparar respuestas_julio.md respuestas_isidoro.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _baseline import CLASES, FECHA_REF, cargar          # noqa: E402

RAIZ = Path(__file__).resolve().parent
ETIQUETAS = RAIZ / "data" / "etiquetas_p1_p2.json"
FORMULARIO = RAIZ / "docs" / "formulario_etiquetado.md"

# Criterio de prioridad de reemplazo, escrito antes de mirar los datos para que
# no se pueda acomodar al resultado. Ordena por urgencia de suministro, que es
# lo unico que esta tabla soporta: no trae criticidad de proceso ni coste de
# parada, que son las otras dos mitades de la decision real.
CRITERIO_P2 = [
    "1. Primero las que YA no tienen repuestos: fin de reparacion publicado y pasado.",
    "2. Despues aquellas cuyo fin de repuestos NO esta publicado. Es un riesgo de "
    "suministro no confirmado y no se cuenta como si ya hubiera terminado.",
    "3. Al final las que tienen repuestos confirmados, menos anios restantes primero.",
    "4. Dentro de cada banda, mas antigua primero.",
    "5. Empate final: orden alfabetico de plataforma, para que sea reproducible.",
]


def _anios_restantes(p) -> float | None:
    """Anios desde FECHA_REF hasta el fin de repuestos. Negativo si ya paso.

    None cuando el fabricante no lo publica. NO se sustituye por el peor caso:
    decir "sin repuestos ya" de un dato que nadie publico es inventarlo, y el
    proyecto marca el hueco en vez de suponerlo.
    """
    if p.fin_repuestos is None:
        return None
    return (p.fin_repuestos[0] - FECHA_REF[0]) + (p.fin_repuestos[1] - FECHA_REF[1]) / 12


def _banda(p) -> int:
    """0 = sin repuestos confirmado, 1 = fin no publicado, 2 = con repuestos."""
    r = _anios_restantes(p)
    if r is None:
        return 1
    return 0 if r <= 0 else 2


def provisional() -> dict:
    datos = cargar()
    orden = sorted(
        datos,
        key=lambda p: (_banda(p),
                       _anios_restantes(p) if _anios_restantes(p) is not None else 0.0,
                       -p.antiguedad, p.plataforma),
    )
    return {
        "procedencia": "provisional_regla",
        "advertencia": (
            "ETIQUETADO PROVISIONAL. No es juicio experto: sale de una regla "
            "escrita, no de criterio humano. No usar como validacion. Se "
            "sustituye por las respuestas del panel en cuanto esten."
        ),
        "fecha_referencia": "%04d-%02d-%02d" % FECHA_REF,
        "evaluadores": [],
        "criterio_p2": CRITERIO_P2,
        "p1_clase": {p.plataforma: p.clase for p in datos},
        "p1_regla": ("derivada de las fechas contra la fecha de referencia; por eso "
                     "las columnas de fecha quedan excluidas como variable en "
                     "_baseline.py. Ver la auditoria de fuga."),
        "p2_orden": [p.plataforma for p in orden],
        "p2_detalle": [
            {"puesto": i + 1, "plataforma": p.plataforma,
             "anios_repuestos_restantes": (None if _anios_restantes(p) is None
                                           else round(_anios_restantes(p), 1)),
             "antiguedad": p.antiguedad,
             "estado_repuestos": ["sin repuestos confirmado",
                                  "fin de repuestos NO publicado",
                                  "con repuestos"][_banda(p)]}
            for i, p in enumerate(orden)
        ],
    }


# --------------------------------------------------------------------------
# Metricas de P2: importa el orden
# --------------------------------------------------------------------------

def metricas_ranking(propuesto: list[str], referencia: list[str],
                     ks: tuple[int, ...] = (1, 3, 5)) -> dict:
    """Compara un orden propuesto contra el de referencia.

    ADAPTACION DECLARADA. El rubro pide "precision en los primeros k" y
    "posicion media del elemento correcto", que estan pensadas para una
    recuperacion donde hay un elemento relevante y muchos que no. P2 es una
    permutacion completa de las mismas nueve plataformas, asi que:

      - precision@k se mide como el solapamiento entre los k primeros del orden
        propuesto y los k primeros de la referencia, dividido por k. Responde a
        "de las k que dije que hay que reemplazar antes, cuantas lo son".

      - posicion media del elemento correcto se mide sobre los elementos que la
        REFERENCIA pone en cabeza: en que puesto medio los coloca el orden
        propuesto. Si la referencia dice que hay tres urgentes y el modelo los
        pone en los puestos 1, 2 y 5, la posicion media es 2.67 frente a un
        ideal de 2.0.

    Se anade el desplazamiento medio absoluto sobre TODOS los elementos, que es
    lo unico que resume la permutacion entera sin privilegiar la cabeza.
    """
    puesto_prop = {p: i + 1 for i, p in enumerate(propuesto)}
    puesto_ref = {p: i + 1 for i, p in enumerate(referencia)}
    comunes = set(puesto_prop) & set(puesto_ref)
    if not comunes:
        return {"error": "los dos ordenes no comparten ningun elemento"}

    res: dict = {"n": len(comunes), "precision_en_k": {}, "posicion_media_en_k": {}}
    for k in ks:
        if k > len(referencia):
            continue
        cabeza_ref = set(referencia[:k])
        cabeza_prop = set(propuesto[:k])
        res["precision_en_k"][k] = round(len(cabeza_ref & cabeza_prop) / k, 3)
        puestos = [puesto_prop[p] for p in referencia[:k] if p in puesto_prop]
        res["posicion_media_en_k"][k] = {
            "obtenida": round(sum(puestos) / len(puestos), 2),
            "ideal": round(sum(range(1, k + 1)) / k, 2),
        }

    res["desplazamiento_medio"] = round(
        sum(abs(puesto_prop[p] - puesto_ref[p]) for p in comunes) / len(comunes), 2)
    return res


def orden_por_antiguedad(datos) -> list[str]:
    """Orden trivial de P2: la mas antigua primero. Es el B0 del ordenamiento,
    el suelo contra el que cualquier propuesta tiene que ganar."""
    return [p.plataforma for p in sorted(datos, key=lambda x: (-x.antiguedad,
                                                              x.plataforma))]


def escribir_formulario() -> None:
    datos = cargar()
    L = ["# Formulario de etiquetado por juicio experto",
         "",
         "Para: coautores del trabajo. Tiempo estimado: 20-30 minutos.",
         "",
         "Este formulario **no contiene ninguna salida del agente** ni el etiquetado",
         "provisional que hay en el repositorio. Se responde con criterio propio; ese",
         "es justamente el valor de lo que se pide.",
         "",
         "Rellena tu nombre y responde las dos partes. Devuelve el archivo tal cual,",
         "renombrado con tu apellido.",
         "",
         "**Evaluador:** `_______________________`   **Fecha:** `___________`",
         "",
         "---",
         "",
         "## Parte 1 — Nivel de obsolescencia",
         "",
         "Para cada plataforma, marca **una** clase de la escala:",
         ""]
    for c in sorted(CLASES):
        L.append(f"- **{c}** — {CLASES[c]}")
    L += ["",
          "Los datos que se te dan son los publicados por el fabricante. Si consideras",
          "que falta informacion para decidir, escribe `NS` en vez de adivinar: un",
          "dato faltante declarado vale mas que una clase inventada.",
          ""]

    for p in datos:
        L += [f"### {p.plataforma}  ({p.fabricante})",
              "",
              f"- Lanzamiento: **{p.lanzamiento}**",
              f"- Anuncio de fin de vida: **{_fmt(p.anuncio)}**",
              f"- Fin de comercializacion: **{_fmt(p.fin_comercializacion)}**",
              f"- Fin de repuestos y reparacion: **{_fmt(p.fin_repuestos)}**",
              "",
              "Clase (1-4, o NS): `____`    Comentario: `______________________________`",
              ""]

    L += ["---",
          "",
          "## Parte 2 — Prioridad de reemplazo",
          "",
          "Ordena las nueve plataformas de **1 = se reemplaza primero** a **9 = puede",
          "esperar**, suponiendo que las nueve estan instaladas en la misma planta y",
          "compiten por el mismo presupuesto. Usa el criterio que usarias en tu planta;",
          "no hay respuesta oficial.",
          ""]
    for p in sorted(datos, key=lambda x: x.plataforma):
        L.append(f"- `____`  {p.plataforma}  ({p.fabricante})")
    L += ["",
          "En una linea, que peso le diste a cada cosa (obsolescencia, criticidad,",
          "coste, riesgo de parada):",
          "",
          "`__________________________________________________________________`",
          ""]
    FORMULARIO.write_text("\n".join(L), encoding="utf-8")
    print(f"Escrito {FORMULARIO.relative_to(RAIZ).as_posix()} "
          f"({len(datos)} plataformas, sin salida del motor)")


def _fmt(f) -> str:
    return "no publicado" if f is None else "%04d-%02d" % (f[0], f[1])


def comparar(archivos: list[Path]) -> None:
    """Lee formularios rellenados y mide el acuerdo. El resultado con valor
    cientifico es el acuerdo ENTRE expertos: si dos ingenieros leen los mismos
    datos y clasifican distinto, el problema no es el motor sino que el criterio
    admite lecturas distintas."""
    base = json.loads(ETIQUETAS.read_text(encoding="utf-8")) if ETIQUETAS.exists() else {}
    respuestas: dict[str, dict[str, str]] = {}
    for a in archivos:
        texto = a.read_text(encoding="utf-8")
        clases = {}
        actual = None
        for linea in texto.splitlines():
            m = re.match(r"^###\s+(.+?)\s+\(", linea)
            if m:
                actual = m.group(1).strip()
            m = re.search(r"Clase \(1-4, o NS\):\s*`?\s*([1-4]|NS)\s*`?", linea)
            if m and actual:
                clases[actual] = m.group(1)
        respuestas[a.stem] = clases
        print(f"{a.name}: {len(clases)} clases leidas")

    nombres = list(respuestas)
    if len(nombres) >= 2:
        comunes = set.intersection(*(set(respuestas[n]) for n in nombres))
        acuerdos = sum(len({respuestas[n][p] for n in nombres}) == 1 for p in comunes)
        print(f"\nAcuerdo entre {len(nombres)} evaluadores: {acuerdos}/{len(comunes)} "
              f"plataformas con clase identica")
        for p in sorted(comunes):
            votos = {n: respuestas[n][p] for n in nombres}
            if len(set(votos.values())) > 1:
                print(f"  DESACUERDO {p}: {votos}")

    if base.get("p1_clase"):
        print("\nDistancia contra la regla provisional (no es una nota, es un contraste):")
        for n in nombres:
            comunes = set(respuestas[n]) & set(base["p1_clase"])
            iguales = sum(str(base["p1_clase"][p]) == respuestas[n][p] for p in comunes)
            print(f"  {n}: {iguales}/{len(comunes)} coinciden con la regla")


def main() -> None:
    ap = argparse.ArgumentParser(description="Etiquetado de P1 y P2.")
    ap.add_argument("accion", choices=["provisional", "formulario", "comparar", "p2"])
    ap.add_argument("archivos", nargs="*", type=Path)
    args = ap.parse_args()

    if args.accion == "provisional":
        d = provisional()
        ETIQUETAS.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Escrito {ETIQUETAS.relative_to(RAIZ).as_posix()}")
        print(f"procedencia = {d['procedencia']}  <-- NO es juicio experto")
        print("\nOrden de prioridad provisional (P2):")
        for e in d["p2_detalle"]:
            estado = e["estado_repuestos"]
            restan = e["anios_repuestos_restantes"]
            if restan is not None and restan > 0:
                estado += f" ({restan} anios)"
            print(f"  {e['puesto']}. {e['plataforma']:<30s} antig {e['antiguedad']:>2d}  {estado}")
    elif args.accion == "formulario":
        escribir_formulario()
    elif args.accion == "p2":
        if not ETIQUETAS.exists():
            ap.error("falta data/etiquetas_p1_p2.json; corre primero 'provisional'")
        ref = json.loads(ETIQUETAS.read_text(encoding="utf-8"))
        datos = cargar()
        print("=" * 70)
        print("P2 PRIORIDAD DE REEMPLAZO - METRICAS DE ORDENAMIENTO")
        print("=" * 70)
        print(f"Orden de referencia: procedencia = {ref['procedencia']}")
        if ref["procedencia"] != "panel_experto":
            print("AVISO: la referencia NO es juicio experto. Lo que sigue mide")
            print("coherencia interna, no acierto. No publicar como validacion.")
        print()
        trivial = orden_por_antiguedad(datos)
        m = metricas_ranking(trivial, ref["p2_orden"])
        print("B0 trivial: ordenar por antiguedad, la mas vieja primero")
        for k, v in m["precision_en_k"].items():
            pm = m["posicion_media_en_k"][k]
            print(f"   precision@{k} = {v:<5}   posicion media de los {k} primeros "
                  f"de la referencia = {pm['obtenida']} (ideal {pm['ideal']})")
        print(f"   desplazamiento medio de puesto = {m['desplazamiento_medio']}")
        print()
        print("El clasico de P2 -gradient boosting en modo ranking- no se evalua:")
        print("sigue sin haber un orden de referencia de juicio experto. En cuanto")
        print("lleguen los formularios, este mismo comando lo mide.")
    else:
        if not args.archivos:
            ap.error("comparar necesita al menos un formulario rellenado")
        comparar(args.archivos)


if __name__ == "__main__":
    main()
