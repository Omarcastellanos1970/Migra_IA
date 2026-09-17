# MIGRA-IA — contrato de nombres ES→EN

Este archivo es el **contrato de nombres** del repositorio bilingüe. Todo
renombrado que se aplique al código, a las claves de datos y a los nombres de
archivo sale de aquí, y no se renombra nada que no esté listado. Se escribe
antes del refactor a propósito: aprobar una lista de términos es barato,
deshacer 275 funciones renombradas no lo es.

La versión inglesa de este documento es `docs/en/GLOSSARY.md`. Las dos se
mantienen al día, y ninguna mezcla idiomas: **un documento se escribe en un
solo idioma de principio a fin.** El único elemento bilingüe admitido en
cualquier sitio es una tabla de términos, cuyas dos columnas son la traducción
misma.

## 1. Alcance: qué se traduce y qué no

**Regla rectora, fijada por el autor:** *todo lo que describe el funcionamiento
del agente, y el cuestionario, debe existir en los dos idiomas.*

| Capa | ¿Bilingüe? | Forma |
|---|---|---|
| Contenido del agente — cuestionario, base de conocimiento, procedimiento, informe emitido | **Sí** | `data/es/` y `data/en/`, seleccionado por `MIGRA_IA_LANG` |
| Documentación que describe cómo funciona el agente — reglas de puntuación, características de dominio, protocolo de validación, línea base reproducible, evaluación interna, riesgo de datos, formularios de etiquetado, informe de ejemplo | **Sí** | `docs/` (ES) + `docs/en/` (EN) |
| Guías de instalación y despliegue, README, landing, tarjeta del artefacto | **Sí** | `README.md` + `README.en.md`, selector ES \| EN en la página |
| Demo web (`migra-ia.onrender.com`) | **Sí** | Selector ES \| EN |
| Metadatos de Zenodo y `CITATION.cff` | **Un idioma por campo** | Un campo de título no puede llevar dos idiomas sin mezclarlos, que es lo que prohíbe la D4. Punto abierto: hoy el registro publicado está en español — ver la sección 13 |
| Identificadores del código — módulos, funciones, claves de esquema | **No — versión única, en inglés** | Nombres internos; quien usa el agente en español no los ve nunca |
| `BITACORA.md` y los 57 mensajes de commit | **No — se quedan en español** | Son el registro histórico de lo que se hizo, no una descripción de cómo funciona el agente. Reescribir la historia cambiaría todos los SHA y rompería las releases archivadas en Zenodo |

## 2. Regla 0 — lo que NUNCA se renombra

Parecen identificadores, pero son **datos**. Renombrarlos corrompería el
conjunto de datos o rompería la correspondencia con el paper:

- Nombres de marca y plataforma usados como clave: `Siemens`, `Rockwell`,
  `Mitsubishi`, `Schneider`, `Omron`, `PLC-5 (1785)`, `SLC 500`,
  `S7-300 / ET 200M`, `Modicon Quantum`, `Modicon Premium`,
  `MELSEC-A/QnA (tipo grande)`, `MELSEC AnS/QnAS`, `SYSMAC CS1`,
  `SYSMAC CJ1 (Europa)`.
- Los códigos de pregunta `S1a`…`S30c` y los códigos de factor como `M01`.
- Los códigos de subproblema `P1`, `P2`, `P3` — son las etiquetas del propio
  paper.
- El nombre del paquete `migra_ia` y el nombre del producto **MIGRA-IA**.
- `loto` — LOTO (lockout/tagout) es el término internacional en los dos
  idiomas.
- El nombre del repositorio `Migra_IA`, su URL y el DOI de concepto
  `10.5281/zenodo.21480949`, que el paper imprime.

**Comprobado:** ni `Paper_Tesis.tex` ni `Paper_Tesis_EN.tex` citan un solo
nombre de archivo del repositorio — solo la URL de GitHub y el DOI. Renombrar
archivos no toca el paper.

## 3. Módulos — `migra_ia/`

