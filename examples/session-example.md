# Session Example

## Propósito

Este documento muestra un ejemplo narrativo de cómo una sesión atraviesa Context Kernel.

No es una especificación formal.
Sirve para explicar:

- qué entra por la API
- qué estado se carga
- qué memoria se usa
- qué retrieval ocurre
- qué contexto final ve el modelo
- qué se persiste después

---

## Scenario

Caso de uso:
**research assistant** con memoria persistente.

El usuario ya lleva varios turnos investigando "context engineering".
Ahora pregunta:

> "Dame una version final del mapa unificado que consolide todas las piezas en un solo marco"

---

## Existing state before the turn

### Session state
```json
{
 "session_id": "sess_001",
 "profile": "research_assistant",
 "active_mode": "analysis",
 "open_artifacts": ["doc_research_notes"],
 "last_turn_id": "turn_014"
}
Task state
{
 "goal": "investigar context engineering",
 "subtasks_open": [
   "unificar memoria + estado + contexto",
   "cerrar mapa final"
 ],
 "pending_questions": [
   "cómo representar el eje temporal",
   "cómo explicar sleep-time compute"
 ],
 "progress": "advanced"
}
Core memory
- label: user_preferences
 value: "prefiere explicaciones sencillas y ejemplos claros"

- label: current_research_topic
 value: "context engineering, agent memory, stateful agents, sleep-time compute"

- label: response_style
 value: "responder en español, con estructura clara y analogías simples"
Recall memory
Hay muchos turnos previos sobre:
ventana de contexto
memory blocks
stateful agents
sleep-time compute
arquitectura del sistema
Archival memory
Existe una nota consolidada:
title: "research synthesis draft"
content: "El sistema se entiende mejor como 4 capas: modelo, contexto activo, core memory y memoria externa, con estado y tiempo como ejes transversales."

Turn-time flow
1. Request enters API
Input
{
 "session_id": "sess_001",
 "message": "Dame una version final del mapa unificado que consolide todas las piezas en un solo marco"
}
API valida y entrega la petición al orchestrator.

2. Orchestrator loads state
Se cargan:
session state
task state
referencias activas
profile config
Resultado:
El sistema entiende que:
- seguimos en la misma investigación
- el usuario quiere síntesis final
- conviene usar memoria consolidada + algo de historial reciente

3. Memory manager returns memory snapshot
Included by default
core memory
recent message buffer
referencias a recall relevante
Decision
Como es una pregunta de síntesis final, el sistema decide:
no cargar mucho historial bruto
sí usar la nota consolidada
sí mantener pocas piezas recientes del buffer

4. Retrieval plan
El orchestrator decide:
recuperar una nota archivada de síntesis
no recuperar documentos externos nuevos
no ejecutar tools externas
Retrieval devuelve:
retrieved_context:
 - source: archival_memory
   title: "research synthesis draft"
   summary: "4 capas + ejes transversales"

5. Context assembly
El assembler recibe:
petición actual
estado
core memory
buffer reciente
nota archivada
límites del modelo
Budget example
total_window: 32000
reserved_for_output: 4000
usable_input_budget: 28000
Chosen sections
1. system instructions
2. response style constraints
3. task state summary
4. core memory
5. short recent buffer
6. archival synthesis note
7. current user request
Final assembly sketch
[SYSTEM]
- responder en español
- sintetizar y consolidar
- ser claro y estructurado

[TASK STATE]
- investigación avanzada sobre context engineering
- pendiente: mapa unificado final

[CORE MEMORY]
- usuario prefiere explicaciones sencillas
- tema actual: context engineering + memory + stateful + sleep-time

[RECENT BUFFER]
- últimos turnos donde se pidió el mapa final

[ARCHIVAL NOTE]
- síntesis: 4 capas + ejes transversales

[USER REQUEST]
- "Dame una version final del mapa unificado..."

6. Model call
El model adapter:
normaliza el formato de mensajes
aplica configuración
llama al proveedor
Resultado:
respuesta generada
token usage
metadata del call

7. Persist outcome
Se guarda:
mensaje del usuario
respuesta del sistema
context assembly usado
metadata de uso
posible actualización de task state
Task state updated
{
 "goal": "investigar context engineering",
 "subtasks_open": [],
 "pending_questions": [],
 "progress": "synthesis_delivered"
}

8. Between-turn follow-up
Más tarde, el sleep-time worker puede:
compactar el buffer
fusionar esta nueva síntesis con la nota archivada
generar una versión más madura de la investigación

What the example shows
Este ejemplo ilustra que el sistema:
no reenvía toda la conversación
no depende solo del buffer
usa core memory para continuidad
usa archival memory para síntesis estable
arma un contexto pequeño y de alta señal
mejora el estado después del turno

Anti-example
Lo que NO haría un sistema bien diseñado:
- reenviar 50 turnos completos
- meter todas las notas y todos los documentos
- duplicar la misma información en buffer y memory blocks
- olvidar actualizar task state después de la síntesis

Summary
request
 -> load state
 -> load memory
 -> retrieve note
 -> assemble compact high-signal context
 -> call model
 -> persist
 -> improve memory later
