# AURORA-R01 · Expediente RDL-PB-001 v0.1

Evaluación del 23 de noviembre de 2026. Candidato AURORA v1.4, «Market Context Indicator», admitido para caracterización técnica de un indicador descriptivo. Base `37a05cc82aa6b450230e1f235563ca1e1728b0dd`, candidato original `6d3e37bfd305b78984e0d6e60b6eab2172d2ae9f`. Ambos árboles contienen `codigo` con el blob `2f97468470318d471db30f2696986c7d05681705`. La fuente es la implementación Pine v6. El [Playbook](../program/RDL-PB-001_v0.1_original_propuesta.md) rige el proceso. Quedan pendientes una especificación canónica de producto y la confirmación independiente del comportamiento en TradingView.

## Preguntas y criterios previos (§§5–8, 19–20)

Protocolo R01-P1 v1. Primero se examina el código y se deducen predicados y cotas. Después se usa una cuadrícula pequeña y un oráculo local con casos OHLC deterministas. La validación externa del runtime queda restringida al smoke test E4. Sin semillas ni datos de mercado. Cada pregunta se refiere al mismo blob.

| Pregunta | Referencia y supuesto inicial | Resultado que cambia la decisión | Presupuesto y cierre |
|---|---|---|---|
| E1 · ¿Hay un estado común? | Tres vistas del original. Contrato de coherencia de la orden | Una discrepancia sin contrato obliga a definir el régimen antes de confiar en las vistas | Una tabla exhaustiva de bits, más fronteras y cobertura OHLC disponible. Cierre al contrastar las seis combinaciones lógicas |
| E2 · ¿Qué miden y cuándo existen las series? | Fórmulas del original, con el piso de `1e-10`. Semántica de producto abierta | Un valor inesperado, sustitución o caso degenerado obliga a definir dominio y tratamiento antes del uso descriptivo | Una derivación y seis familias de 100 barras, más longitudes límite e historia corta. Cierre con traza de disponibilidad por barra |
| E3 · ¿Qué añade el producto? | Comparación emparejada con φ y 1−Ψ en las barras comunes y con entradas directas | Separar empates o cambiar el orden permite formular una hipótesis estructural. Validar un filtro exige resultado externo | Tres pares mínimos y las mismas series E2. Cierre con igualdad, desacuerdo y atribución |
| E4 · ¿Se reproduce en Pine? | Motor TradingView y documentación de ejecución. Oráculo como referencia local | Compilación, trazas alineadas y prueba separada de barra abierta/cerrada habilitan un dictamen de runtime | Una comprobación de acceso, un gráfico y una recarga si hay acceso autorizado. Cierre instrumental explícito si falta acceso o traza |

Los ejes de dominio, prioridad, semántica y tiempo se revisan por separado. El motor de Pine podría diferir en tratamiento de faltantes, precisión, cálculos nativos y comparaciones cercanas al umbral. El análisis local conserva esas incertidumbres.

## R01-C1 · Contrato reconstruido del candidato (§5)

Entradas por barra: `close`, `high`, `low`, y `close[1]` para retorno y rango verdadero. El oráculo usa precios positivos finitos, velas consistentes y longitudes enteras positivas. En la fórmula del retorno se requiere un cociente positivo y utilizable. El original declara `input.int` sin `minval` para `L_phi=50`, `L_sigma=30` y `L_slope=20`. El grupo «Parameters» y el comentario «LOCKED» conviven con controles editables en la fuente. Se requiere TradingView para compilar y ejecutar el original. El código usa funciones nativas de Pine y el historial del gráfico, sin importaciones ni solicitudes externas en la fuente. El estado procede de rezagos, ventanas, las dos EMA y la tabla persistente. Los parámetros se mantienen fijos durante cada ejecución y las estimaciones cambian con la serie. La huella de cálculo depende del motor y la longitud del historial. Sin medición de tiempo o memoria de Pine en R01.

