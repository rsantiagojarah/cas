# SKILL — E.030 Diseño Sismorresistente (Perú)  
## Versión para Codex basada en la nueva norma adjunta
**Nombre sugerido del skill:** `skill_e030_diseno_sismorresistente_peru.md`

> **Advertencia de fuente:** el archivo cargado por el usuario se llama **“Norma E.030 Diseño sismorresistente_2026.pdf”**, pero en su portada e índice internos figura como **“NORMA TÉCNICA E.030 DISEÑO SISMORRESISTENTE 2025”**.  
> Para este skill, **se debe tomar como fuente normativa principal ese PDF adjunto más reciente**, porque es el documento que el usuario ha denominado como “nueva norma 2026”.  
> Además, existe un archivo de texto pegado con un ejemplo de análisis sísmico en formato reporte. **Ese texto NO es la fuente normativa**: solo debe usarse como **referencia de estructura de salida**.

---

## 1. Propósito del skill

Este skill sirve para que Codex:

1. **lea y use como fuente principal la nueva E.030 adjunta**;
2. **ignore valores viejos** de versiones anteriores cuando contradigan la nueva norma;
3. **genere cálculos, tablas, reportes o scripts** de análisis sísmico E.030;
4. **redacte memorias o resúmenes técnicos** con formato claro;
5. **produzca salidas estilo reporte** similares al archivo de texto adjunto, pero **actualizadas a la nueva norma**;
6. **detecte incoherencias normativas**, datos faltantes y restricciones de aplicabilidad;
7. **no invente artículos, tablas ni fórmulas** que no estén verificadas en la fuente adjunta.

---

## 2. Jerarquía de fuentes que Codex debe respetar

Codex debe seguir este orden de prioridad:

### Fuente 1 — Norma principal
Archivo adjunto: **`Norma E.030 Diseño sismorresistente_2026.pdf`**  
Uso: **fuente normativa principal** para artículos, tablas, factores, restricciones, fórmulas y criterios.

### Fuente 2 — Texto pegado por el usuario
Archivo adjunto: **`Pasted text.txt`**  
Uso: **solo como plantilla de estructura de salida** o ejemplo de reporte paso a paso.  
**Nunca** usar sus valores normativos si contradicen la nueva norma.

### Fuente 3 — Versiones antiguas adjuntas
Otros PDFs adjuntos de E.030 (edición 2020 / rectificaciones 2019 / etc.).  
Uso: solo para **comparaciones históricas** o para identificar qué cambió.  
**No** deben prevalecer sobre la norma nueva.

---

## 3. Comportamiento obligatorio de Codex

Codex debe actuar como un **ingeniero estructural asistente especializado en E.030** y seguir estas reglas:

### 3.1. No inventar
- No inventar artículos.
- No inventar tablas.
- No inventar valores de factores.
- No inventar fórmulas faltantes.
- No completar vacíos “por costumbre” si la nueva norma no está verificada en la fuente.

### 3.2. Si hay conflicto entre archivos
- Priorizar la **nueva E.030 adjunta**.
- Tratar el archivo de texto antiguo como ejemplo de formato, no como norma.

### 3.3. Si falta un dato de entrada
Codex debe:
1. identificar el dato faltante;
2. explicar qué cálculo no puede cerrarse sin ese dato;
3. proponer una salida parcial;
4. marcarlo explícitamente como **pendiente**;
5. no asumir valores ocultos si son normativamente sensibles.

### 3.4. Si el usuario pide script o automatización
Codex debe:
- separar claramente:
  - **entrada de datos**
  - **lógica normativa**
  - **validaciones**
  - **salida de resultados**
- dejar el código listo para auditar;
- incluir comentarios normativos;
- mantener trazabilidad de cada factor utilizado.

### 3.5. Si el usuario pide memoria o reporte
Codex debe:
- presentar el cálculo en pasos;
- incluir tablas normativas relevantes;
- mostrar fórmulas;
- indicar criterios de control;
- cerrar con observaciones y validaciones normativas.

---

## 4. Alcance técnico del skill

Este skill cubre, como mínimo:

1. zonificación sísmica;
2. clasificación de perfiles de suelo;
3. parámetros de sitio `S`, `TP`, `TL`;
4. construcción del factor `C`;
5. categoría de edificación y factor `U`;
6. sistema estructural permitido;
7. coeficiente `R0`;
8. irregularidades `Ia`, `Ip`;
9. coeficiente `R = R0 * Ia * Ip`;
10. estimación del peso sísmico `P`;
11. análisis estático;
12. análisis dinámico modal espectral;
13. verificaciones mínimas de cortante;
14. desplazamientos laterales;
15. derivas admisibles;
16. separación sísmica;
17. redundancia estructural;
18. advertencias de aplicabilidad;
19. generación de plantilla de reporte estilo “ANÁLISIS SÍSMICO E.030 – SENTIDO X / SENTIDO Y”.

---

## 5. Datos de entrada esperados

Codex debe solicitar o leer, según el caso, los siguientes datos:

### 5.1. Datos del proyecto
- nombre del proyecto;
- ubicación: departamento / provincia / distrito;
- zona sísmica si ya está determinada;
- categoría de edificación;
- número de pisos;
- altura total `hn`;
- altura de entrepisos;
- material estructural;
- sistema estructural por dirección;
- regularidad o irregularidades;
- si hay aislamiento sísmico o disipación de energía;
- si hay sistema de transferencia;
- tipo de análisis requerido: estático, modal espectral o verificación tiempo-historia.

