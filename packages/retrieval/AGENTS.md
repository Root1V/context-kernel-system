# AGENTS.md

## Qué construye este módulo
Recupera contexto desde memoria externa, documentos e índices híbridos.

## Qué NO construye
- No ensambla el prompt final
- No persiste sesión
- No decide políticas de memoria

## Invariantes
- Retrieval primero filtra, luego busca, luego rerankea
- No devolver chunks redundantes si pueden agruparse
- Toda salida debe incluir metadata mínima para trazabilidad
