# MIGRA-IA — ES→EN naming contract

**Select language:** [Español](../GLOSARIO.md) · [English](GLOSSARY.md)

This file is the **naming contract** for the bilingual repository. Every rename
applied to code, data keys and file names comes from here, and nothing is
renamed that is not listed here. It is written before the refactor on purpose:
approving a term list is cheap, undoing 275 renamed functions is not.

The Spanish counterpart of this document is `docs/GLOSARIO.md`. The two are
kept in step, and neither mixes languages: **a document is written in one
language from beginning to end.** The only bilingual element allowed anywhere
is a term table, whose two columns are the translation itself.

## 1. Scope: what is translated and what is not

**Governing rule, set by the author:** *everything that describes how the agent
works, and the questionnaire, must exist in both languages.*

| Layer | Bilingual? | Form |
|---|---|---|
| Agent content — questionnaire, knowledge base, procedure, emitted report | **Yes** | `data/es/` and `data/en/`, selected by `MIGRA_IA_LANG` |
| Documentation describing how the agent works — scoring rules, domain features, validation protocol, reproducible baseline, internal evaluation, data risk, labelling forms, example report | **Yes** | `docs/` (ES) + `docs/en/` (EN) |
| Install and deployment guides, README, landing page, artifact card | **Yes** | `README.md` + `README.en.md`, ES \| EN selector on the page |
| Web demo (`migra-ia.onrender.com`) | **Yes** | ES \| EN selector |
| Zenodo / `CITATION.cff` metadata | **One language per field** | A single title field cannot hold two languages without mixing them, which D4 forbids. Open point: the published record is in Spanish today, and switching it to English edits a live scientific record — see section 13 |
| Code identifiers — modules, functions, schema keys | **No — single English version** | Internal names; never seen by a Spanish-speaking user |
| `BITACORA.md` and the 57 commit messages | **No — stay in Spanish** | A historical record of what was done, not a description of how the agent works. Rewriting history would change every SHA and break the archived Zenodo releases |

## 2. Rule 0 — what is NEVER renamed

These look like identifiers but are **data**. Renaming them would corrupt the
dataset or break the correspondence with the paper:

- Brand and platform names used as keys: `Siemens`, `Rockwell`, `Mitsubishi`,
  `Schneider`, `Omron`, `PLC-5 (1785)`, `SLC 500`, `S7-300 / ET 200M`,
  `Modicon Quantum`, `Modicon Premium`, `MELSEC-A/QnA (tipo grande)`,
  `MELSEC AnS/QnAS`, `SYSMAC CS1`, `SYSMAC CJ1 (Europa)`.
- Question codes `S1a`…`S30c` and factor codes such as `M01`.
- Subproblem codes `P1`, `P2`, `P3` — they are the paper's own labels.
- The package name `migra_ia` and the product name **MIGRA-IA**.
- `loto` — LOTO (lockout/tagout) is the international term in both languages.
- The repository name `Migra_IA`, its URL and the concept DOI
  `10.5281/zenodo.21480949`, which the paper prints.

**Verified:** neither `Paper_Tesis.tex` nor `Paper_Tesis_EN.tex` cites a single
repository file name — only the GitHub URL and the DOI. Renaming files does not
touch the paper.

## 3. Modules — `migra_ia/`

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
| `config.py` · `prompt.py` · `scoring.py` · `__init__.py` | unchanged (already English) |

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
| `_baseline.py` · `_figura_p3.py` · `_smoke_test.py` | unchanged |

User-facing entry points are **added, not renamed**, so the Spanish ones keep
working: `EMPIEZA_AQUI.txt` + `START_HERE.txt`, `INSTALAR.bat` + `INSTALL.bat`,
`Iniciar_MIGRA-IA.bat` + `Start_MIGRA-IA.bat`.

## 5. Data files

**Language-dependent** (one copy per language, same English keys in both):

| ES | `data/es/` and `data/en/` |
|---|---|
| `base_conocimiento.json` | `knowledge_base.json` |
| `cuestionario.json` | `questionnaire.json` |
| `procedimiento_migracion.json` | `migration_procedure.json` |
| `fabricantes_cpu.json` | `cpu_manufacturers.json` |