### 5.2. Datos geotécnicos
- `Vs` promedio en 30 m;
- `N60` promedio ponderado para estratos granulares;
- `Su` promedio ponderado para estratos cohesivos;
- tipo de cimentación;
- si existen pilotes;
- para categorías A y B en zona 4: `Ts` del sitio por método `H/V`, si aplica;
- identificación de suelo `S5`, licuación, colapso, orgánicos, amplificación local, etc.

### 5.3. Datos del modelo estructural
- períodos modales;
- masas modales participativas;
- peso por nivel;
- desplazamientos por nivel;
- derivas por nivel;
- cortantes por nivel;
- cortante basal estático;
- cortante basal dinámico;
- dimensiones en planta por nivel;
- excentricidades;
- participación de muros / pórticos;
- resultados por dirección X e Y;
- para diafragma rígido: desplazamientos en extremos del entrepiso para evaluar torsión.

### 5.4. Si se trabaja con ETABS / SAP / Robot / similares
Codex debe aceptar tablas exportadas como:
- Modal Periods and Frequencies
- Modal Participating Mass Ratios
- Story Weights
- Story Drifts
- Story Shears
- Base Reactions
- Joint Displacements
- Diaphragm CM Displacements
- Torsional Irregularity data
- Forces in vertical elements

---

## 6. Reglas normativas verificadas en la nueva norma adjunta

> **IMPORTANTE:** todo lo siguiente debe tratarse como parte normativa base del skill.

---

## 7. Tabla de factores de zona `Z`

### Tabla 1 — Factores de zona “Z”

| Zona | Z |
|---|---:|
| 4 | 0.45 |
| 3 | 0.35 |
| 2 | 0.25 |
| 1 | 0.10 |

### Regla
- `Z` representa la aceleración máxima horizontal en suelo rígido con probabilidad de 10% de excedencia en 50 años.
- Se expresa como fracción de `g`.

---

## 8. Clasificación de perfiles de suelo

### Tabla 2 — Tipos de perfiles de suelo (resumen operativo)

| Perfil | Nombre | Criterio general |
|---|---|---|
| S0 | Roca | `Vs >= 800 m/s` |
| S1 | Suelos muy rígidos | `550 <= Vs < 800 m/s` |
| S2 | Suelos rígidos | `350 <= Vs < 550 m/s` |
| S3 | Suelos intermedios | `200 <= Vs < 350 m/s` |
| S4 | Suelos blandos | `Vs < 200 m/s` |
| S5 | Suelos excepcionales | licuables, colapsables, orgánicos, turba, finos saturados, amplificación local, topografía o geología desfavorable, etc. |

### Tabla 3 — Clasificación resumida por parámetros

| Perfil | `Vs` | `N60` | `Su` |
|---|---|---|---|
| S0 | `> 800 m/s` | — | — |
| S1 | `550 a <800 m/s` | `> 50` | — |
| S2 | `350 a <550 m/s` | `30 a 50` | `> 100 kPa` |
| S3 | `200 a <350 m/s` | `15 a 30` | `50 a 100 kPa` |
| S4 | `< 200 m/s` | `< 15` | `< 50 kPa` |

### Reglas obligatorias
1. La clasificación se hace en los **30 m superiores del perfil**, medidos desde el fondo de cimentación.
2. Para suelos granulares se puede usar `N60`.
3. Para suelos cohesivos se puede usar `Su`.
4. Para suelos heterogéneos se toma el **perfil más desfavorable**.
5. Si el suelo es `S5`, **no usar directamente la tabla estándar**: se requiere tratamiento especial.
6. Para estructuras con pilotes, el perfil corresponde a los **30 m por debajo del extremo superior de los pilotes**.

### Fórmulas de promedios ponderados
#### Velocidad promedio de ondas de corte
\[
\bar{V_s} = \frac{\sum d_i}{\sum (d_i / V_{si})}
\]

#### Promedio ponderado `N60`
\[
\bar{N}_{60} = \frac{\sum d_i}{\sum (d_i / N_{60i})}
\]

#### Promedio ponderado `Su`
\[
\bar{S_u} = \frac{\sum d_i}{\sum (d_i / S_{ui})}
\]

---

## 9. Regla especial para categorías A y B en zona 4

Si la edificación es **categoría A o B**, está en **zona 4** y el suelo resultó `S1`, `S2`, `S3` o `S4`, entonces:

1. debe determinarse el **periodo predominante del terreno `Ts`** a partir de mediciones de vibraciones ambientales y relación espectral `H/V`;
2. se debe verificar si:

\[
T_s < 0.65 \, T_P
\]

3. si `Ts > 0.65 Tp`, debe adoptarse el **perfil siguiente más desfavorable** (hasta el límite superior permitido) o realizar un **estudio de sitio específico**.

### Reglas mínimas para `H/V`
- mínimo 3 mediciones;
- al menos 30 min cada una;
- interpretación con criterio conservador.

---

## 10. Parámetros de sitio `S`, `TP`, `TL`

### Tabla 4 — Factor de suelo `S`

| Zona / Suelo | S0 | S1 | S2 | S3 | S4 |
|---|---:|---:|---:|---:|---:|
| Z4 | 0.80 | 1.00 | 1.10 | 1.20 | **Requiere análisis de respuesta de sitio** |
| Z3 | 0.80 | 1.00 | 1.15 | 1.20 | 1.30 |
| Z2 | 0.80 | 1.00 | 1.30 | 1.40 | 1.70 |
| Z1 | 0.80 | 1.00 | 1.30 | 1.60 | 2.40 |

