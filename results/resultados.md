# Resultados - P1 (se regenera con `python _reproduce.py`)

Metrica principal: **F1 macro**. Media +- desviacion muestral entre los 2 pliegues, promediada sobre las semillas 42, 7, 2026.

| Modelo | F1 macro | Exactitud | sd entre semillas |
|---|---|---|---|
| Trivial (clase mayoritaria) | 0,402 +- 0,038 | 0,675 | 0,000 |
| Clasico 1: logistica ordinal | 0,688 +- 0,442 | 0,800 | 0,000 |
| Clasico 2: arbol de profundidad 1 | 0,748 +- 0,021 | 0,775 | 0,000 |
| Profundo: MLP 1-8-1 | 0,748 +- 0,021 | 0,775 | 0,000 |
| Propuesto: agente en lazo | 0,900 +- 0,141 | 0,900 | 0,000 |
| Ablacion: lazo sin 'recuperar' | 0,881 +- 0,168 | 0,900 | 0,000 |

## Ablacion

Quitar la funcion `recuperar` (la consulta de la politica de repuestos del fabricante) cambia el F1 macro de 0,900 a 0,881. Misma particion, mismas semillas, mismo codigo: la unica diferencia es el argumento `recuperar_activa`. Detalle por decision en `logs/decisiones.jsonl` (campo `variante`).

## Las cuatro funciones del lazo

1. **percibir**: toma solo la antiguedad (unica variable que deja la auditoria de fuga) y el fabricante.
2. **recuperar**: consulta `data/politicas_fabricante.json` (anios de repuestos que garantiza el fabricante) y cita la fuente; si no hay dato, no lo supone.
3. **decidir**: aplica los cortes 7,0 / 17,5 / 35,0 anios, derivados de medias ya publicadas, sin entrenar con estos datos.
4. **verificar**: contrasta la decision con la evidencia (una clase 3 pasa a 4 si la antiguedad supera 35 menos los anios de repuestos del fabricante) y marca para revision humana los cambios y los casos a menos de 2 anios de un corte.

## Limites que hay que leer junto a los numeros

- **n = 9 plataformas en 2 pliegues.** Cada pliegue tiene 4-5 casos: un solo acierto mueve el F1 de un pliegue en decenas de puntos. Las desviaciones son grandes y se solapan.
- **La regla de `verificar` se formulo despues de ver el unico fallo de la variante sin recuperacion** (MELSEC AnS/QnAS, 2026-09-14). No estaba congelada en el protocolo, asi que el resultado del metodo propuesto es **optimista**: falta validarlo en datos que no se hayan mirado.
- La misma regla produce un **falso positivo** (S7-300, politica de 10 anios): ver `results/errores/peores_casos.md`.
- El MLP es un modelo profundo sobre una sola variable y 4-5 filas de entrenamiento: esta declarado para cumplir el protocolo, no porque el tamanio del conjunto lo justifique. La sd entre semillas mide cuanto depende de la inicializacion.
- Las etiquetas se derivan de fechas (etiqueta provisional por regla, no juicio de panel).

## Entorno

- python: 3.14.6
- sistema: Windows 11
- procesador: Intel64 Family 6 Model 154 Stepping 3, GenuineIntel
- matplotlib: 3.10.9
