# Las cinco cosas que lo hacen distinto de un estudio de laboratorio

Son el diseño del proyecto, no una descripción de lo que ya corre. **Cada una
lleva el hito en que deja de ser una promesa**: ✅ ya está, 🕓 todavía no. En un
repo que vende rigor, escribir en presente lo que no existe es el peor fallo
posible, más grave que un bug.

1. ✅ **El juez no es concursante.** Este repo no construye ni construirá un
   extractor propio. Si lo hiciera, el ranking valdría cero. Es una regla, no
   código, y se cumple desde el primer día.
2. ✅🕓 **L3-L4 · Verdad de referencia gratis y auditable.** El BOE publica el mismo
   documento como PDF firmado y como XML con marcado de tabla real. **Ya está: 1.000
   documentos emparejados (L3) y la verdad derivada reproduciendo 25 de 30 tablas
   transcritas a mano, con cero discrepancias atribuibles al código (L4).** Lo que
   sigue 🕓 es lo que de verdad la valida: **su error frente a auditoría humana se
   mide en L8b**, y hasta entonces nadie sabe cuánto vale. Y L4 dejó medido que su
   propia muestra **no puede ver** una clase de fallo del código (límites 65-66).
3. ✅🕓 **L3 · El motor no sabe qué es el BOE.** Cualquier entidad entra por un
   adaptador de siete métodos, con su fuente, su modo de verdad, su licencia, su
   privacidad y su vocabulario: el `Protocol` y su suite de conformidad **están
   escritos, y antes que su primera implementación**. Lo que sigue 🕓 es la única
   prueba de verdad de que la interfaz aguanta: **una segunda entidad real, en
   L13**. Con un solo adaptador, «es genérico» es una intención.
4. 🕓 **L8 · La licencia y la privacidad serán código.** Cuando un adaptador
   declare `may_send_to_third_party: false`, el motor **rechazará** los
   extractores por API y la campaña no arrancará, con código de salida 2. No será
   una advertencia. Hoy no hay motor, ni CLI, ni `benchcore.core.policy`: la
   cadena entera se cablea en L8.
5. ✅🕓 **Ningún error se traga.** El enum cerrado de causas y el invariante que
   impide registrar un fallo sin causa **ya son código** (`docbench_es.types`,
   L0). Que además **se cuente en el informe** —la tasa de fallo por extractor
   como resultado publicado— llega con el informe, en **L5**.
