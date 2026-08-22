# RESULTS · docbench-es

> **La regla de este fichero.** Un número que no se puede reproducir no existe.
> Toda **estimación** lleva su intervalo; todo número que **no** es una estimación
> —un tiempo, un recuento, una tasa sobre el censo completo— lleva su método y su
> incertidumbre declarada: n, rango y resolución del instrumento. **Una cifra
> desnuda no se admite en ninguno de los dos casos.** Es la regla de oro 2 de
> `CLAUDE.md`, acotada en [ADR-0015](docs/adr/0015-alcance-de-la-regla-del-intervalo.md).
>
> **Aquí van los números. El método va en [`docs/metrics.md`](docs/metrics.md)**:
> qué mide cada ventana, con qué resolución, de dónde sale cada incertidumbre y el
> historial de correcciones. Lo que el proyecto NO mide, en
> [`LIMITS.md`](LIMITS.md).

## Lo que todavía NO hay aquí, dicho antes que lo que sí

**No hay ni un solo número de exactitud, de TEDS ni de coste.** A 22 de agosto de
2026, con L0 cerrado, hay esqueleto, modelo de datos y puerta de CI: ni corpus, ni
verdad de referencia, ni extractores. Cualquier número de calidad que apareciera
aquí estaría inventado. **El único número publicado hoy es un tiempo.**

| Número | Hito | Qué dirá |
|---|---|---|
| Primera tabla de estructura, con coste y cobertura evaluable | L5 | Qué extractor reconstruye mejor las tablas, cada métrica con su IC |
| **El titular**: hueco atribuible a la extracción | L10 | *"Con extracción perfecta X, IC [a,b]; con el mejor real Y, IC [c,d]; el hueco es Z puntos, IC [e,f]"* |
| Cuánto aporta la capa semántica | L11 | *"Cargar el glosario sube X puntos, IC [a,b]"* |

---

## L0 · Tiempo de la puerta rápida

Criterio: `make fast` en verde en menos de 90 s (§15 del manual). Es una de las
tres partes del criterio de L0; las otras dos —el control negativo y que
`lint-imports` encuentre `.importlinter`— no son números y están en
[`docs/metrics.md`](docs/metrics.md) y el [`CHANGELOG.md`](CHANGELOG.md).

### En el runner de GitHub · corrida del commit del cierre, `28186b9`

| Medida | Valor | Rango observado (n=4) | Resolución | Presupuesto | Margen |
|---|---|---|---|---|---|
| **`make fast`, el paso `la puerta`** | **4,43 s** | 3,41 – 4,43 s | ~0,1 s | **90 s** | **20×** |
| Job `fast` completo | 11 s | 10 – 14 s | 1 s | — | — |
| *Run* completo | 15 s | 14 – 18 s | 1 s | — | — |

**Sólo la primera fila es el criterio de L0.** El valor publicado es el de la
corrida del commit del cierre; el rango, el de las cuatro corridas que han corrido
este código. Qué mide cada fila, de dónde sale cada resolución y por qué el margen
de hoy no será el de L5: [`docs/metrics.md`](docs/metrics.md).