### Tabla 5 — Períodos `TP` y `TL`

| Perfil | `TP (s)` | `TL (s)` |
|---|---:|---:|
| S0 | 0.3 | 3.0 |
| S1 | 0.4 | 3.0 |
| S2 | 0.4 – 0.6 | 3.0 |
| S3 | 0.6 – 0.9 | 2.5 |
| S4 | 1.2 | 2.0 |

### Reglas obligatorias
1. Para `S2` y `S3`, `TP` debe interpolarse linealmente en función de `Vs`.
2. Si no se dispone de `Vs`:
   - usar `TP = 0.6` para `S2`;
   - usar `TP = 0.9` para `S3`.
3. Para `Z4 + S4`, no se debe asignar `S` automáticamente desde una tabla estándar: se requiere **análisis de respuesta de sitio**.

---

## 11. Factor de amplificación sísmica `C`

### Tabla 6 — Determinación de `C`

Para período fundamental `T`:

#### Tramo 1
Si:
\[
T < 0.2 T_P
\]

entonces:
\[
C = 1 + 7.5\left(\frac{T}{T_P}\right)
\]

#### Tramo 2
Si:
\[
0.2T_P \le T \le T_P
\]

entonces:
\[
C = 2.5
\]

#### Tramo 3
Si:
\[
T_P < T < T_L
\]

entonces:
\[
C = 2.5\left(\frac{T_P}{T}\right)
\]

#### Tramo 4
Si:
\[
T > T_L
\]

entonces:
\[
C = 2.5\left(\frac{T_P T_L}{T^2}\right)
\]

### Regla especial para análisis estático
Para calcular la **fuerza cortante basal del análisis estático**, usar:

\[
C = 2.5
\quad \text{en todo el rango} \quad 0 \le T \le T_P
\]

---

## 12. Categoría de edificación y factor de uso `U`

### Tabla 7 — Categoría y factor `U`

| Categoría | Descripción resumida | Factor U |
|---|---|---:|
| A | Edificaciones esenciales | 1.5 |
| B | Edificaciones importantes | 1.3 |
| C | Edificaciones comunes | 1.0 |
| D | Edificaciones temporales | **ver nota** |

### Reglas obligatorias
1. En edificaciones de usos combinados, usar el **mayor `U`** si ese uso ocupa más del 15% del área total sin contar sótanos.
2. Para **A1**:
   - nuevas edificaciones en zonas 4 y 3 deben tener **aislamiento sísmico**;
   - en ese caso usar `U = 1`.
3. En zonas 1 y 2, la entidad responsable define si A1 usa o no aislamiento; si no lo usa, `U` debe ser como mínimo `1.5`.

### Nota importante sobre categoría D
En el extracto visible de la nueva tabla, la fila de categoría D no muestra de forma legible un valor numérico completo.  
**Regla del skill:** si el usuario pide cálculo con categoría D, Codex debe:
- buscar el valor exacto en el PDF fuente;
- si no puede verificarlo de forma explícita, **no inventarlo**;
- marcarlo como **dato normativo pendiente de confirmación**.

---

## 13. Sistemas estructurales

### Tabla 8 — Sistemas estructurales (resumen operativo)

#### Concreto armado
- **Pórticos**: al menos 80% del cortante basal actúa sobre columnas de pórticos.
- **Muros estructurales**: los muros toman al menos 70% del cortante basal.
- **Dual**: muros toman más de 20% y menos de 70% del cortante basal.
- **EMDL**: muros de ductilidad limitada; máximo 8 pisos.

#### Acero
- `SMF`
- `IMF`
- `OMF`
- `SCBF`
- `OCBF`
- `EBF`

#### Otros
- albañilería armada o confinada;
- madera;
- tierra.

---

## 14. Sistemas permitidos por categoría y zona

### Tabla 9 — Categoría y sistema estructural de las edificaciones

| Categoría | Zona | Sistema permitido |
|---|---|---|
| A1 | 4 y 3 | Aislamiento sísmico con cualquier sistema estructural |
| A1 | 2 y 1 | Acero SCBF y EBF; Concreto dual o muros; Albañilería armada o confinada |
| A2 | 4, 3 y 2 | Acero SCBF y EBF; Concreto dual o muros; Albañilería armada o confinada |
| A2 | 1 | Cualquier sistema |
| B | 4, 3 y 2 | Acero SMF, IMF, SCBF, OCBF y EBF; Concreto pórticos, dual o muros; Albañilería; Madera |
| B | 1 | Cualquier sistema |
| C | 4, 3, 2 y 1 | Cualquier sistema |

### Reglas
- Para coberturas livianas se permite cualquier sistema.
- Para pequeñas construcciones rurales de la categoría indicada por la norma, se admiten materiales tradicionales siguiendo sus normas correspondientes.

---

## 15. Coeficiente básico de reducción `R0`

### Tabla 10 — Sistemas estructurales y `R0`

| Sistema estructural | `R0` |
|---|---:|
| Acero SMF | 8 |
| Acero IMF | 5 |
| Acero OMF | 4 |
| Acero SCBF | 7 |
| Acero OCBF | 4 |
| Acero EBF | 8 |
| Concreto — Pórticos | 8 |
| Concreto — Dual | 7 |
| Concreto — Muros estructurales | 6 |
| Concreto — Muros de ductilidad limitada | 3.5 |
| Albañilería armada o confinada | 3 |
| Madera | 7 *(para diseño por esfuerzos admisibles)* |