| Declaración en la fuente | Definición observable | Interpretación pendiente |
|---|---|---|
| `ret` | logaritmo natural de close / close previo | Política ante precios inválidos o datos faltantes |
| `φ (Structure)` | Recorte a [0,1] de 1 − abs(ret − EMA(ret, L_phi)) / max(SMA(abs(ret), L_phi), 1e−10) | Qué representa «estructura», incluida la asignación en reposo y a escalas ínfimas |
| `ΔV`, `CHOP` | Desviación estándar móvil de ret, diferencia absoluta entre desviaciones consecutivas, y 100 × log10(suma de TR / max(rango, 1e−10)) / log10(L_sigma). TR es el máximo de high−low y distancias absolutas al cierre previo. Rango es máximo de high menos mínimo de low. CHOP pasa a 50 si la fórmula queda en `na` | Contrato de normalización, límites del CHOP y significado de 50 como sustitución |
| `Ψ (Risk)` | Sigmoide de 0.5 × (zDeltaV + zChop). Cada z resta la media móvil y divide por max(desviación móvil, 1e−10) con L_sigma | Definición de «riesgo». El resultado no tiene calibración como probabilidad |
| `Ω (Operability)` | Producto de φ por el complemento 1−Ψ | Definición de «operabilidad», significado de cortes y decisión asociada a un filtro |
| `Trend Strength`, `Regime`, `Context` | Pendiente firmada por diferencia de EMA del precio (L_slope), normalizada con L_sigma. Tres predicados producen histograma, fondo y texto | Dirección de tendencia, estado base, solapamientos y precedencia común |

Se dibujan Ω, φ y Ψ, y un histograma de régimen en el panel del indicador. Ω es verde para valores superiores a 0.8, amarillo para superiores a 0.5 hasta 0.8 inclusive, y rojo hasta 0.5 para valores definidos. Las guías horizontales son 0.8, 0.5 y 0.3. La tabla muestra texto de régimen, Ω y φ en la última barra, con formato `#.##` para las dos cifras numéricas. El gráfico puede presentar un régimen antes de tener métricas compuestas. Las etiquetas y colores describen la fuente. El contrato de producto para su interpretación queda **AMBIGUO**.

## R01-E1 · Identidad del régimen (§§9–11)

Sea T = zSlope > 1 y zChop < −1, R = zChop > 1 y V = zDeltaV > 1. T y R son mutuamente excluyentes por zChop, así que 110 y 111 son imposibles por predicado. Para z finitos, todas las demás combinaciones son alcanzables como entradas de la lógica. Se probaron 125 entradas con z en {−2, −1, 0, 1, 2}. Orden de las entradas directas: (zSlope, zChop, zDeltaV).

| T/R/V | Entrada directa mínima | Histograma | Fondo | Panel |
|---|---|---:|---|---|
| 000 | (0, 0, 0) | 0 | Sin color | NEUTRAL |
| 001 | (0, 0, 2) | 2 | Rojo | VOLATILE |
| 010 | (0, 2, 0) | 0 | Gris | RANGE |
| 011 | (0, 2, 2) | 2 | Gris | RANGE |
| 100 | (2, −2, 0) | 1 | Verde | TREND |
| 101 | (2, −2, 2) | 1 | Verde | TREND |

Los predicados usan desigualdades estrictas. (1, −2, 0), (2, −1, 0) y (0, 1, 1) generan 000. Con (2, −2, 1) se obtiene 100 y con (0, 1, 2), 001. La cuadrícula confirmó los resultados esperados. El histograma prioriza T y luego V. El fondo y el panel priorizan T, luego R y luego V. R sin V comparte el código 0 con NEUTRAL. R con V genera un código 2 que también se usa para VOLATILE. La fuente carece de un contrato que autorice esa proyección. La coincidencia T/V sí resuelve TREND en las tres vistas.

Testigos **OBSERVADOS** en OHLC con el oráculo. «—» denota serie sin valor.

| Caso/barra | zSlope | zChop | zDeltaV | T/R/V | Histograma/fondo/panel |
|---|---:|---:|---:|---|---|
| flat/60 | 0 | 0 | 0 | 000 | 0 / sin color / NEUTRAL |
| jump/71 | −0.772402 | −3.513599 | 2.349769 | 001 | 2 / rojo / VOLATILE |
| osc/30 | 1.198740 | 5.385165 | — | 010 | 0 / gris / RANGE |
| range_vol/71 | −5.044306 | 5.385165 | 5.385165 | 011 | 2 / gris / RANGE |
| jump/74 | 2.697712 | −1.727444 | 0.906525 | 100 | 1 / verde / TREND |
| jump/70 | 5.360594 | −5.385165 | 5.385165 | 101 | 1 / verde / TREND |

