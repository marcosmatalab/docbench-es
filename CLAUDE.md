# docbench-es · instrucciones de proyecto

Banco de extracción documental en español, adaptable a cualquier entidad.
La especificación completa está en `MANUAL.md`, en la raíz del repo. **Léela con
`Read` antes de proponer nada.** No se importa aquí a propósito: son unas 1.800 líneas
y `@` las metería enteras en el contexto de cada sesión.

## La regla que gobierna todo el repo

> **Este proyecto vende rigor. Cualquier cosa que el repo afirme y el código no
> cumpla es el fallo más grave posible aquí, más grave que un bug.**

De ahí salen las demás reglas.

## Reglas de oro, en orden

1. **El juez no puede ser concursante.** `docbench-es` NUNCA construye un extractor
   propio. Si alguna vez parece buena idea, no lo es: el ranking valdría cero.
2. **Todo número publicado lleva su intervalo y su comando de reproducción.** Un
   número sin intervalo no se publica. Un número que no se puede reproducir no existe.
3. **El bootstrap remuestrea DOCUMENTOS, nunca preguntas.** Las preguntas de un mismo
   documento están correlacionadas.
4. **Un extractor que no expresa `rowspan`/`colspan` sale `NO_APLICABLE`, no cero**,
   y su nota va siempre con su cobertura evaluable.
5. **La licencia y la privacidad son código.** Si un adaptador declara
   `may_send_to_third_party: false`, el motor **rechaza** los extractores por API y la
   campaña no arranca. No es una advertencia.
6. **Ningún error se traga.** Un documento que falla se registra con su causa del enum
   cerrado y **se cuenta en el informe**. La tasa de fallo por extractor es un resultado.
7. **Toda normalización se documenta.** Una normalización agresiva es una forma
   silenciosa de hacer trampas a favor de un extractor.

## Cómo se trabaja aquí

- **Plan de 10 líneas y OK antes de picar.** Siempre. Usa `/hito`.
- **Ningún fichero por encima de 300 líneas.** Si un módulo crece, se parte.
- **Un extractor por fichero. Un adaptador de fuente por fichero.** Nada de módulos
  que agrupan cinco cosas.
- **Contrato primero, implementación después.** El `Protocol` y su suite de
  conformidad se escriben antes que cualquier implementación.
- **Golden file antes que métrica.** Antes de escribir TEDS existen los casos de
  PubTabNet contra los que se valida.
- **Al cerrar un hito: `/cerrar`.** Incluye escrutinio adversarial obligatorio.

## Comandos

```bash
make quickstart   # 20 documentos versionados, 4 extractores locales, < 3 min, sin red
make fast         # lint + tipos + arquitectura + núcleo puro. < 90 s. LA PUERTA
make full         # + contratos, hostiles, secretos, degradación, deriva, e2e. Docker
make test         # pytest tests/unit
make arch         # lint-imports: el contrato de capas
make bench PLAN=…  ·  make report CAMPANA=…
make fix          # ruff format + ruff check --fix
```

`make fast` es la puerta. **No se cierra un hito con la puerta en rojo.**

## El contrato de capas

Está en **`.importlinter`** —con ese nombre exacto: import-linter no lee un fichero
llamado `importlinter.ini`— y lo verifica el CI. Además del orden de capas, con
`exhaustive = true` para que un paquete nuevo sin ubicar ponga el CI rojo, hay tres
prohibiciones, y cada una hace cumplir una afirmación del README:

| Prohibición | La afirmación que protege |
|---|---|
| `core` no importa `extract`, `entity`, `corpus`, `sources`, `truth` | El núcleo es puro: se prueba sin red y se puede reejecutar sobre extracciones viejas |
| `drift` no importa `truth` | La deriva funciona **sin verdad de referencia nueva**, o sea que es ejecutable en producción |
| `route` no importa `extract`, `ask`, `truth` | La recomendación sale de números publicados, no de una heurística escondida |

**Si `lint-imports` se pone rojo, no es un problema de estilo: es una promesa del
proyecto que se acaba de romper.** Se arregla el import, nunca el contrato.