### Reglas
1. Si en una misma dirección hay más de un sistema estructural, usar el **menor `R0`**.
2. Estos coeficientes no aplican a estructuras tipo péndulo invertido.
3. No se permiten construcciones de tierra en suelos `S4` y `S5`.

---

## 16. Regularidad e irregularidades

### Regla base
- Si la estructura no presenta ninguna irregularidad de las tablas respectivas, entonces:
  - `Ia = 1.0`
  - `Ip = 1.0`
  - la estructura es **regular**
- Si presenta una o más irregularidades:
  - la estructura es **irregular**
  - `Ia` e `Ip` se toman como el **menor valor aplicable**

---

## 17. Irregularidades en altura — `Ia`

### Tabla 11 — Irregularidades estructurales en altura

| Irregularidad | `Ia` |
|---|---:|
| Piso blando / piso débil | 0.75 |
| Irregularidad extrema de rigidez / resistencia | 0.50 |
| Irregularidad de masa o peso | 0.90 |
| Irregularidad geométrica vertical | 0.90 |
| Discontinuidad en sistemas resistentes | 0.80 |
| Discontinuidad extrema de sistemas resistentes | 0.60 |

### Definiciones operativas mínimas
- **Piso blando**: rigidez lateral de un entrepiso < 70% de la del entrepiso superior o < 80% del promedio de los 3 superiores.
- **Piso débil**: resistencia cortante del entrepiso < 80% de la del superior.
- **Irregularidad extrema de rigidez**: < 60% del superior o < 70% del promedio de los 3 superiores.
- **Irregularidad extrema de resistencia**: < 65% de la resistencia del superior.
- **Irregularidad de masa**: peso de un piso > 1.5 veces el de un piso adyacente.
- **Discontinuidad en sistemas resistentes**: cambio de orientación o desplazamiento del eje > 25% de la dimensión del elemento cuando ese elemento resiste > 10% del cortante.
- **Discontinuidad extrema**: cuando esos elementos discontinuos superan 25% del cortante total.

---

## 18. Irregularidades en planta — `Ip`

### Tabla 12 — Irregularidades estructurales en planta

| Irregularidad | `Ip` |
|---|---:|
| Irregularidad torsional | 0.75 |
| Irregularidad torsional extrema | 0.60 |
| Esquinas entrantes | 0.90 |
| Discontinuidad del diafragma | 0.85 |
| Sistemas no paralelos | 0.90 |

### Definiciones operativas mínimas
#### Torsional
Existe cuando:
\[
\Delta_{max} > 1.3 \, \Delta_{prom}
\]

y además el máximo desplazamiento relativo del entrepiso supera 50% del desplazamiento permisible.

#### Torsional extrema
Existe cuando:
\[
\Delta_{max} > 1.5 \, \Delta_{prom}
\]

y además el máximo desplazamiento relativo del entrepiso supera 50% del desplazamiento permisible.

#### Esquinas entrantes
Cuando las dimensiones entrantes en ambas direcciones exceden 20% de la dimensión total correspondiente.

#### Discontinuidad del diafragma
- aberturas > 50% del área bruta del diafragma; o
- área neta resistente de una sección transversal < 50% del área bruta equivalente.

#### Sistemas no paralelos
Cuando los elementos resistentes no son paralelos en una dirección de análisis, salvo las excepciones explícitas de la norma.

---

## 19. Restricciones a la irregularidad

### Tabla 13 — Restricciones por categoría y zona

| Categoría | Zona | Restricción |
|---|---|---|
| A1 y A2 | 4, 3 y 2 | No se permiten irregularidades |
| A1 y A2 | 1 | No se permiten irregularidades extremas |
| B | 4, 3 y 2 | No se permiten irregularidades extremas |
| B | 1 | Sin restricciones |
| C | 4 y 3 | No se permiten irregularidades extremas |
| C | 2 | No se permiten irregularidades extremas, excepto edificios de hasta 2 pisos u 8 m de altura total |
| C | 1 | Sin restricciones |

### Restricción adicional
En zonas 4, 3 y 2 no se permiten estructuras con **sistemas de transferencia** donde más del 25% de las cargas de gravedad o sísmicas en cualquier nivel sean soportadas por elementos verticales no continuos hasta cimentación, salvo el último entrepiso.

---

## 20. Coeficiente de reducción `R`

### Fórmula
\[
R = R_0 \cdot I_a \cdot I_p
\]

### Reglas
- usar el `R0` del sistema estructural en la dirección analizada;
- usar el menor `Ia` entre ambas direcciones cuando la norma así lo exige;
- usar el menor `Ip` entre ambas direcciones cuando la norma así lo exige;
- no reportar `R` sin mostrar cómo se obtuvo.

---

## 21. Reglas generales para el análisis estructural

### 21.1. Direcciones de análisis
- estructuras regulares: puede analizarse cada dirección principal por separado;
- estructuras irregulares: analizar con **100% en una dirección + 30% en la perpendicular**;
- sistemas no paralelos: considerar también las acciones sísmicas en sus ejes propios.

### 21.2. Excentricidad accidental
- solo debe considerarse en la dirección perpendicular a la del 100% de la acción.

### 21.3. Fuerzas sísmicas verticales
Deben considerarse en:
- elementos verticales;
- elementos horizontales de gran luz;
- elementos postensados o pretensados;
- voladizos o salientes.

### 21.4. Tiempo-historia
- puede usarse con fines de verificación;
- no reemplaza obligatoriamente al análisis estático o modal espectral como procedimiento base.

---