| ES | EN |
|---|---|
| `agente.py` | `agent.py` |
| `caso.py` | `case.py` |
| `conocimiento.py` | `knowledge.py` |
| `cuestionario.py` | `questionnaire.py` |
| `fabricantes.py` | `manufacturers.py` |
| `herramientas.py` | `tools.py` |
| `interactivo.py` | `interactive.py` |
| `nucleo.py` | `core.py` |
| `procedimiento.py` | `procedure.py` |
| `config.py` · `prompt.py` · `scoring.py` · `__init__.py` | sin cambio (ya están en inglés) |

## 4. Scripts

| ES | EN |
|---|---|
| `_caracteristicas.py` | `_features.py` |
| `_etiquetado.py` | `_labeling.py` |
| `_evaluacion.py` | `_evaluation.py` |
| `_figura_comparacion.py` | `_figure_comparison.py` |
| `_generar_procedimiento.py` | `_generate_procedure.py` |
| `_interactivo_run.py` | `_interactive_run.py` |
| `_plantilla_ciega.py` | `_blind_template.py` |
| `_reglas_puntuacion.py` | `_scoring_rules.py` |
| `_tabla_ii.py` | `_table_ii.py` |
| `_baseline.py` · `_figura_p3.py` · `_smoke_test.py` | sin cambio |

Los puntos de entrada que ve el usuario se **añaden, no se renombran**, para
que los españoles sigan funcionando: `EMPIEZA_AQUI.txt` + `START_HERE.txt`,
`INSTALAR.bat` + `INSTALL.bat`, `Iniciar_MIGRA-IA.bat` + `Start_MIGRA-IA.bat`.

## 5. Archivos de datos

**Dependientes del idioma** (una copia por idioma, las mismas claves inglesas
en las dos):

| ES | `data/es/` y `data/en/` |
|---|---|
| `base_conocimiento.json` | `knowledge_base.json` |
| `cuestionario.json` | `questionnaire.json` |
| `procedimiento_migracion.json` | `migration_procedure.json` |
| `fabricantes_cpu.json` | `cpu_manufacturers.json` |

**Neutros respecto al idioma** (copia única en `data/`, claves en inglés — ver
la decisión D2):

| ES | EN |
|---|---|
| `ciclo_vida_plataformas.csv` | `platform_lifecycle.csv` |
| `particion_ciclo_vida.json` | `lifecycle_partition.json` |
| `etiquetas_p1_p2.json` | `labels_p1_p2.json` |
| `figura_comparacion_propuesta.csv` | `figure_comparison_proposal.csv` |
| `figura_p3_verificador.csv` | `figure_p3_verifier.csv` |

## 6. Cabeceras de los CSV

`platform_lifecycle.csv` — el conjunto de datos de P1, separado por `;`:

| ES | EN | Paper (EN) |
|---|---|---|
| `Fabricante` | `manufacturer` | «grouped by manufacturer» |
| `Plataforma` | `platform` | «platform» |
| `Lanzamiento` | `release` | «release» |
| `Anuncio_fin_de_vida` | `end_of_life_announcement` | «status declared by the vendor» |
| `Fin_comercializacion` | `end_of_manufacturing` | «end of manufacturing» |
| `Fin_repuestos_reparacion` | `end_of_spare_parts` | «spare parts» |
| `Vida_comercial_anios` | `commercial_life_years` | «commercial life cycles» |
| `Soporte_total_anios` | `total_support_years` | «support horizon» |
| `Nivel` | `level` | «four ordered classes» |

`figure_comparison_proposal.csv`: `metrica,media,sd` → `metric,mean,sd`.

`figure_p3_verifier.csv`: `iteracion,programas_pasan,programas_total,notas` →
`iteration,programs_passing,programs_total,notes`.

## 7. Términos de dominio — la autoridad es el paper en inglés

Están tomados literalmente de `Paper_Tesis_EN.tex`, no inventados. Donde el
paper distingue dos palabras, la distinción se respeta.

