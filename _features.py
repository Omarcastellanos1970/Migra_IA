"""Contrasta las caracteristicas de dominio que pide el rubro con las que el
proyecto realmente define, alimenta y usa.

Casilla 3 del entregable: "las caracteristicas de dominio definidas y
justificadas, o la decision de ir con el dato crudo documentada".

El documento se genera leyendo el cuestionario y las tablas de puntuacion que a
su vez se extraen del codigo, de modo que no pueda divergir del motor: si
manana un factor deja de leer un codigo, este documento lo dice en la siguiente
corrida.

    python _features.py          # resumen en pantalla
    python _features.py --md     # escribe el documento del idioma activo
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from migra_ia import config

ROOT = Path(__file__).resolve().parent


def D(key: str) -> str:
    """Texto del documento en el idioma de esta ejecucion."""
    return config.doc_tools().get(key, key)


def questionnaire_path() -> Path:
    return config.questionnaire_path()


def rules_path() -> Path:
    """El documento de reglas DEL MISMO idioma: de ahi salen los factores."""
    return ROOT / D("sr_path")


def output_path() -> Path:
    return ROOT / D("ft_path")


# Lo que el rubro nombra como caracteristicas candidatas, y el codigo del
# cuestionario que las recoge. La correspondencia entre los dos vocabularios es
# lo unico que vive aqui: los NOMBRES y la justificacion van por idioma.
CANDIDATAS = [
    (1, ["C05", "D07"]),
    (2, ["M03", "M02"]),
    (3, ["M01"]),
    (4, ["M04", "M05", "M06"]),
    (5, ["G01"]),
    (6, ["C08", "C10", "Q01"]),
]


def used_codes() -> dict[str, tuple[list[str], str]]:
    """Factor -> codigos que lee, extraido del documento que genera el codigo."""
    text = rules_path().read_text(encoding="utf-8")
    factors: dict[str, list[str]] = {}
    actual = None
    for linea in text.splitlines():
        m = re.match(r"^## (.+)$", linea)
        if m:
            actual = m.group(1).strip()
        m = re.search(D("ft_reads_regex"), linea)
        if m and actual:
            peso = re.search(D("ft_weight_regex"), linea)
            factors[actual] = (re.findall(r"[A-Q]\d{2}", m.group(1)),
                                peso.group(1) if peso else "?")
    return factors


def questions() -> dict[str, str]:
    d = json.loads(questionnaire_path().read_text(encoding="utf-8"))
    fuera: dict[str, str] = {}

    def rec(o):
        if isinstance(o, dict):
            if "code" in o and "text" in o:
                fuera[o["code"]] = o["text"]
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(d)
    return fuera


def report() -> str:
    factors = used_codes()
    usados = {c for cs, _ in factors.values() for c in cs}
    textos = questions()

    L: list[str] = []
    a = L.append
    a(D("ft_title"))
    a("")
    a(config.doc_language_line("ft"))
    a("")
    a(D("ft_intro") % (questionnaire_path().relative_to(ROOT).as_posix(),
                       D("sr_path")))
    a("")
    a(D("ft_decision"))
    a("")
    a(D("ft_candidates_title"))
    a("")
    a(D("ft_candidates_head"))
    a("|---|---|---|")
    huerfanas: list[tuple[str, list[str]]] = []
    for n, codigos in CANDIDATAS:
        name = D("ft_cand_%d_name" % n)
        dentro = [c for c in codigos if c in usados]
        fuera = [c for c in codigos if c not in usados and c in textos]
        if dentro:
            status = D("ft_used") % ", ".join(dentro)
            if fuera:
                status += D("ft_asked_unused_tail") % ", ".join(fuera)
                huerfanas.append((name, fuera))
        else:
            status = D("ft_asked_unused") % ", ".join(fuera)
            huerfanas.append((name, fuera))
        a(f"| {name} | {', '.join(codigos)} | {status} |")
    a("")
    for n, codigos in CANDIDATAS:
        a(f"**{D('ft_cand_%d_name' % n)}.** {D('ft_cand_%d_text' % n)}")
        a("")

    a(D("ft_factors_title"))
    a("")
    a(D("ft_factors_intro"))
    a("")
    a(D("ft_factors_head"))
    a("|---|---|---|")
    for factor, (cs, peso) in factors.items():
        a(f"| {factor} | {peso} | {', '.join(cs)} |")
    a("")

    a(D("ft_gaps_title"))
    a("")
    if huerfanas:
        a(D("ft_gaps_intro"))
        a("")
        for name, codigos in huerfanas:
            for c in codigos:
                a(f"- `{c}` — {textos.get(c, D('ft_no_text'))[:88]}  \\[{name}\\]")
        a("")
        a(D("ft_gaps_tail"))
    else:
        a(D("ft_gaps_none"))
    a("")

    a(D("ft_survivor_title"))
    a("")
    a(D("ft_survivor") % D("bl_path"))
    a("")
    a(D("ft_survivor_tail"))
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()
    text = report()
    print(text)
    if args.md:
        destino = output_path()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(text + "\n", encoding="utf-8")
        print(D("ft_written") % destino.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