## 22. Diseño y verificación por esfuerzos admisibles

Si el usuario trabaja por **esfuerzos admisibles**:

\[
F_{sismo,adm} = 0.8 \, F_{sismo,E030}
\]

Codex debe:
- indicarlo explícitamente;
- no mezclar resultados de resistencia última con esfuerzos admisibles sin avisarlo.

---

## 23. Modelado estructural

Codex debe respetar estas reglas:

1. modelar masas y rigideces de forma consistente;
2. en concreto armado y albañilería, analizar con **inercias brutas**, ignorando fisuración y refuerzo;
3. usar diafragma rígido solo si se justifica;
4. si no hay rigidez suficiente del diafragma, considerar su flexibilidad;
5. incluir tabiquería no aislada adecuadamente;
6. verificar el sistema con y sin tabiquería cuando corresponda;
7. en estructuras dominadas por muros, considerar interacción entre muros en `H`, `T`, `L`;
8. no incluir rigidez fuera del plano de las losas para el modelo global;
9. solo modelar alas de losa como T/L cuando su confinamiento y detallado sean adecuados.

---

## 24. Peso sísmico `P`

### Regla
El peso sísmico es la carga permanente total más una fracción de carga viva:

| Caso | Fracción de carga viva |
|---|---:|
| Categorías A y B | 50% |
| Categoría C | 25% |
| Depósitos | 80% del máximo almacenado |
| Azoteas y techos | 25% |
| Tanques, silos y similares | 100% del contenido |

---

## 25. Procedimientos de análisis permitidos

### Permitidos
- análisis estático o fuerzas estáticas equivalentes;
- análisis dinámico modal espectral.

### Tiempo-historia
- solo como verificación complementaria.

---

## 26. Aplicabilidad del análisis estático

Codex debe verificar:

1. **Zona 1**:
   - pueden analizarse estructuras regulares o irregulares.

2. **Zonas 2, 3 y 4**:
   - estructuras regulares de hasta 30 m;
   - estructuras de muros portantes de concreto armado y albañilería armada o confinada de hasta 15 m, aun si son irregulares.

3. Si la estructura **no cumple** con esas condiciones:
   - **no** usar análisis estático como procedimiento base;
   - pasar a **análisis dinámico modal espectral**.

4. Si la estructura es irregular y aun así puede analizarse con método estático por norma:
   - aplicar **100% + 30%**;
   - sumar valores absolutos según corresponda.

---

## 27. Fuerza cortante en la base — análisis estático

### Fórmula principal
\[
V = \frac{Z \cdot U \cdot C \cdot S}{R}\cdot P
\]

### Regla adicional
Si:
\[
T < T_P
\]
usar:
\[
C = 2.5
\]

### Cota mínima
\[
\frac{C}{R} \ge 0.11
\]

### Instrucción obligatoria para Codex
Siempre reportar:
- `Z`
- `U`
- `S`
- `C`
- `R`
- `P`
- `V`

y mostrar el reemplazo numérico.

---

## 28. Distribución en altura de fuerzas sísmicas

**Regla del skill:**  
La distribución en altura debe ejecutarse con la **expresión exacta del Artículo 35** de la norma fuente.

### Instrucción obligatoria
Si el usuario pide:
- cálculo manual detallado de `Fi` por nivel;
- script automatizado de distribución;
- memoria completa nivel por nivel;

entonces Codex debe:
1. leer el **Artículo 35 completo del PDF fuente**;
2. implementar la fórmula exacta;
3. no reemplazarla por una versión “recordada” o supuesta.

### Comportamiento seguro
Si Codex no tiene la fórmula textual completa disponible en el contexto:
- no inventarla;
- indicar: **“pendiente de extracción exacta del Artículo 35 del PDF fuente”**.

---

## 29. Período fundamental `T`

**Regla del skill:**  
El período puede provenir del modelo estructural o calcularse con el **Artículo 36**.

### Instrucción obligatoria
Si el usuario pide script o memoria que calcule `T` manualmente, Codex debe:
1. usar la expresión exacta del **Artículo 36** del PDF;
2. si no está íntegramente visible en el contexto, extraerla primero del PDF;
3. no inventar coeficientes por memoria si no están verificados en el archivo fuente actual.

### Sí se permite
- usar el período del software estructural cuando el usuario lo proporcione;
- usar períodos modales exportados por ETABS/SAP;
- identificar el período predominante por dirección.

---

## 30. Excentricidad accidental

### Regla base
Para cada dirección de análisis:
\[
M_{ti} = \pm F_i \cdot e_i
\]

donde la excentricidad accidental en el nivel `i` es:

\[
e_i = 0.05 \times \text{dimensión perpendicular del edificio}
\]

Codex debe aplicar esto cuando corresponda a estructuras con diafragma rígido.

---

## 31. Análisis dinámico modal espectral

### Modos
- considerar modos hasta que la suma de masas efectivas sea al menos **90%** de la masa total en cada dirección;
- considerar al menos los **3 primeros modos predominantes** en la dirección analizada.

### Espectro de pseudoaceleraciones
\[
S_a = \frac{Z \cdot U \cdot C \cdot S}{R}\cdot g
\]

### Dirección vertical
Puede usarse un espectro vertical igual a:

\[
\frac{2}{3}
\]
del espectro horizontal empleado.

---

## 32. Combinación modal

Codex puede usar:

### Método 1 — Combinación cuadrática completa (CQC)
Usar la formulación del artículo respectivo con `β = 0.05`.

