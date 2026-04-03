## Why

El sistema tiene 8 paquetes construidos y un API funcional, pero nadie puede ejecutarlos de manera práctica para ver qué hacen. Los archivos en `examples/` son narrativas estáticas. Necesitamos scripts Python simples que cualquier desarrollador pueda correr para entender el sistema de manera incremental, empezando por un paquete y llegando hasta el e2e completo.

## What Changes

- Se agregan scripts Python en `examples/` numerados del 01 al 06, cada uno independiente y ejecutable directamente con `python3`.
- Cada script prueba una capa del sistema: empieza en los paquetes individuales y escala hasta el e2e HTTP completo.
- No se introduce ningún módulo nuevo ni clase de abstracción — cada script es standalone y autocontenido.
- Los scripts imprimen resultados legibles a stdout para que el desarrollador vea exactamente qué devuelve cada capa.

## Capabilities

### New Capabilities
- `e2e-incremental-scripts`: Colección de 6 scripts Python en `examples/` que prueban el sistema de manera incremental: memoria, retrieval, context assembly, model adapter, orquestador directo, y API HTTP e2e.

### Modified Capabilities
<!-- ninguna -->

## Impact

- Nuevos archivos:
  - `examples/01_storage_state_smoke.py` — paquetes `storage` + `state`
  - `examples/02_memory_retrieval_smoke.py` — paquetes `memory` + `retrieval`
  - `examples/03_context_observability_smoke.py` — paquetes `context_assembler` + `observability`
  - `examples/04_model_tool_runtime_smoke.py` — paquetes `model_adapter` + `tool_runtime`
  - `examples/05_orchestrator_direct.py` — paquete `orchestrator` (ejercita los 9 paquetes completos)
  - `examples/06_api_worker_e2e.py` — API HTTP (`POST /chat`) + worker (`enqueue_job` + `handle_compaction`)
- Sin cambios a ningún paquete existente, la API ni el worker
- Sin nuevas dependencias — usa solo stdlib + los paquetes ya instalados
- `PYTHONPATH=packages` requerido en los scripts del 01 al 05; el 06 también necesita `PYTHONPATH=packages:apps/worker`