La asimetría de dirección está en el predicado `zSlope > 1`. La muestra de deriva ascendente alcanzó T en la barra 30 y la descendente permaneció 000 en toda la traza. Una pendiente de precio negativa todavía puede tener zSlope positivo si es superior a su media móvil. «Tendencia» bidireccional queda pendiente de un requisito.

**Evidencia contraria suficiente** para la coherencia exigida a nivel de fuente. La prueba directa verifica la lógica reconstruida y los testigos verifican alcanzabilidad solo bajo el oráculo. Sigue pendiente la verificación en Pine.

## R01-E2 · Dominio y disponibilidad (§§9–11)

Con intermedios definidos y finitos, el denominador de φ es positivo y el error absoluto no es negativo. El recorte garantiza 0 ≤ φ ≤ 1. φ llega a 1 si el error es cero en aritmética exacta y a 0 si el error alcanza o supera el denominador. Para argumento finito, la sigmoide matemática da 0 < Ψ < 1. En coma flotante puede redondear a un extremo. En consecuencia 0 ≤ Ω ≤ min(φ, 1−Ψ) ≤ 1. En aritmética exacta, Ω es estrictamente inferior a 1 y es cero cuando φ es cero. Entradas finitas por sí solas no aseguran intermedios finitos, historia suficiente ni argumentos válidos de las funciones. Con una ventana poblacional de n valores finitos y desviación no nula, la magnitud del z del último valor está acotada por √(n−1), por la suma cero de los desvíos y Cauchy–Schwarz. El piso solo reduce dicha magnitud. Con desviación cero y media exacta, el z es 0.

El CHOP bruto requiere suma TR positiva y L_sigma > 1 para la expresión logarítmica. El piso permite un rango de precio cero si TR suma un valor positivo, por ejemplo por el cierre inmediatamente anterior a una ventana plana con un salto de precio. Es la suma TR cero, no el rango cero por sí solo, la que hace fallar el logaritmo en el caso plano continuo. El 50 de sustitución es un dato efectivo de la ventana de zChop y puede producir cambios de clasificación al salir del calentamiento. En `osc/30` el régimen cambia a RANGE en la primera barra con CHOP bruto mientras falta zDeltaV. La división por log10(1)=0 es degenerada con longitud 1. El oráculo representa esos resultados indefinidos con ausencia y aplica el 50. El comportamiento exacto del motor ante log10(0), división por cero y longitudes inválidas queda **NO EVALUADO**.

R01-P1 usa barras numeradas desde cero, ventanas completas contiguas, desviación poblacional, EMA iniciada con el primer dato disponible, aritmética binaria de Python y comparaciones directas. Ausencia se representa por `None` y se propaga por las fórmulas hasta tener su ventana, excepto el CHOP sustituido. En el oráculo una comparación con z ausente no activa un predicado. El tratamiento general de huecos en Pine requiere una prueba separada. Una barra se considera elegible para la métrica si sus intermedios requeridos existen. El CSV imprime también las barras no elegibles y señala cada sustitución.

| Familia | Primera TR sumada y vol | Primer delta | Primer CHOP bruto | Primer zChop / zSlope / zDeltaV | Primer φ / Ψ / Ω | Barras con sustitución |
|---|---|---|---|---|---|---|
| Predeterminadas, no planas | 30 | 31 | 30 | 29 / 30 / 60 | 50 / 60 / 60 | 0–29 |
| Plana | 30 | 31 | — | 29 / 30 / 60 | 50 / 60 / 60 | 0–99 |
| L_sigma=1 sobre oscilación | 1 | 2 | — | 0 / 1 / 2 | 50 / 2 / 50 | 0–99 |
| Historia corta, 29 barras | — | — | — | — / — / — | — / — / — | 0–28 |