### Método 2 — Alternativa permitida por la norma
\[
r = 0.25\sum |r_i| + 0.75\sqrt{\sum r_i^2}
\]

### Regla
Siempre indicar cuál criterio se usó.

---

## 33. Combinación direccional

La respuesta máxima esperada por acción simultánea de:
- 100% en una dirección;
- 30% en la perpendicular;

se obtiene por combinación según la norma.

### Instrucción para Codex
- si el usuario entrega resultados separados por X e Y, hacer la combinación direccional explícita;
- no asumir independencia total en estructuras irregulares.

---

## 34. Cortante dinámico mínimo

Para cada dirección:

- estructuras regulares:
  \[
  V_{din} \ge 0.80 \, V_{est}
  \]

- estructuras irregulares:
  \[
  V_{din} \ge 0.90 \, V_{est}
  \]

### Regla de escalamiento
Si el cortante dinámico no cumple:
- escalar proporcionalmente todos los resultados obtenidos;
- **excepto los desplazamientos**.

---

## 35. Desplazamientos laterales

### Estructuras regulares
\[
\Delta = 0.75R \cdot \Delta_{elástica}
\]

### Estructuras irregulares
\[
\Delta = 0.85R \cdot \Delta_{elástica}
\]

### Regla
Para calcular desplazamientos laterales:
- **no** considerar el mínimo `C/R`;
- **no** considerar el escalamiento por cortante mínimo para desplazamientos.

---

## 36. Derivas admisibles

### Tabla 14 — Límites de distorsión de entrepiso

| Material predominante | Límite |
|---|---:|
| Concreto armado | 0.007 |
| Acero | 0.010 |
| Albañilería | 0.005 |
| Madera | 0.010 |
| Concreto armado con muros de ductilidad limitada | 0.004 |

### Regla importante
Esta es una diferencia relevante respecto a versiones anteriores:
- **EMDL ahora controla con 0.004**, no con 0.005.

### Nota
En uso industrial, el proyectista puede definir el límite, pero nunca mayor que el doble de estos valores.

---

## 37. Separación entre edificios

### Fórmula mínima
\[
s = 0.02 \cdot Z \cdot S \cdot h \ge 0.03 \, m
\]

### Reglas
1. además:
   \[
   s \ge \frac{2}{3}(\text{suma de desplazamientos máximos de edificios adyacentes})
   \]
2. verificar retiro hacia linderos y edificaciones vecinas según la norma;
3. si no existe junta sísmica reglamentaria en el edificio vecino, considerar la parte correspondiente de ambos edificios.

---

## 38. Redundancia estructural

Si un solo elemento (muro o pórtico) resiste **30% o más** del cortante horizontal total de un entrepiso, ese elemento debe diseñarse para:

\[
1.25 \times \text{esa fuerza}
\]

---

## 39. Verificación de resistencia última

La norma permite usar, si se decide realizar esa verificación:

- `ASCE/SEI 41`

pero no lo exige como requisito obligatorio.

---

## 40. Tiempo-historia — reglas que el skill sí puede afirmar

Cuando el usuario use verificación por tiempo-historia, Codex debe respetar lo siguiente:

1. seguir los artículos 46 al 49 de la norma;
2. no usar tiempo-historia como sustituto obligatorio del estático o modal espectral;
3. para tratamiento de resultados:
   - las distorsiones máximas de entrepiso no exceden `1.25` veces los valores admisibles;
   - las deformaciones no exceden `2/3` de aquellas asociadas a pérdida de capacidad vertical o pérdida de resistencia mayor a 30%;
   - para verificar resistencia, los resultados del análisis se dividen entre:
     \[
     R = 2
     \]

### Regla de honestidad
Si el usuario pide selección mínima de registros, escalamiento o reglas específicas no visibles en el contexto actual, Codex debe:
- extraer primero los artículos completos del PDF;
- no inventar el número de registros ni procedimientos no verificados.

---

## 41. Procedimiento paso a paso que Codex debe seguir

Codex debe estructurar el trabajo siguiendo el Anexo I y el estilo del texto pegado por el usuario.

### ETAPA 1 — Peligro sísmico
1. Determinar zona sísmica.
2. Determinar `Z`.
3. Clasificar perfil de suelo.
4. Determinar `S`, `TP`, `TL`.
5. Construir función `C(T)`.

### ETAPA 2 — Caracterización del edificio
6. Determinar categoría y `U`.
7. Determinar sistema estructural.
8. Verificar si el sistema está permitido para la categoría y zona.
9. Determinar `R0`.
10. Determinar irregularidades `Ia` e `Ip`.
11. Calcular:
   \[
   R = R_0 \cdot I_a \cdot I_p
   \]

### ETAPA 3 — Análisis
12. Estimar peso sísmico `P`.
13. Verificar si aplica análisis estático o si debe usarse modal espectral.
14. Obtener `T`.
15. Calcular `C`.
16. Calcular cortante basal estático:
   \[
   V = \frac{Z U C S}{R} P
   \]
17. Si es modal espectral, construir espectro:
   \[
   S_a = \frac{Z U C S}{R} g
   \]
18. Verificar masa modal participante.
19. Verificar cortante dinámico mínimo.
20. Escalar resultados si corresponde, excepto desplazamientos.

### ETAPA 4 — Validación
21. Verificar restricciones de irregularidad.
22. Verificar derivas.
23. Verificar separación sísmica.
24. Verificar redundancia estructural.
25. Identificar observaciones o incumplimientos.
26. Generar reporte final.

---

## 42. Plantilla de salida obligatoria para Codex