| ES | EN | Nota |
|---|---|---|
| fabricante | **manufacturer** | La entidad del conjunto de datos, la variable de agrupamiento |
| (la empresa que publica documentación) | **vendor** | El paper reserva *vendor* para la documentación declarada |
| obsolescencia | obsolescence | |
| migración | migration | |
| reacondicionamiento | refurbishment | Del título del paper |
| ciclo de vida | life cycle (prosa) / `lifecycle` (identificadores) | |
| fin de comercialización | end of manufacturing | |
| repuestos | spare parts | |
| cuestionario | questionnaire | |
| base de conocimiento | knowledge base | |
| línea base | baseline | |
| ordinal | ordinal | |
| recuperación | retrieval | |
| verificación / verificador | verification / verifier | |
| etapa | stage | |
| fase | phase | |
| procedimiento | procedure | |
| plataforma | platform | |
| heredado, legado | legacy | |
| descontinuado | discontinued | |
| pliegue | fold | Validación cruzada |
| semilla | seed | |
| exactitud | accuracy | |
| puntuación, riesgo | score, risk | |
| expediente | case file | |
| ruta (de migración) | route | |
| origen → destino | source → target | Dirección de la migración |

## 8. Claves de esquema

Claves recurrentes, aplicadas en todos los archivos de datos:

| ES | EN | ES | EN |
|---|---|---|---|
| `titulo` | `title` | `subtitulo` | `subtitle` |
| `nombre` | `name` | `descripcion` | `description` |
| `nota` | `note` | `fecha` | `date` |
| `fuente` / `fuentes` | `source` / `sources` | `codigo` | `code` |
| `clave` | `key` | `tipo` | `type` |
| `estado` | `status` | `objetivo` | `objective` |
| `proposito` | `purpose` | `criterio` / `criterios` | `criterion` / `criteria` |
| `regla` / `reglas` | `rule` / `rules` | `guia` | `guide` |
| `ejemplo` | `example` | `advertencia` | `warning` |
| `detalle` | `detail` | `etiqueta` / `etiquetas` | `label` / `labels` |
| `opciones` | `options` | `paso` / `pasos` | `step` / `steps` |
| `fase` / `fases` | `phase` / `phases` | `etapa` / `etapas` | `stage` / `stages` |
| `rol` | `role` | `evidencia` | `evidence` |
| `prerrequisitos` | `prerequisites` | `requiere` | `requires` |
| `marca` | `brand` | `familia` | `family` |
| `modelos` | `models` | `generaciones` | `generations` |
| `observacion` | `remark` | `caso` / `casos` | `case` / `cases` |
| `documento` | `document` | `capitulos` | `chapters` |
| `actividades` | `activities` | `dispositivo` | `device` |
| `riesgos` | `risks` | `pruebas` | `tests` |
| `plantillas` | `templates` | `rutas` | `routes` |
| `rama` | `branch` | `orden` | `order` |
| `cobertura` | `coverage` | `principio` | `principle` |
| `profundidad` | `depth` | `extension` | `extension` |

Claves compuestas:

| ES | EN |
|---|---|
| `aprobacion_humana` | `human_approval` |
| `maquina_detenida` | `machine_stopped` |
| `especialista_seguridad` | `safety_specialist` |
| `criterio_salida` | `exit_criterion` |
| `criterios_salida_por_etapa` | `stage_exit_criteria` |
| `nota_agente` | `agent_note` |
| `cubierto_por_cuestionario` | `covered_by_questionnaire` |
| `especializa_paso` | `specializes_step` |
| `afecta_a_pasos` | `affects_steps` |
| `aplica_a_pasos` | `applies_to_steps` |
| `total_pasos` | `total_steps` |
| `huecos_declarados` | `declared_gaps` |
| `capa_anotada` | `annotated_layer` |
| `campos_propuestos` | `proposed_fields` |
| `punto_de_decision_cpu` | `cpu_decision_point` |
| `opciones_cpu_destino` | `target_cpu_options` |
| `rutas_por_fabricante` | `routes_by_manufacturer` |
| `ruta_cambio_de_marca` | `brand_change_route` |
| `variante_cambio_marca` | `brand_change_variant` |
| `variante_sin_respaldo` | `no_backup_variant` |
| `activa_variante` | `activates_variant` |
| `excluye_variante` | `excludes_variant` |
| `habilita_ruta_por_fabricante` | `enables_manufacturer_route` |
| `familias_origen` / `familias_destino` | `source_families` / `target_families` |
| `destino_step7_s7_300_400` | `target_step7_s7_300_400` |
| `destino_tia_portal` | `target_tia_portal` |
| `origen_metodologico` | `methodological_origin` |
| `alternativa_mapa_decision` | `decision_map_alternative` |
| `soporte_de_datos` | `data_support` |
| `limite_duro` | `hard_limit` |
| `bloqueante` | `blocking` |
| `condicion_de_uso` | `usage_condition` |
| `nota_aplicacion` | `application_note` |
| `nota_tecnica` | `technical_note` |
| `a_favor` / `en_contra` | `pros` / `cons` |
| `que_ofrece` | `what_it_offers` |
| `regla_adaptativa` | `adaptive_rule` |
| `que_decide` | `what_it_decides` |
| `que_cambia` | `what_changes` |
| `condiciones_favorables` | `favorable_conditions` |
| `obligatorio` | `required` |
| `criterio_obligatorio` | `mandatory_criterion` |
| `disparador` / `disparadores` | `trigger` / `triggers` |
| `mapa_decision` | `decision_map` |
| `factores_riesgo` | `risk_factors` |
| `criterios_alternativa` | `alternative_criteria` |
| `evaluar_primero` | `evaluate_first` |
| `variantes_de_ejecucion` | `execution_variants` |
| `como_se_ejecuta` | `how_it_is_executed` |
| `reglas_de_prioridad` | `priority_rules` |
| `opciones_por_fabricante` | `options_by_manufacturer` |
| `campos_por_modulo` | `fields_by_module` |
| `campos_por_dispositivo` | `fields_by_device` |
| `rama_si` / `rama_no` | `branch_yes` / `branch_no` |
| `preguntas_finales` | `final_questions` |
| `principios_rectores` | `guiding_principles` |
| `entregables_minimos` | `minimum_deliverables` |
| `procedimiento_recomendado` | `recommended_procedure` |
| `matriz_verificacion` | `verification_matrix` |
| `biblioteca_pruebas` | `test_library` |
| `anexos_gestion` | `management_annexes` |
| `casos_estudio` | `case_studies` |
| `aspectos_criticos` | `critical_aspects` |
| `puntos_clave` | `key_points` |
| `riesgo_tipico` | `typical_risk` |
| `software_legado` / `software_objetivo` | `legacy_software` / `target_software` |
| `redes_heredadas` | `legacy_networks` |
| `criterio_rigor` | `rigor_criterion` |
| `como_leer` | `how_to_read` |
| `observaciones_verificacion` | `verification_remarks` |
| `modelos_texto` | `models_text` |
| `referencia_catalogo` | `catalog_reference` |
| `nivel_confianza` | `confidence_level` |

Claves del conjunto de datos (`labels_p1_p2.json`, `lifecycle_partition.json`):

| ES | EN |
|---|---|
| `puesto` | `rank` |
| `antiguedad` | `age_years` |
| `anios_repuestos_restantes` | `spare_parts_years_left` |
| `estado_repuestos` | `spare_parts_status` |
| `procedencia` | `provenance` |
| `fecha_referencia` | `reference_date` |
| `evaluadores` | `raters` |
| `criterio_p2` | `p2_criterion` |
| `p1_clase` / `p1_regla` | `p1_class` / `p1_rule` |
| `p2_orden` / `p2_detalle` | `p2_ranking` / `p2_detail` |
| `pliegue` / `pliegues` | `fold` / `folds` |
| `entrenamiento` / `prueba` | `train` / `test` |
| `prueba_marcas` | `test_brands` |
| `esquema` | `scheme` |
| `nota_k` | `k_note` |
| `agrupamiento` | `grouping` |
| `preprocesamiento` | `preprocessing` |
| `semilla` | `seed` |
| `variable_admitida` | `allowed_variable` |

## 9. Funciones públicas