El retorno, TR y la pendiente empiezan en la barra 1. Antes de las primeras barras indicadas, cada serie está ausente salvo el CHOP efectivo, que vale 50 en las barras marcadas. Rango de precio, CHOP efectivo y vistas de régimen quedan representados desde 0 en la réplica. Con CHOP bruto válido a partir de 30, la primera ventana de zChop libre de sustituciones es la de la barra 59. La ventana de zDeltaV queda completa en 60. Disponibilidad y estabilidad numérica son propiedades distintas. La EMA conserva memoria decreciente de su inicio, la oscilación sigue alternando y un cambio de volatilidad alimenta varias ventanas encadenadas. La barra 99 contiene la primera ventana de volatilidad con 30 retornos del nuevo tramo de `jump`. zDeltaV aún registra la transición en esa barra. La traza no identifica una barra de estabilización universal.

### Casos mínimos y resultados locales

En cada familia, barra 0 = (100,100,100,100). Para i ≥ 1, apertura = cierre previo, cierre = apertura × exp(rᵢ), máximo = max(apertura,cierre) × (1+s), mínimo = min(apertura,cierre) × (1−s), con s=0 salvo indicación. Son 100 barras por familia completa.

| Caso | Generador | Lectura esperada y observada |
|---|---|---|
| flat | rᵢ=0 | Sin rango ni TR positivos. Sustitución permanente, zChop=0 desde 29, φ=1 constante desde 50 y Ψ=Ω=0.5 constantes desde 60 |
| tiny | rᵢ=(−1)ⁱ × 1e−12 | Domina el piso de φ. En 60 y 99, φ≈0.989275 y 0.990394. La serie oscila alrededor de 0.99, Ψ≈0.5. Un error absoluto pequeño frente al piso basta para producir φ alto |
| up y down | rᵢ=±0.002, por separado | Error de retorno teóricamente cero en una deriva exacta. En 60 y 99 se observa φ≈1 y Ψ≈0.5 en ambas direcciones, con diferencias residuales de punto flotante. Esto no fija una clasificación direccional simétrica |
| osc | rᵢ=(−1)ⁱ × 0.01, s=0.001 | φ recorta a 0 en 60 y vale ≈0.039434 en 99. Ψ≈0.500586 en 60 y ≈0.5 en 99. La paridad sigue afectando a φ |
| jump | rᵢ=(−1)ⁱ × 0.001 hasta 69 y (−1)ⁱ × 0.03 desde 70, s=0.001 | En 70, zDeltaV y zChop se compensan y Ψ≈0.5 aunque V se activa. En 99 Ψ≈0.582372 y Ω=0, por φ=0 |
| range_vol | rᵢ=0.001 hasta 69 y (−1)ⁱ × 0.001 desde 70 | Testigo adicional para E1. En 71 confirma 011. En 99, φ=0, Ψ≈0.779693 y Ω=0 |
| sigma1 | osc con L_sigma=1 | Volatilidad y z de ventana unitaria degeneran a cero en el oráculo. Sustitución permanente, Ψ=0.5 desde 2 y Ω=φ/2 desde 50 |
| short | Primeras 29 barras de jump | Las tres métricas quedan siempre ausentes. La sustitución de CHOP ya se aplica en todas las barras |
| Longitudes no positivas | (0,30,20), (50,−1,20) y (50,30,0) | Rechazo explícito del oráculo. La fuente carece de mínimo explícito. Admisión en UI y fallo concreto en Pine pendientes |

El valor φ=1 de la secuencia plana queda deducido de error cero sobre el piso y observado en las barras elegibles. Decidir si el producto debe premiar, penalizar o marcar como indeterminado ese reposo requiere definir «estructura». La combinación de retornos casi nulos con φ alto muestra que φ y Ω tampoco son invariantes a reescalar retornos cuando interviene el piso.

## R01-E3 · Diferencial de Ω (§§9–11)

Con q=1−Ψ, Ω=φq mide coincidencia de dos puntuaciones altas. Con φ fijo y positivo, el orden de Ω sigue a q. Con q fijo y positivo, sigue a φ. Si ambas componentes conservan el orden, el producto también lo conserva débilmente. Para puntuaciones positivas en desacuerdo, Ω_A > Ω_B si φ_A/φ_B > q_B/q_A. Una componente cero anula la otra. Esa es una propiedad medible del cálculo.