| Corrida | Commit | `make fast` | Job | Run | Ventana cruda (apertura → cierre) |
|---|---|---|---|---|---|
| [`32572385551`](https://github.com/marcosmatalab/docbench-es/actions/runs/32572385551) | `78ee8f0` | 3,41 s | 11 s | 16 s | `12:13:10.2845181Z` → `12:13:13.6938054Z` |
| [`32572585111`](https://github.com/marcosmatalab/docbench-es/actions/runs/32572585111) | `4e4ea0b` | 3,62 s | 10 s | 14 s | `12:17:28.7904222Z` → `12:17:32.4119044Z` |
| [**`32572683716`**](https://github.com/marcosmatalab/docbench-es/actions/runs/32572683716) | **`28186b9`** | **4,43 s** | **11 s** | **15 s** | `12:19:45.6204105Z` → `12:19:50.0508128Z` |
| [`32575381380`](https://github.com/marcosmatalab/docbench-es/actions/runs/32575381380) | `3a6b9d7` | 4,28 s | 14 s | 18 s | `13:18:23.8046256Z` → `13:18:28.0860583Z` |

**Mínimo 3,41 · mediana 3,95 · máximo 4,43 s · n=4.** La más lenta tarda **≈1,3×**
lo que la más rápida. La dispersión va como **razón entre extremos**, no como un
`±`: la mediana con n=4 es inestable —añadir esta cuarta corrida la movió de 3,62 a
3,95 s— y un `±` anclado a ella se movería con ella. **Léase el rango, no el
centro.**

- **Qué entra en la muestra, y hasta cuándo.** Las corridas de todo commit cuyo
  árbol de código sea idéntico al de `28186b9`. Los cuatro se diferencian sólo en
  markdown, y ningún `.md` entra en lo que mide la puerta. **Corte: 22 ago 2026.**
  El criterio es de inclusión, no de conveniencia: la muestra crece con cada commit
  de documentación, y una corrida que caiga fuera del rango se añade igual.
- **Fecha:** las cuatro el 2026-08-22 · **máquina:** runner estándar de GitHub,
  `ubuntu-latest`, 4 vCPU · **conclusión:** `success` en las cuatro.
- **Lo que ha cambiado desde `28186b9` fuera de markdown**, y por qué no afecta:
  `Makefile` —sólo el objetivo `clean`, que `make fast` no ejecuta— y `.gitignore`.
  Se comprueba con `git diff --name-only 28186b9 HEAD | grep -v '\.md$'`, que los
  nombra, y con `git diff 28186b9 HEAD -- Makefile`, que enseña que el objetivo
  `fast` es idéntico.
- **Reproducción** de las ventanas (las crudas están arriba porque los logs
  caducan) y de las columnas de job y run:
  ```bash
  for R in 32572385551 32572585111 32572683716 32575381380; do
    gh run view "$R" --repo marcosmatalab/docbench-es \
      --json createdAt,updatedAt,jobs \
      -q '"run \(.createdAt)->\(.updatedAt) job \(.jobs[0].startedAt)->\(.jobs[0].completedAt)"'
    JID=$(gh run view "$R" --repo marcosmatalab/docbench-es \
          --json jobs -q '.jobs[0].databaseId')
    gh api "repos/marcosmatalab/docbench-es/actions/jobs/$JID/logs" \
      | grep -E '##\[group\]Run make fast|\[100%\]'
  done
  ```
- La corrida comprueba además que el pin de Python se cumple: imprime
  `esperado=3.12 real=3.12`.

### En local · no sustituye al del runner

| Medida | Mediana | Rango observado (n=10) | Fecha |
|---|---|---|---|
| `make fast` en frío | **1742 ms** | 1715 – 1872 ms | 2026-08-22 |
| `make fast` en caliente | **723 ms** | 697 – 752 ms | 2026-08-22 |

En frío: `1750 1737 1752 1737 1747 1717 1715 1872 1732 1771`. En caliente:
`730 697 711 727 719 715 704 727 752 750`.

**Condición de máquina: en reposo**, `load average` 0,05. Se declara porque
importa: una tanda anterior tomada mientras corrían agentes de verificación en la
misma máquina dio una mediana 44 ms distinta. Ver [`docs/metrics.md`](docs/metrics.md).

- **Máquina:** AMD Ryzen 9 9950X3D, 8 vCPU asignadas a WSL2, 31 GB RAM ·
  Ubuntu 24.04.3 LTS sobre WSL2 (kernel 6.6.87.2) · Python 3.12.3 · uv 0.12.0.
  Medido dentro de WSL, en shell nativa.
- **Reproducción:**
  ```bash
  for i in $(seq 10); do
    make clean >/dev/null 2>&1; rm -rf .import_linter_cache
    s=$(date +%s%N); make fast >/dev/null 2>&1 || { echo "PUERTA EN ROJO"; break; }
    e=$(date +%s%N); echo "$(( (e - s) / 1000000 )) ms"
  done
  ```
  El `||` no es decoración: `make` para en el primer paso que falla, así que una
  puerta rota da un tiempo **menor**, no mayor. Sin comprobar el código de salida,
  el bucle publicaría ese número como si fuera bueno.
- Qué entra y qué no en «en frío», qué sobrevive aún, y por qué estas cifras no se
  comparan con las del runner: [`docs/metrics.md`](docs/metrics.md).
