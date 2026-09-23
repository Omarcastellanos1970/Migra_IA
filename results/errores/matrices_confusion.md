# Matrices de confusion (P1, pliegues de prueba agregados)

Filas = clase real, columnas = clase predicha. Semilla 42; los modelos deterministas dan la misma matriz con las tres semillas (ver `matrices_confusion.json`), el MLP se muestra con las tres.

## Trivial (clase mayoritaria)

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 6 | 0 |
| 4 | 3 | 0 |

## Clasico 1: logistica ordinal

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 6 | 0 |
| 4 | 2 | 1 |

## Clasico 2: arbol de profundidad 1

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 5 | 1 |
| 4 | 1 | 2 |

## Profundo: MLP 1-8-1 - semilla 42

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 5 | 1 |
| 4 | 1 | 2 |

## Profundo: MLP 1-8-1 - semilla 7

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 5 | 1 |
| 4 | 1 | 2 |

## Profundo: MLP 1-8-1 - semilla 2026

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 5 | 1 |
| 4 | 1 | 2 |

## Propuesto: agente en lazo

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 5 | 1 |
| 4 | 0 | 3 |

## Ablacion: lazo sin 'recuperar'

| real \ predicha | 3 | 4 |
|---|---|---|
| 3 | 6 | 0 |
| 4 | 1 | 2 |