**Language-neutral** (single copy at `data/`, English keys — see decision D2):

| ES | EN |
|---|---|
| `ciclo_vida_plataformas.csv` | `platform_lifecycle.csv` |
| `particion_ciclo_vida.json` | `lifecycle_partition.json` |
| `etiquetas_p1_p2.json` | `labels_p1_p2.json` |
| `figura_comparacion_propuesta.csv` | `figure_comparison_proposal.csv` |
| `figura_p3_verificador.csv` | `figure_p3_verifier.csv` |

## 6. CSV headers

`platform_lifecycle.csv` — the P1 dataset, `;` separated:

| ES | EN | Paper (EN) |
|---|---|---|
| `Fabricante` | `manufacturer` | "grouped by manufacturer" |
| `Plataforma` | `platform` | "platform" |
| `Lanzamiento` | `release` | "release" |
| `Anuncio_fin_de_vida` | `end_of_life_announcement` | "status declared by the vendor" |
| `Fin_comercializacion` | `end_of_manufacturing` | "end of manufacturing" |
| `Fin_repuestos_reparacion` | `end_of_spare_parts` | "spare parts" |
| `Vida_comercial_anios` | `commercial_life_years` | "commercial life cycles" |
| `Soporte_total_anios` | `total_support_years` | "support horizon" |
| `Nivel` | `level` | "four ordered classes" |

`figure_comparison_proposal.csv`: `metrica,media,sd` → `metric,mean,sd`.

`figure_p3_verifier.csv`: `iteracion,programas_pasan,programas_total,notas` →
`iteration,programs_passing,programs_total,notes`.

## 7. Domain terms — the authority is the English paper

These are taken verbatim from `Paper_Tesis_EN.tex`, not invented. Where the
paper distinguishes two words, the distinction is kept.

| ES | EN | Note |
|---|---|---|
| fabricante | **manufacturer** | The entity in the dataset, the grouping variable |
| (la empresa que publica documentación) | **vendor** | The paper reserves *vendor* for declared documentation |
| obsolescencia | obsolescence | |
| migración | migration | |
| reacondicionamiento | refurbishment | From the paper title |
| ciclo de vida | life cycle (prose) / `lifecycle` (identifiers) | |
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
| pliegue | fold | Cross-validation |
| semilla | seed | |
| exactitud | accuracy | |
| puntuación, riesgo | score, risk | |
| expediente | case file | |
| ruta (de migración) | route | |
| origen → destino | source → target | Migration direction |

## 8. Schema keys

Recurring keys, applied across every data file:

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

Compound keys:

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

Dataset keys (`labels_p1_p2.json`, `lifecycle_partition.json`):

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

## 9. Public functions

| Module | ES | EN |
|---|---|---|
| `knowledge.py` | `cargar_base` · `resumen_metodologia` · `indice_para_prompt` · `consultar` | `load_base` · `methodology_summary` · `prompt_index` · `query` |
| `questionnaire.py` | `cargar` · `pregunta` · `indice_para_prompt` · `criterios_para_prompt` · `consultar` | `load` · `question` · `prompt_index` · `prompt_criteria` · `query` |
| `manufacturers.py` | `cargar_catalogo` · `identificar` · `ficha` · `generaciones_actuales` · `sugerencias` · `tipo_de_producto` · `anclaje` · `indice_para_prompt` | `load_catalog` · `identify` · `profile` · `current_generations` · `suggestions` · `product_type` · `anchor` · `prompt_index` |
| `tools.py` | `ejecutar_herramienta` | `run_tool` |
| `interactive.py` | `factores` · `decidir` · `iniciar` · `responder` | `factors` · `decide` · `start` · `answer` |
| `core.py` | `aprobador_pendiente` · `ejecutar_turno` · `nuevo_cliente` | `pending_approver` · `run_turn` · `new_client` |
| `prompt.py` | `construir_system_prompt` | `build_system_prompt` |
| `scoring.py` | `clasificar` · `calcular_riesgo` | `classify` · `compute_risk` |
| `case.py` | class `Caso` | class `Case` |
| `webapp/app.py` | `nuevo_caso` · `mensaje` · `resumen` | `new_case` · `message` · `summary` |

