## Context

El repo tiene 8 paquetes funcionales y una API FastAPI. Los paquetes tienen fallback graceful (si un servicio externo no está disponible, retornan datos vacíos, no crashean). Esto significa que los scripts pueden ejecutarse sin una base de datos ni LLM reales y mostrar el flujo de datos, pero con valores vacíos o fallback.

Cada script debe:
1. Mostrar claramente qué está importando y llamando
2. Imprimir el resultado con `print()` legible
3. Ser ejecutable con un solo comando desde la raíz del repo

## Goals / Non-Goals

**Goals:**
- 6 scripts standalone en `examples/`, numerados del 01 al 06
- Cada script testea una capa específica; escala de paquete individual → sistema completo
- Se pueden ejecutar en orden o individualmente
- Sin dependencias entre scripts — cada uno se basta a sí mismo

**Non-Goals:**
- No hay abstracciones, clases de runner, ni módulos compartidos
- No hay asserts ni framework de testing — solo ejecutar y ver output
- No se siembran datos en DB ni se mockean servicios
- No se integra en CI

## Decisions

### D1: Scripts numerados por capa de sistema

El número refleja la profundidad en el stack. Cada script cubre 1-2 paquetes de la misma capa y escala hasta los puntos de entrada:

| Script | Capa | Paquete(s) cubiertos | Dependencias externas |
|--------|------|---------------------|-----------------------|
| `01_storage_state_smoke.py` | Persistencia | `storage`, `state` | ninguna (fallback sin DB) |
| `02_memory_retrieval_smoke.py` | Servicios de datos | `memory`, `retrieval` | ninguna (fallback sin DB) |
| `03_context_observability_smoke.py` | Ensamblado + trazas | `context_assembler`, `observability` | ninguna |
| `04_model_tool_runtime_smoke.py` | LLM + herramientas | `model_adapter`, `tool_runtime` | API key OpenAI/Anthropic (opcional) |
| `05_orchestrator_direct.py` | Orquestador completo | `orchestrator` (ejercita los 9 paquetes) | API key opcional |
| `06_api_worker_e2e.py` | Puntos de entrada | API HTTP + `apps/worker` | servidor en :8000 (opcional) |

Alternativa considerada: un solo script e2e — descartado porque no ayuda a entender dónde falla si algo está mal.
Alternativa considerada: un script por paquete (9 scripts) — descartado porque paquetes de la misma capa comparten contexto y es más eficiente mostrarlos juntos.

### D2: `PYTHONPATH=packages` como convención

Los paquetes no están instalados como módulos del sistema. La forma más simple de importarlos sin instalar nada extra es `PYTHONPATH=packages python3 examples/0X_<script>.py`. Cada script incluye un comentario en la primera línea con el comando exacto.

### D3: Output legible, no silencioso

Cada script imprime:
- El input que se pasó
- El resultado crudo (repr o JSON dump del objeto retornado)
- Una línea de resumen indicando si hubo fallback o datos reales

No se lanza excepción si hay fallback — se imprime `⚠️ fallback: <razón>` para que el desarrollador entienda qué está pasando.

## Risks / Trade-offs

- **[Riesgo] `04_model_tool_runtime_smoke.py` falla sin API key** → Mitigación: captura el error e imprime `⚠️ No LLM configured: set OPENAI_API_KEY or ANTHROPIC_API_KEY` — exit 0. La sección de `tool_runtime` siempre se ejecuta (no necesita LLM).
- **[Riesgo] `06_api_worker_e2e.py` falla si el servidor no está corriendo** → Mitigación: captura `URLError` e imprime el comando para iniciar el servidor; la sección del worker se ejecuta de todas formas de manera directa.
- **[Trade-off] Sin asserts — el desarrollador debe interpretar el output** → Decisión positiva: el propósito es explorar y entender, no hacer pasar un test suite.
- **[Trade-off] Scripts 01-05 necesitan `PYTHONPATH=packages`** → Es la convención del repo; cada script lo documenta en la primera línea.