Cuando el usuario pida “análisis sísmico E.030”, Codex debe responder en un formato parecido a este:

---

# ANÁLISIS SÍSMICO E.030 – SENTIDO X

## 1. Factor de zona sísmica (Z)

**Tabla – Zona sísmica / Factor Z**

| Zona | Z |
|---|---:|
| 4 | 0.45 |
| 3 | 0.35 |
| 2 | 0.25 |
| 1 | 0.10 |

**Dato adoptado**
- Zona ingresada: `...`
- Factor `Z` tomado: `...`

---

## 2. Perfil de suelo

**Tabla – Clasificación resumida**

| Perfil | `Vs` | `N60` | `Su` |
|---|---|---|---|
| S0 | `>800` | — | — |
| S1 | `550–<800` | `>50` | — |
| S2 | `350–<550` | `30–50` | `>100 kPa` |
| S3 | `200–<350` | `15–30` | `50–100 kPa` |
| S4 | `<200` | `<15` | `<50 kPa` |
| S5 | especial | especial | especial |

**Dato adoptado**
- `Vs = ...`
- `N60 = ...`
- `Su = ...`
- Perfil adoptado: `...`

**Advertencias**
- `...`

---

## 3. Parámetros de sitio `S`, `TP`, `TL`

**Tabla – Factor de suelo S**
(Colocar tabla correspondiente)

**Tabla – Períodos `TP`, `TL`**
(Colocar tabla correspondiente)

**Dato adoptado**
- `S = ...`
- `TP = ...`
- `TL = ...`

---

## 4. Factor de amplificación sísmica `C`

**Expresión aplicada**
- tramo usado: `...`
- fórmula: `...`

**Cálculo**
\[
C = ...
\]

---

## 5. Categoría y factor de uso `U`

**Tabla – Categorías**
(Colocar tabla resumida)

**Dato adoptado**
- Categoría: `...`
- `U = ...`

---

## 6. Sistema estructural y `R0`

**Tabla – Sistemas y `R0`**
(Colocar tabla resumida)

**Dato adoptado**
- Sistema en X: `...`
- `R0 = ...`

---

## 7. Irregularidades

**Tabla – Factores `Ia` y `Ip`**

| Factor | Valor |
|---|---:|
| `Ia` | `...` |
| `Ip` | `...` |

**Descripción**
- irregularidades en altura: `...`
- irregularidades en planta: `...`

---

## 8. Coeficiente de reducción `R`

\[
R = R_0 \cdot I_a \cdot I_p
\]

\[
R = (...) \cdot (...) \cdot (...) = ...
\]

---

## 9. Período fundamental

- período adoptado en X: `...`
- fuente: software / artículo 36 / tabla modal

**Si hay tabla modal**, mostrarla.

---

## 10. Peso sísmico `P`

Mostrar:
- peso por nivel;
- suma total;
- porcentaje de carga viva aplicado;
- `P total = ...`

---

## 11. Cortante basal estático

\[
V = \frac{Z U C S}{R} P
\]

Mostrar reemplazo numérico completo.

---

## 12. Análisis dinámico modal espectral
Si aplica:
- espectro usado;
- tabla de modos;
- masa modal participante;
- cortante dinámico;
- comparación con mínimo normativo;
- escalamiento si corresponde.

---

## 13. Desplazamientos laterales
- desplazamiento elástico;
- factor de amplificación de desplazamientos;
- desplazamiento final de diseño.

---

## 14. Derivas
Mostrar por nivel:
- deriva obtenida;
- deriva límite;
- cumple / no cumple.

---

## 15. Separación sísmica
\[
s = 0.02 \cdot Z \cdot S \cdot h \ge 0.03 m
\]

Mostrar cálculo y comparación con desplazamientos relativos.

---

## 16. Redundancia estructural
Indicar si algún elemento resiste 30% o más del cortante del entrepiso.

---

## 17. Conclusiones técnicas
- procedimiento usado;
- si el modelo es compatible con E.030;
- si la estructura cumple o no;
- observaciones pendientes.

---

## 43. Reglas específicas para scripts y automatización

Si el usuario pide código, Codex debe separar el programa así:

### Módulo 1 — Entradas
- ubicación
- categoría
- perfil de suelo
- sistema estructural
- resultados del software
- irregularidades
- pesos por nivel
- desplazamientos por nivel
- etc.

### Módulo 2 — Parámetros normativos
Contendrá:
- tabla `Z`
- tabla `S`
- tabla `TP`, `TL`
- categorías `U`
- sistemas permitidos
- `R0`
- `Ia`
- `Ip`
- límites de deriva
- regla de separación
- regla de redundancia

### Módulo 3 — Lógica de cálculo
Funciones mínimas sugeridas:
- `obtener_zona()`
- `obtener_Z()`
- `clasificar_suelo()`
- `obtener_S_TP_TL()`
- `calcular_C(T, TP, TL, modo_estatico=False)`
- `obtener_U(categoria, usa_aislamiento=False, zona=None, subtipo=None)`
- `obtener_R0(sistema)`
- `calcular_R(R0, Ia, Ip)`
- `calcular_P(...)`
- `verificar_aplicabilidad_estatico(...)`
- `calcular_V_estatico(...)`
- `calcular_Sa(...)`
- `verificar_cortante_dinamico_minimo(...)`
- `amplificar_desplazamientos(...)`
- `verificar_derivas(...)`
- `calcular_separacion(...)`
- `verificar_redundancia(...)`