| Módulo | ES | EN |
|---|---|---|
| `knowledge.py` | `cargar_base` · `resumen_metodologia` · `indice_para_prompt` · `consultar` | `load_base` · `methodology_summary` · `prompt_index` · `query` |
| `questionnaire.py` | `cargar` · `pregunta` · `indice_para_prompt` · `criterios_para_prompt` · `consultar` | `load` · `question` · `prompt_index` · `prompt_criteria` · `query` |
| `manufacturers.py` | `cargar_catalogo` · `identificar` · `ficha` · `generaciones_actuales` · `sugerencias` · `tipo_de_producto` · `anclaje` · `indice_para_prompt` | `load_catalog` · `identify` · `profile` · `current_generations` · `suggestions` · `product_type` · `anchor` · `prompt_index` |
| `tools.py` | `ejecutar_herramienta` | `run_tool` |
| `interactive.py` | `factores` · `decidir` · `iniciar` · `responder` | `factors` · `decide` · `start` · `answer` |
| `core.py` | `aprobador_pendiente` · `ejecutar_turno` · `nuevo_cliente` | `pending_approver` · `run_turn` · `new_client` |
| `prompt.py` | `construir_system_prompt` | `build_system_prompt` |
| `scoring.py` | `clasificar` · `calcular_riesgo` | `classify` · `compute_risk` |
| `case.py` | clase `Caso` | clase `Case` |
| `webapp/app.py` | `nuevo_caso` · `mensaje` · `resumen` | `new_case` · `message` · `summary` |

`procedure.py`, con 28 funciones públicas, es la superficie más grande:

| ES | EN | ES | EN |
|---|---|---|---|
| `cargar` | `load` | `orden` | `order` |
| `total_pasos` | `total_steps` | `paso_bruto` | `raw_step` |
| `fase` | `phase` | `disparadores` | `triggers` |
| `huecos_declarados` | `declared_gaps` | `contexto` | `context` |
| `codigo_accesible` | `accessible_code` | `obsolescencia_sin_repuestos` | `obsolescence_without_spares` |
| `detectar_disparadores` | `detect_triggers` | `paso` | `step` |
| `texto_paso` | `step_text` | `estado` | `status` |
| `siguiente` | `next_step` | `bloqueos` | `blocks` |
| `opciones_destino` | `target_options` | `texto_opciones` | `options_text` |
| `rutas_fabricante` | `manufacturer_routes` | `ruta_fabricante` | `manufacturer_route` |
| `texto_ruta_fabricante` | `manufacturer_route_text` | `ruta_cambio_marca` | `brand_change_route` |
| `texto_ruta_cambio_marca` | `brand_change_route_text` | `ruta_para_paso` | `route_for_step` |
| `texto_ruta_para_paso` | `route_for_step_text` | `texto_ruta_resumen` | `route_summary_text` |
| `indice_para_prompt` | `prompt_index` | `consultar` | `query` |

## 10. Nombres de herramienta que ve el modelo

Estos 17 nombres son la superficie de API del agente: viajan en el prompt y el
modelo los llama por su nombre.

| ES | EN | ES | EN |
|---|---|---|---|
| `guardar_respuestas` | `save_answers` | `registrar_activo` | `register_asset` |
| `registrar_evidencia` | `register_evidence` | `registrar_dato_faltante` | `register_missing_data` |
| `registrar_bandera_seguridad` | `register_safety_flag` | `calcular_riesgo_obsolescencia` | `compute_obsolescence_risk` |
| `resumen_caso` | `case_summary` | `consultar_guia` | `query_guide` |
| `identificar_cpu` | `identify_cpu` | `consultar_catalogo` | `query_catalog` |
| `consultar_cuestionario` | `query_questionnaire` | `consultar_procedimiento` | `query_procedure` |
| `iniciar_guia_migracion` | `start_migration_guide` | `fijar_cpu_destino` | `set_target_cpu` |
| `marcar_paso_migracion` | `mark_migration_step` | `solicitar_aprobacion_humana` | `request_human_approval` |
| `generar_informe` | `generate_report` | | |

> **Advertencia, dicha por delante.** La clave del `.env` de la máquina de
> desarrollo es un marcador de posición (21 caracteres; una real pasa de 100),
> así que la API responde `401 authentication_error`. **La capa del LLM no se
> puede ejercitar en local**, de modo que estos 17 renombrados son verificables
> por inspección y mediante el motor determinista, pero no con una ejecución de
> punta a punta, hasta que haya una clave válida. El motor determinista
> —`scoring.py`, el catálogo y la guía— sí corre sin clave y es verificable por
> completo.