| Par de entradas (φ, Ψ) A / B | Orden por φ | Orden por q | Ω A / B, esperado y verificado |
|---|---|---|---|
| (0.8, 0.25) / (0.8, 0.75) | A=B | A>B | 0.60 / 0.20. q rompe el empate |
| (0.9, 0.8) / (0.5, 0.2) | A>B | A<B | 0.18 / 0.40. q cambia el orden de φ |
| (0.9, 0.5) / (0.5, 0.2) | A>B | A<B | 0.45 / 0.40. φ cambia el orden de q |

Estos pares son entradas a la fórmula. La observabilidad conjunta desde OHLC se contrasta por separado. Para las seis familias E2 predeterminadas se compararon los 15 pares de familias en las mismas 40 barras elegibles (60–99), con diferencias absolutas de hasta 1e−7 tratadas como empates. Ese umbral agrupa el residuo visible en las derivas, del orden de 1e−9. El análisis no trata las 600 comparaciones como muestras independientes.

| Signo de A−B por (φ, q, Ω) | Cantidad |
|---|---:|
| (−, 0, −) | 80 |
| (0, −, −) | 5 |
| (0, −, 0) | 12 |
| (0, 0, 0) | 120 |
| (0, +, 0) | 8 |
| (+, −, +) | 59 |
| (+, 0, +) | 196 |
| (+, +, +) | 120 |

En los 59 desacuerdos de signos estrictos el producto siguió a φ. El contraejemplo algebraico de la tabla muestra que esto depende de las magnitudes y del conjunto evaluado. En la barra 60, flat y tiny tienen q≈0.5, pero el producto distingue Ω=0.5 de Ω≈0.494637 por φ. En la misma barra, osc y jump tienen φ=0, y el producto empata en cero aunque q difiere. En la barra 99, jump queda por debajo de osc por ambas componentes (0 frente a ≈0.039434 y q≈0.417628 frente a ≈0.5). En ese caso el producto conserva el orden y el cero lo determina φ. No hay evidencia aquí sobre selección de operaciones.

## R01-E4 · Contrato temporal y brecha instrumental (§§9–11)

