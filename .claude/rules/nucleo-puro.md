---
paths:
  - "src/docbench_es/core/**/*.py"
---

# Reglas del núcleo puro

Este módulo **no toca el mundo**: sin red, sin disco, sin proveedor de modelos, sin
reloj, sin variables de entorno. Entra datos, sale resultado.

- Si necesitas la hora, se pasa como argumento. Nunca `datetime.now()`.
- Si necesitas aleatoriedad, se pasa la semilla. Nunca `random` sin semilla.
- Nada de `open()`, `requests`, `httpx`, `subprocess`.
- Toda función pública lleva anotación de tipos completa y pasa `mypy --strict`.
- Toda función que pueda recibir una entrada vacía o degenerada **declara qué hace en
  ese caso**, en el docstring y con un test.

Los tests de este módulo corren en `tests/unit` y el objetivo es **menos de 20
segundos para todo el paquete**. Si algo aquí tarda, es que ha dejado de ser puro.
