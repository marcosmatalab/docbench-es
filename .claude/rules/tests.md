---
paths:
  - "tests/**/*.py"
---

# Reglas de los tests

**La pregunta que hay que contestar para cada test nuevo no es "qué prueba" sino
"qué demuestra".** Si la respuesta es "que el código hace lo que hace", el test sobra.

- **Property-based con `hypothesis`** para los invariantes de `CanonicalTable`. Los
  casos límite escritos a mano nunca cubren solapes ni spans fuera de rango.
- **Golden files** para TEDS: contra la implementación de referencia de PubTabNet.
  TEDS no tiene valores intuibles, así que no se valida "a ojo".
- **Tests de degradación:** se degrada una extracción a propósito (borrar una fila,
  fundir dos celdas, romper una cabecera) y se comprueba que la métrica lo detecta.
  Esto es lo que demuestra que las métricas miden lo que dicen.
- **Adaptadores hostiles:** uno restrictivo, uno con categorías especiales, uno que
  prohíbe terceros. Demuestran que la política es código.
- **Ningún test toca la red** fuera de `tests/e2e`.
- **Determinismo:** todo lo que sortee lleva semilla fija y hay un test de dos corridas.

Si un test falla, el orden de sospecha es: **primero el código, segundo el test,
NUNCA el golden file.**