La fuente usa OHLC de la barra actual y datos anteriores. No invoca datos de barras futuras y carece de un filtro explícito de confirmación. Por el modelo de ejecución documentado, en barras históricas el indicador se calcula con sus datos confirmados. En la barra abierta se vuelve a calcular cuando llegan actualizaciones, con rollback y persistencia del resultado final al cierre. High, low y close pueden variar intrabar, de modo que métricas, color, clasificación, histograma y tabla pueden cambiar. `barstate.islast` condiciona la actualización de la tabla a la última barra del gráfico, incluida la abierta. La confirmación en vivo y la reconstrucción histórica son verificaciones distintas. [Modelo de ejecución de Pine](https://www.tradingview.com/pine-script-docs/language/execution-model/)

La sonda HTTPS a TradingView devolvió HTTP 403 del proxy durante CONNECT. No se creó copia instrumental ni se transfirió el código a un servicio externo. Compilación del original, ejecución sobre barras cerradas, actualizaciones de barra abierta, casos inválidos y concordancia con Pine quedan **NO EVALUADOS**.

Para reabrir E4, compilar el blob original en Pine Editor con una sesión autorizada. Fijar símbolo, proveedor, sesión, temporalidad, tipo de gráfico, parámetros, precisión y barra inicial del historial. Usar una copia instrumental identificada por hash, con idénticos cálculos y solo salidas adicionales, para exponer TR, CHOP bruto y efectivo, normalizaciones y métricas. Exportar OHLC y trazas con tiempo y barra, incluidos intermedios durante el calentamiento. Usar la misma historia de inicialización para ambas EMA. Comparar por barra máscaras de ausencia, sustituciones y discretos de forma exacta. Comparar cada serie continua con una tolerancia explícita basada en su precisión de exportación y escala; investigar por separado discrepancias próximas a los umbrales. Registrar varias actualizaciones de una barra abierta sin reconstruirlas desde OHLC final. Capturar su cierre y recargar el gráfico con el mismo historial para contrastar la fila confirmada. Repetir el smoke test con longitud unitaria y con longitudes no positivas si la UI las admite.

## Registro de ejecución y control de calidad (§§9, 14, 19–20)

R01-P1 / ejecuciones locales R01-L1 y R01-L2. Codex Cloud Linux, Python 3.12.14, biblioteca estándar, sin servicios, datos externos ni azar. Parámetros, datos, salidas esperadas y resultados se vinculan en E1–E4. El [oráculo](aurora_r01_oracle.py) materializa las trazas completas. Los ceros se conservan y los campos vacíos representan ausencia. Las aserciones usan 1e−12 de tolerancia absoluta y 1e−9 relativa para valores de referencia simples del oráculo. Las identidades discretas son exactas. Esas tolerancias no acreditan concordancia con Pine.

Desde el checkout, ejecutar:

```bash
git rev-parse 37a05cc82aa6b450230e1f235563ca1e1728b0dd:codigo \
  6d3e37bfd305b78984e0d6e60b6eab2172d2ae9f:codigo
python3 docs/research/aurora_r01_oracle.py /tmp/aurora-r01.csv
python3 docs/research/aurora_r01_oracle.py /tmp/aurora-r01-repeat.csv
cmp /tmp/aurora-r01.csv /tmp/aurora-r01-repeat.csv
sha256sum /tmp/aurora-r01.csv
git diff --check 37a05cc82aa6b450230e1f235563ca1e1728b0dd HEAD
git diff --exit-code 37a05cc82aa6b450230e1f235563ca1e1728b0dd HEAD -- codigo docs/program
git ls-remote origin refs/heads/research/aurora-r01
```

Resultados locales. Identidad de blobs verificada, aserciones pasadas y 829 filas de datos repetidas byte a byte en este entorno. SHA-256 del CSV `4c9ecfdfe6b37a602e91ffcba691cfa0108c88a28d700f7fcef0447b330dd8e7`. La condición de cierre local se satisface. El añadido de un testigo dirigido para 011 amplió E1 en una serie de 100 barras después de la primera ejecución, dejando intactos sus criterios. El activo reutilizable es el oráculo con sus generadores y trazas bajo demanda. La réplica comparte método y entorno. La independencia instrumental y las reproducciones experimental y de trayectoria en Pine siguen pendientes. El nivel de confianza es alto para la deducción de los predicados y el álgebra, y limitado a las convenciones declaradas para las trayectorias locales.

## Decisiones por uso (§§13–14, 19–20 y 23)

| Decisión | Dictamen y evidencia | Evidencia mínima de reapertura |
|---|---|---|
| R01-D1 · Describir contexto (E2, E4 · G1/G3) | **Reproducible como cálculo local condicionado.** Repetibilidad y trayectoria observadas para las series y convenciones R01. **Suspender por limitación instrumental** el dictamen de reproducibilidad del indicador Pine. La sustitución de CHOP y el tratamiento de reposo, longitudes y calentamiento requieren definición para un uso descriptivo estable | Compilación más traza alineada E4 y contrato de dominio que declare reposo, faltantes, mínimos y momento de disponibilidad |
| R01-D2 · Coherencia entre salidas (E1 · G3) | **No cumple el criterio de coherencia de esta auditoría.** Contradicción deducida y verificada en la lógica, con testigos OHLC locales. **Ampliar investigación** para escoger el contrato de estados y precedencias antes de autorizar una corrección | Una tabla canónica de las seis combinaciones, incluso si se decide proyectar estados en alguna vista. Después, comprobar la implementación frente a esa tabla |
| R01-D3 · Formular una prueba futura de filtro (E2–E3 · G2) | **Continuar con el diseño de la prueba.** Ω mide una conjunción multiplicativa de ajuste del retorno a su EMA y puntuación complementaria de Ψ. Los contraejemplos y empates demuestran cuándo cambia el orden o suprime información. El significado externo de «operabilidad» queda pendiente | Definir un resultado objetivo, población y horizonte, barras elegibles, umbral y criterio de éxito. Comparar Ω, φ y 1−Ψ en las mismas barras con datos fuera de muestra y parámetros fijados |

R01 cierra la pregunta de coherencia de la fuente y delimita la propiedad matemática de Ω. La siguiente inversión que respaldan estos hallazgos es aclarar el contrato del régimen y la semántica de las métricas, y completar E4 cuando exista acceso. Esta revisión no autoriza cambios en el indicador. La capacidad predictiva, la rentabilidad y la utilidad en decisiones de mercado quedan **NO EVALUADAS**. Se conserva el expediente como revisión técnica con obligaciones pendientes de producto y runtime.