`procedure.py`, with 28 public functions, is the largest surface:

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

## 10. Tool names seen by the model

These 17 names are the agent's API surface: they travel in the prompt and the
model calls them by name.

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

> **Caveat, stated up front.** The `.env` key on the development machine is a
> placeholder (21 characters; a real one exceeds 100), so the API returns
> `401 authentication_error`. **The LLM layer cannot be exercised locally**,
> which means these 17 renames are verifiable by inspection and by the
> deterministic engine, but not by an end-to-end run, until a valid key is
> available. The deterministic engine — `scoring.py`, catalog and guide — runs
> without a key and is fully verifiable.

## 11. Verification: numbers, not words

Once the content is in English a prose diff proves nothing, because every
string legitimately changed. The refactor is verified against a **numeric
fingerprint** captured from the deterministic engine *before* any rename:

| Report | Numbers | SHA-256 (12) |
|---|---|---|
| `_baseline` | 288 | `9b0c7a7cbda3` |
| `_evaluation` | 420 | `9ddda752f4bc` |
| `_features` | 65 | `453806d927f8` |
| `_scoring_rules` | 188 | `be6212e8026a` |

The two figures the paper prints must survive unchanged: **B0 trivial
F1 0.402 ±0.038** and **B1 classical F1 0.688 ±0.442**.

Two generators have drifted from their committed output and must not be re-run
blindly after the rename: `_figure_p3.py` regenerates the P3 figures with
`\begin{figure}[t]` while the committed files carry a hand-placed `[!tb]`, and
`_generate_procedure.py` refuses to regenerate because the JSON holds
hand-added blocks (`routes_by_manufacturer`, `brand_change_route`, steps 23-25).

## 12. Decisions taken

Settled by the author on 2026-09-16; they are not open questions any more.

- **D1 — Default language is `es`.** `MIGRA_IA_LANG` defaults to Spanish, so
  nothing changes for current users unless they opt in.
- **D2 — The three dataset files stay single-copy, with English keys.**
  `labels_p1_p2.json`, `lifecycle_partition.json` and `platform_lifecycle.csv`
  are measurements tied to the paper, not a description of how the agent works,
  so the bilingual rule does not reach them. Their Spanish provenance notes
  move to English.
- **D3 — `ficha` → `profile`.**
- **D4 — No document mixes languages.** Every file is written in one language
  from beginning to end. There is no bilingual README, no page with a Spanish
  half and an English half, and no section appended in the other language. Two
  consequences that shape the build: the landing page ships as **two separate
  pages** —`docs/index.html` in Spanish, `docs/en/index.html` in English— tied
  by a selector that swaps the whole page rather than parts of it; and the web
  demo switches language as a whole, never per panel. The only bilingual
  element allowed is a term table, whose two columns are the translation.
- **D5 — English is never served as a fallback.** If a translated file is
  missing, the loader fails loudly instead of silently returning Spanish
  content to an English user, which would be a mixed-language screen. A
  language is offered in the selector only once its files are complete.

## 13. Open point: the language of the Zenodo record

The archived record is in Spanish: *«MIGRA-IA: Agente inteligente para
diagnóstico de obsolescencia y migración de sistemas de automatización
industrial»*, in `.zenodo.json` and `CITATION.cff` alike. Under D4 that field
cannot carry both languages, so it is one or the other.

What is already established: editing the metadata of a published deposit
**does not change the DOI** — verified on record 22683608, which kept
`10.5281/zenodo.22683608` after its description was edited. The **files** of a
published record are immutable, but the metadata is not.

This one is not decided here, because switching the title of a live scientific
record is outward-facing and the paper cites the concept DOI. The options are
to leave the record in Spanish and let the English landing page carry the
English presentation, or to move the record to English to match the English
version of the paper.