## 11. Verificación: números, no palabras

Con el contenido en inglés, un diff de prosa no prueba nada, porque todas las
cadenas han cambiado legítimamente. El refactor se verifica contra una **huella
numérica** capturada del motor determinista *antes* de cualquier renombrado:

| Informe | Números | SHA-256 (12) |
|---|---|---|
| `_baseline` | 288 | `9b0c7a7cbda3` |
| `_evaluation` | 420 | `9ddda752f4bc` |
| `_features` | 65 | `453806d927f8` |
| `_scoring_rules` | 188 | `be6212e8026a` |

Las dos cifras que el paper imprime tienen que sobrevivir intactas: **B0
trivial F1 0,402 ± 0,038** y **B1 clásico F1 0,688 ± 0,442**.

Dos generadores han divergido de su salida versionada y no deben ejecutarse a
ciegas después del renombrado: `_figure_p3.py` regenera las figuras de P3 con
`\begin{figure}[t]` mientras que los archivos versionados llevan un `[!tb]`
puesto a mano, y `_generate_procedure.py` se niega a regenerar porque el JSON
tiene bloques añadidos a mano (`routes_by_manufacturer`, `brand_change_route`,
pasos 23-25).

## 12. Decisiones tomadas

Fijadas por el autor el 2026-09-16; ya no son preguntas abiertas.

- **D1 — El idioma por defecto es `es`.** `MIGRA_IA_LANG` arranca en español,
  así que nada cambia para los usuarios actuales salvo que lo pidan.
- **D2 — Los tres archivos de datos se quedan en copia única, con claves en
  inglés.** `labels_p1_p2.json`, `lifecycle_partition.json` y
  `platform_lifecycle.csv` son mediciones atadas al paper, no una descripción
  de cómo funciona el agente, así que la regla bilingüe no los alcanza. Sus
  notas de procedencia en español pasan a inglés.
- **D3 — `ficha` → `profile`.**
- **D4 — Ningún documento mezcla idiomas.** Cada archivo se escribe en un solo
  idioma de principio a fin. No hay README bilingüe, ni página con una mitad en
  español y otra en inglés, ni sección añadida en el otro idioma. Dos
  consecuencias que condicionan la construcción: la landing se publica como
  **dos páginas separadas** —`docs/index.html` en español y
  `docs/en/index.html` en inglés— unidas por un selector que cambia la página
  entera, no partes de ella; y la demo web cambia de idioma como un todo, nunca
  por paneles. El único elemento bilingüe admitido es una tabla de términos,
  cuyas dos columnas son la traducción.
- **D5 — El inglés nunca se sirve como respaldo.** Si falta un archivo
  traducido, el cargador falla de forma ruidosa en vez de devolver en silencio
  contenido en español a un usuario inglés, que sería una pantalla con los dos
  idiomas mezclados. Un idioma solo se ofrece en el selector cuando sus
  archivos están completos.

## 13. Punto abierto: el idioma del registro de Zenodo

El registro archivado está en español: *«MIGRA-IA: Agente inteligente para
diagnóstico de obsolescencia y migración de sistemas de automatización
industrial»*, tanto en `.zenodo.json` como en `CITATION.cff`. Con la D4, ese
campo no puede llevar los dos idiomas, así que es uno o el otro.

Lo que ya está establecido: editar los metadatos de un depósito publicado **no
cambia el DOI** —verificado sobre el registro 22683608, que conservó
`10.5281/zenodo.22683608` después de editar su descripción—. Los **archivos**
de un registro publicado sí son inmutables, pero los metadatos no.

Esto no se decide aquí, porque cambiar el título de un registro científico vivo
es una acción hacia fuera y el paper cita el DOI de concepto. Las opciones son
dejar el registro en español y que la landing inglesa lleve la presentación en
inglés, o pasar el registro a inglés para que case con la versión inglesa del
paper.