### Módulo 4 — Validación
El script debe advertir, como mínimo:
- uso de `S5`;
- `Z4 + S4`;
- categoría A/B en zona 4 sin `Ts`;
- sistema no permitido;
- análisis estático no aplicable;
- `R` no consistente;
- derivas fuera de límite;
- cortante dinámico por debajo del mínimo;
- categoría D sin `U` verificado.

### Módulo 5 — Salida
- tablas en consola;
- exportación a Markdown;
- opcionalmente exportación a Word / PDF si el usuario lo pide.

---

## 44. Reglas de validación obligatorias para Codex

Antes de dar un resultado “cerrado”, Codex debe revisar esta lista:

### Validación geotécnica
- [ ] ¿Se identificó correctamente el perfil de suelo?
- [ ] ¿Es `S5`?
- [ ] ¿Hay `Z4 + S4`?
- [ ] ¿Se requiere `Ts` por `H/V`?

### Validación estructural
- [ ] ¿El sistema está permitido para la categoría y zona?
- [ ] ¿Hay irregularidades prohibidas?
- [ ] ¿El análisis estático es aplicable?
- [ ] ¿Se verificó `R = R0 * Ia * Ip`?

### Validación de análisis
- [ ] ¿Se usó la fórmula correcta para `V`?
- [ ] ¿Se respetó `C/R >= 0.11`?
- [ ] ¿Se alcanzó 90% de masa modal?
- [ ] ¿Se verificó el cortante dinámico mínimo?
- [ ] ¿No se escalaron desplazamientos indebidamente?

### Validación de desempeño
- [ ] ¿Se verificaron derivas?
- [ ] ¿Se verificó separación sísmica?
- [ ] ¿Se verificó redundancia?

---

## 45. Reglas de comparación con textos antiguos

Si el usuario entrega un cálculo viejo, una memoria vieja o un archivo como el texto adjunto, Codex debe:

1. identificar qué partes son solo de formato;
2. comparar los valores normativos con la nueva E.030;
3. actualizar, como mínimo:
   - clasificación de suelos;
   - tabla `S`;
   - tabla `TP`, `TL`;
   - definición de `C`;
   - límites de deriva;
   - separación sísmica;
   - restricciones por irregularidad;
4. marcar los cambios relevantes;
5. no copiar tablas antiguas si ya no son válidas.

---

## 46. Diferencias clave que Codex debe tener presentes respecto a versiones anteriores

Codex debe asumir que los siguientes puntos **ya cambiaron** en la nueva norma y, por tanto, no debe reutilizar automáticamente valores anteriores:

1. **Clasificación de suelos**
   - ahora incluye `S5`;
   - cambian rangos de `Vs`, `N60`, `Su`.

2. **Tabla de `S`**
   - cambian varios valores;
   - en `Z4 + S4` se requiere análisis de respuesta de sitio.

3. **Tabla de `TP`, `TL`**
   - `S2` y `S3` ahora usan intervalos e interpolación;
   - `TL` cambia respecto a versiones previas.

4. **Definición de `C`**
   - ahora existe tramo:
     \[
     T < 0.2 T_P
     \]
     con:
     \[
     C = 1 + 7.5(T/T_P)
     \]

5. **Deriva para EMDL**
   - ahora:
     \[
     0.004
     \]

6. **Separación sísmica**
   - ahora:
     \[
     s = 0.02 Z S h \ge 0.03\,m
     \]

7. **Reglas especiales para A/B en zona 4**
   - incorporación de `Ts` con método `H/V`.

---

## 47. Qué NO debe hacer Codex

- no usar el archivo de texto antiguo como si fuera norma;
- no mezclar tablas viejas con la norma nueva;
- no asumir `U` de categoría D si no está confirmado en la fuente visible;
- no usar análisis estático si normativamente no aplica;
- no omitir restricciones de irregularidad;
- no reportar derivas sin aclarar si ya fueron amplificadas por `0.75R` o `0.85R`;
- no escalar desplazamientos al ajustar el cortante dinámico mínimo;
- no asignar `S` directo para `Z4 + S4`;
- no tratar `S5` como si fuera `S4`;
- no fabricar la fórmula de los artículos no completamente visibles si no fueron extraídos del PDF fuente.

---

## 48. Instrucción final para Codex

Cuando recibas una solicitud relacionada con la E.030:

1. **lee primero la nueva norma adjunta**;
2. usa el texto pegado solo como **molde de presentación**;
3. extrae de la norma los factores y criterios necesarios;
4. verifica aplicabilidad y restricciones;
5. si algo no está completo en el contexto, dilo claramente;
6. entrega una salida técnica, ordenada, audit-able y conservadora.

---

## 49. Respuesta corta que Codex puede usar como política interna

> “Usaré como fuente principal el archivo adjunto `Norma E.030 Diseño sismorresistente_2026.pdf` (contenido interno 2025), tomaré el texto pegado solo como formato de salida, actualizaré tablas y criterios a la nueva E.030, no mezclaré valores de versiones antiguas y marcaré explícitamente cualquier dato normativo no verificable antes de cerrar el cálculo.”

---

## 50. Recomendación de uso del skill

Este skill funciona mejor cuando el usuario entrega, además del PDF normativo:
- exportaciones de ETABS/SAP;
- peso por nivel;
- períodos modales;
- desplazamientos y derivas;
- sistema estructural por dirección;
- ubicación del proyecto;
- datos geotécnicos.

Si el usuario solo entrega resultados parciales, Codex debe construir un **reporte parcial** y listar los faltantes.

---
