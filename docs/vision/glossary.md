# Glossary

## Propósito

Este glosario define el vocabulario oficial del proyecto.
Su objetivo es evitar ambigüedades entre humanos, agentes de código y documentación.

---

## A

### Active Context
Conjunto de información que el sistema ensambla para una llamada concreta al modelo.
Incluye secciones como instrucciones, tools, message buffer, memory blocks,
archivos y contexto recuperado.

### Archival Memory
Memoria externa más estable y estructurada. Suele contener conocimiento ya procesado,
indexado o resumido, en lugar de solo historial bruto.

### Assembly / Context Assembly
Objeto final construido por el sistema que representa exactamente qué verá el modelo en una llamada.

---

## B

### Buffer / Message Buffer
Historial reciente de conversación o eventos que sigue siendo útil para el turno actual.

### Budget / Token Budget
Presupuesto de tokens disponible para ensamblar el contexto y reservar salida del modelo.

---

## C

### Compaction
Proceso de resumir o comprimir historial/contexto para conservar continuidad útil
sin seguir acumulando tokens de forma bruta.

### Context Engineering
Disciplina de diseñar cómo se selecciona, organiza, resume, recupera y fija
el contexto que entra al modelo en cada llamada.

### Context Window / Model Context Window
Cantidad máxima de contexto que el modelo puede procesar en una llamada concreta.

### Core Memory
Memoria persistente de alta señal que suele estar fijada en el contexto activo
por medio de memory blocks.

---

## E

### External Memory
Todo lo que queda fuera del contexto activo y puede recuperarse o consultarse después.
Incluye recall memory, archival memory y documentos/indexes externos.

---

## F

### Files / Artifacts
Documentos, adjuntos, notas o artefactos estructurados que pueden incorporarse
al contexto activo o mantenerse como referencias externas.

---

## J

### Just-in-Time Retrieval
Estrategia en la que el sistema recupera contexto externo solo cuando lo necesita,
en vez de cargarlo todo por adelantado.

---

## L

### Learned Context
Contexto ya procesado, reorganizado o consolidado para ser más útil que el raw context.

### Layered Memory
Modelo de memoria en varias capas, con diferentes roles:
buffer, core, recall y archival.

---

## M

### Memory Block
Unidad estructurada de core memory con identidad, contenido y límites definidos.

### MCP
Boundary o protocolo para exponer tools y recursos externos de forma desacoplada
respecto al núcleo del sistema.

### Model Adapter
Capa que normaliza cómo el sistema habla con distintos proveedores o modelos.

---

## O

### Orchestrator
Módulo que gobierna el flujo por turno:
carga estado, dispara retrieval, invoca assembler, llama al modelo y persiste resultados.

---

## P

### Prompt
Texto o estructura que forma parte de la llamada al modelo.
En este proyecto, el prompt es solo una parte del contexto activo, no el sistema entero.

---

## R

### Raw Context
Contexto bruto: historial crudo, documentos enteros o salidas sin consolidar.

### Recall Memory
Historial recuperable de interacciones pasadas o eventos del sistema.

### Retrieval
Proceso de buscar y traer contexto externo relevante al turno actual.

### Reranking
Proceso de reordenar resultados de retrieval para mejorar relevancia final.

---

## S

### Session State
Estado asociado a una sesión o conversación concreta.

### Sleep-Time Compute
Cómputo entre turnos que reorganiza y consolida memoria.

### Stateful Agent / Stateful System
Sistema cuya experiencia pasada influye en su comportamiento futuro
mediante estado persistente, no solo mediante historial efímero.

### State Manager
Módulo que administra estado explícito del sistema: sesión, tarea, archivos abiertos, etc.

### Subagent
Agente especializado usado por OpenCode o por el propio sistema
para resolver una parte delimitada del trabajo.

---

## T

### Task State
Parte del estado dedicada al progreso, objetivos y pendientes de una tarea.

### Tool Runtime
Módulo que registra y ejecuta tools internas o externas.

### Traceability
Capacidad de explicar qué contexto se ensambló, qué tools se invocaron
y por qué se produjo una respuesta.

---

## V

### Vector Search
Búsqueda semántica basada en embeddings o representaciones vectoriales.

---

## W

### Worker
Proceso en background que ejecuta tareas asíncronas o entre turnos,
como compaction o consolidación de memoria.