## Ficheros congelados

Están congelados `tests/fixtures/pubtabnet/**`, `tests/fixtures/tablas/**`,
`tests/fixtures/quickstart/**` y cualquier `plan.yaml` **que ya exista**. Crearlos la
primera vez sí se puede: si no, L2, L6 y L7 serían imposibles.

Lo hacen cumplir **dos hooks, y ninguno de los dos basta solo**:

| Hook | Cuándo | Qué cubre | Qué NO cubre |
|---|---|---|---|
| `guard-frozen.sh` | `PreToolUse` | **Previene**: deniega la escritura por `Write`, `Edit` y `NotebookEdit` | Cualquier otra vía. Su `matcher` son esas tres herramientas y nada más |
| `stop-gate.sh` | `Stop` | **Detecta**, por dos vías: `git diff --diff-filter=MDRT HEAD` para lo que ya está en `HEAD`, y un manifiesto de huellas SHA-256 (`.claude/.congelados.sha256`) para el fixture recién creado que todavía no lo está | El cambio hecho **en el mismo turno en que el hook ve el fichero por primera vez**: esa primera huella es la que se toma como buena |

La prevención cubre las tres herramientas de edición; la detección al cerrar el
turno cubre el resto. Un `cat >`, un `sed -i`, un `mv`, un `rm` o un
`uv run python -c` **esquivan `guard-frozen.sh` por completo** —su `matcher` no los
ve— y los caza el `Stop`. No se pueden enumerar todas las formas de escribir un
fichero; sí se puede mirar el resultado.

Las dos vías del `Stop` hacen falta: `git diff` contra `HEAD` no ve un fixture
recién creado, y ése es su estado durante **todo** el hito que lo crea (L2, L6,
L7). El manifiesto cubre esa ventana: la primera vez que ve un congelado anota su
huella y lo deja pasar —eso es crearlo—; a partir de ahí cualquier cambio se caza,
commiteado o no. Si el usuario aprueba cambiar una referencia, se borra su línea
del manifiesto para refijar la huella. El límite que queda está en `LIMITS.md` 27.

**Si un test falla contra un fichero congelado, el fallo está en el código.** No se
toca la verdad de referencia para que salgan los números.

## Qué NO hacer nunca

- No añadir un extractor propio al proyecto.
- No usar `float` para dinero. `Decimal`.
- No publicar exactitud en modo de verdad `NONE`. El motor debe negarse.
- No redistribuir contenido de un adaptador con `may_redistribute_content: false`.
- No registrar un adaptador con `special_categories: true`.
- No "arreglar" un test cambiando lo que se espera. Arregla el código o declara el
  límite en `LIMITS.md`.
- No dejar un hito cerrado sin su número en `RESULTS.md`.

## Reglas que se cargan solas

En `.claude/rules/` hay 3 ficheros con `paths:` en el frontmatter. **No hace falta
importarlos**: Claude Code los mete en contexto solo cuando se leen ficheros que casan
con sus globs, y salen del contexto cuando no hacen falta.

- `.claude/rules/extractores.md`
- `.claude/rules/nucleo-puro.md`
- `.claude/rules/tests.md`

Si cambias la estructura de directorios, **revisa esos globs**: una regla cuyo `paths:`
no casa con nada es una regla que no existe, y no avisa de ello.

## Documentos de referencia

- `MANUAL.md` — la especificación completa. Modelo de datos, interfaces, hitos.
- `HITOS.md` — el prompt literal de cada hito.
- `ESTADO.md` — dónde estamos. **Lo inyecta el hook `SessionStart`**, así que ya lo
  tienes arriba: no hace falta volver a leerlo cada sesión.
- `LIMITS.md` — lo que este proyecto NO mide. Se escribe conforme se descubre. Lo crea L0.
- `RESULTS.md` — los números medidos, con fecha y comando. Lo crea L0.
- `docs/adr/` — una decisión por fichero, con su alternativa descartada.
