# Formulario de etiquetado por juicio experto

Para: coautores del trabajo. Tiempo estimado: 20-30 minutos.

Este formulario **no contiene ninguna salida del agente** ni el etiquetado
provisional que hay en el repositorio. Se responde con criterio propio; ese
es justamente el valor de lo que se pide.

Rellena tu nombre y responde las dos partes. Devuelve el archivo tal cual,
renombrado con tu apellido.

**Evaluador:** `_______________________`   **Fecha:** `___________`

---

## Parte 1 — Nivel de obsolescencia

Para cada plataforma, marca **una** clase de la escala:

- **1** — Activo, en comercializacion
- **2** — Anuncio de descontinuacion (phase-out)
- **3** — Descontinuado, aun con soporte y repuestos
- **4** — Descontinuado y sin soporte (fin de vida)

Los datos que se te dan son los publicados por el fabricante. Si consideras
que falta informacion para decidir, escribe `NS` en vez de adivinar: un
dato faltante declarado vale mas que una clase inventada.

### PLC-5 (1785)  (Rockwell)

- Lanzamiento: **1986**
- Anuncio de fin de vida: **2015-05**
- Fin de comercializacion: **2017-06**
- Fin de repuestos y reparacion: **2025-12**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### SLC 500  (Rockwell)

- Lanzamiento: **1991**
- Anuncio de fin de vida: **no publicado**
- Fin de comercializacion: **2024-03**
- Fin de repuestos y reparacion: **no publicado**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### S7-300 / ET 200M  (Siemens)

- Lanzamiento: **1995**
- Anuncio de fin de vida: **2023-10**
- Fin de comercializacion: **2025-10**
- Fin de repuestos y reparacion: **2033-10**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### Modicon Quantum  (Schneider)

- Lanzamiento: **1994**
- Anuncio de fin de vida: **2018-12**
- Fin de comercializacion: **2022-12**
- Fin de repuestos y reparacion: **no publicado**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### Modicon Premium  (Schneider)

- Lanzamiento: **1996**
- Anuncio de fin de vida: **2018-12**
- Fin de comercializacion: **2022-01**
- Fin de repuestos y reparacion: **no publicado**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### MELSEC-A/QnA (tipo grande)  (Mitsubishi)

- Lanzamiento: **1985**
- Anuncio de fin de vida: **no publicado**
- Fin de comercializacion: **2006-09**
- Fin de repuestos y reparacion: **2013-09**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### MELSEC AnS/QnAS  (Mitsubishi)

- Lanzamiento: **1993**
- Anuncio de fin de vida: **no publicado**
- Fin de comercializacion: **2014-09**
- Fin de repuestos y reparacion: **2021-09**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### SYSMAC CS1  (Omron)

- Lanzamiento: **1999**
- Anuncio de fin de vida: **2023-11**
- Fin de comercializacion: **2025-03**
- Fin de repuestos y reparacion: **2032-03**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

### SYSMAC CJ1 (Europa)  (Omron)

- Lanzamiento: **2001**
- Anuncio de fin de vida: **2024-05**
- Fin de comercializacion: **2025-03**
- Fin de repuestos y reparacion: **2032-01**

Clase (1-4, o NS): `____`    Comentario: `______________________________`

---

## Parte 2 — Prioridad de reemplazo

Ordena las nueve plataformas de **1 = se reemplaza primero** a **9 = puede
esperar**, suponiendo que las nueve estan instaladas en la misma planta y
compiten por el mismo presupuesto. Usa el criterio que usarias en tu planta;
no hay respuesta oficial.

- `____`  MELSEC AnS/QnAS  (Mitsubishi)
- `____`  MELSEC-A/QnA (tipo grande)  (Mitsubishi)
- `____`  Modicon Premium  (Schneider)
- `____`  Modicon Quantum  (Schneider)
- `____`  PLC-5 (1785)  (Rockwell)
- `____`  S7-300 / ET 200M  (Siemens)
- `____`  SLC 500  (Rockwell)
- `____`  SYSMAC CJ1 (Europa)  (Omron)
- `____`  SYSMAC CS1  (Omron)

En una linea, que peso le diste a cada cosa (obsolescencia, criticidad,
coste, riesgo de parada):

`__________________________________________________________________`
