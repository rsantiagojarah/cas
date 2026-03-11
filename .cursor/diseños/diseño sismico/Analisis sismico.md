PROCEDIMIENTO COMPLETO PARA LA DETERMINACIÓN DE ACCIONES SÍSMICAS

Norma Técnica E.030 – Diseño Sismorresistente (RNE)

ETAPA 1 – PELIGRO SÍSMICO

Paso 1: Factor de Zona Sísmica (Z): Se debe ingresar el numero de la zona sismica de la ciudad de la edificacion. Se ingresara (1,2,3,4).

| Zona Sísmica | Factor de Zona (Z) |
|--------------|--------------------|
| Zona 4       | 0.45               |
| Zona 3       | 0.35               |
| Zona 2       | 0.25               |
| Zona 1       | 0.10               |

Paso 2: Factor de Suelo (S): Se debe ingresar el perfil de la categoria de suelo de la ciudad de la edificacion. Se ingresara (s0, s1, s2, s3, s4). La clasificación sigue la **Tabla N° 2 – Clasificación de los perfiles de suelo** de la Norma E.030.

| Perfil | Descripción General                                      | Vs (m/s)                 | N60 (SPT) | Su (kPa)          |
|--------|----------------------------------------------------------|--------------------------|-----------|-------------------|
| S0     | Roca muy dura                                            | > 1500                   | —         | —                 |
| S1     | Roca o suelo muy rígido                                  | 500 a 1500              | > 50      | > 100             |
| S2     | Suelos intermedios (densos o consistentes)               | 180 a 500               | 15 a 50   | 50 a 100          |
| S3     | Suelos blandos                                           | < 180                   | < 15      | 25 a 50           |
| S4     | Suelos muy blandos o especiales (condición particular)   | Clasificación basada en el EMS | —   | —                 |


Paso 3: Parámetros de sitio S, Tp y Tl: Según la zona sísmica y el perfil de suelo, el programa debe obtener el **Factor de Suelo S** de la Tabla N° 3 y los **períodos Tp y Tl** de la Tabla N° 4.

**Tabla N° 3 – Factor de Suelo "S"**

| Zona / Suelo | S0   | S1   | S2   | S3   |
|--------------|------|------|------|------|
| Z4           | 0.80 | 1.00 | 1.05 | 1.10 |
| Z3           | 0.80 | 1.00 | 1.15 | 1.20 |
| Z2           | 0.80 | 1.00 | 1.20 | 1.40 |
| Z1           | 0.80 | 1.00 | 1.60 | 2.00 |

**Tabla N° 4 – Períodos "Tp" y "Tl" (s)**

| Perfil de suelo | S0   | S1   | S2   | S3   |
|-----------------|------|------|------|------|
| Tp (s)          | 0.30 | 0.40 | 0.60 | 1.00 |
| Tl (s)          | 3.0  | 2.5  | 2.0  | 1.6  |

Para el perfil **S4** los valores de S, Tp y Tl se definen según estudio específico.

Paso 4: Construir la funcion factor de amplificacion sismica C versus Periodo T (Output datos tabulados de C vs T)

El factor de amplificación sísmica C depende del período fundamental T de la estructura y de los parámetros del sitio Tp y TL.

### Caso 1: Períodos cortos
Si T < Tp

C = 2.5

---

### Caso 2: Períodos intermedios
Si Tp ≤ T ≤ TL

C = 2.5 (Tp / T)

---

### Caso 3: Períodos largos
Si T > TL

C = 2.5 (Tp · TL / T²)

---


ETAPA 2 – CARACTERIZACION DEL EDIFICIO

Paso 5: Categoría de la edificación y factor de uso (U): Ingresar la categoría de la edificación y el factor de uso (U) según la **Tabla N° 5**. Se ingresará (A, B, C, D).

**Tabla N° 5 – Categoría de las edificaciones y factor "U"**

| Categoría | Descripción (resumen) | Factor U |
|-----------|------------------------|----------|
| **A** – Edificaciones Esenciales | A1: Establecimientos de salud (2.° y 3.° nivel). A2: Emergencias, gobierno, refugio (ver detalle abajo). | A1: Ver nota 1 / A2: 1,5 |
| **B** – Edificaciones Importantes | Gran concentración de personas o patrimonios valiosos (cines, estadios, centros comerciales, museos, etc.). | 1,3 |
| **C** – Edificaciones Comunes | Viviendas, oficinas, hoteles, restaurantes, depósitos e industrias sin riesgo adicional. | 1,0 |
| **D** – Edificaciones Temporales | Construcciones provisionales (depósitos, casetas y similares). | Ver nota 2 |

**Detalle categoría A2:** Edificaciones esenciales para el manejo de emergencias, funcionamiento del gobierno y refugio después de un desastre. Se incluyen: establecimientos de salud no comprendidos en A1; puertos, aeropuertos, estaciones ferroviarias de pasajeros, sistemas masivos de transporte, locales municipales, centrales de comunicaciones; estaciones de bomberos, cuarteles de fuerzas armadas y policía; instalaciones de generación y transformación de electricidad, reservorios y plantas de tratamiento de agua; instituciones educativas, institutos superiores tecnológicos y universidades; edificaciones cuyo colapso pueda representar riesgo adicional (grandes hornos, fábricas, depósitos de materiales inflamables o tóxicos); edificios que almacenen archivos e información esencial del Estado.

**Nota 1:** Las nuevas edificaciones de categoría A1 tienen aislamiento sísmico en la base cuando se encuentren en las zonas sísmicas 4 y 3. En las zonas sísmicas 1 y 2, la entidad responsable puede decidir si usa o no aislamiento sísmico. Si no se utiliza aislamiento sísmico en las zonas sísmicas 1 y 2, el valor de U es como mínimo 1,5.

**Nota 2:** En estas edificaciones se provee resistencia y rigidez adecuadas para acciones laterales, a criterio del proyectista.

Paso 6: Factor de reduccion de respuesta sismica (R): Ingresar el factor de reduccion de respuesta sismica (R) de la tabla.

# Tabla – Sistemas Estructurales y Factor de Reducción R₀
(Norma E.030 – Diseño Sismorresistente)

| Sistema Estructural                                        | R₀ |
|------------------------------------------------------------|----|
| Pórticos de Concreto Armado                                | 8  |
| Muros Estructurales de Concreto Armado                     | 6  |
| Sistema Dual (Pórticos + Muros Estructurales)              | 7  |
| Albañilería Confinada                                      | 3  |

Paso 7: Factores de irregularidad en altura (Ia) y en planta (Ip): Ingresar el factor de irregularidad en altura (Ia) y en planta (Ip) ademas indicar el tipo de irregularidad.

Paso 8: Coeficiente de Reduccion de la fuerza sismica (R):********

R = R₀ * Ia * Ip

ETAPA 3 ANALISIS ESTRUCTURAL

Paso 9: Periodo fundamental de la edificacion (T):

Se obtendra de la tabla de Etabs obtenida con la API, la tabla se llama "Modal Participating Mass Ratio", quiero que quiero que ubiques el mayor UX y UY y ese valor corresponde en la misma fila al periodo fundamental tanto para X como para Y. quiero que lo indiques; y quiero que muestres la tabla de "Modal Periods And Frecuencies"


Paso 10: Porcentaje de masa participante:

Se obtendra de la tabla de Etabs obtenida con la API, la tabla se llama "Modal Participating Mass Ratio", quiero que solo aparezcan la tabla las columnas Case, Period,UX, UY, UZ,SumUX, SumUY, SumUZ. Quiero que verifiques que el porcentaje de masa participante sea mayor al 90% para cada caso.


Paso 9: Estimacion de Peso de la edificacion (P):
Esto se obtendra de una tabla de etabs obtenida con la API, la tabla se llama "Mass Summary by Story", se utilizara todos los pisos a excepcion de la base y se umtiplicara  a las columnas UX, UY por 9.80665 para generar las columnas Peso X y Peso Y y las columnas UX y Uy no deben aparecer; solo Story, Peso X y Peso Y.

Paso 10: Analisis estatico:

Se obtendra la tabla de Etabs obtenida con la API, la tabla de llama Story Forces, Se filtrara la columna OutputCase=SISMOX, y Location=Bottom y solo quiero las columnas Story,Output Case y VX de igual manera para el caso de SISMOY se filtrara la columna OutputCase=SISMOY, y Location=Bottom y solo quiero las columnas Story,Output Case y VY

Paso 11: Analisis dinamico: 

Se obtendra el valor de Sa para cada direccion, para esto se utilizara la formula:
Sa = (Z U C S / R ) * g

Se obtendra la tabla de Etabs obtenida con la API, la tabla de llama Story Forces, Se filtrara la columna OutputCase=SPX, y Location=Bottom y solo quiero las columnas Story,Output Case y VX de igual manera para el caso de SISMOY se filtrara la columna OutputCase=SPY, y Location=Bottom y solo quiero las columnas Story,Output Case y VY

Paso 12: Verficacion de cortante minima en cada direccion:

Segun la Norma E.030, la verificacion de cortante basal minima depende de la existencia de irregularidades en altura (Ia) o en planta (Ip):

- Si la estructura **no presenta irregularidades** (Ia = 1 e Ip = 1), el **cortante basal dinamico minimo** debe ser mayor o igual al **80%** del cortante basal estatico.
- Si la estructura **presenta alguna irregularidad** (Ia distinto de 1 o Ip distinto de 1, por ejemplo Ia = 0.9 o Ip = 1.1), el **cortante basal dinamico minimo** debe ser mayor o igual al **90%** del cortante basal estatico.

Para esto se obtendra la tabla de Etabs obtenida con la API, la tabla se llama **Base Reactions**. Se filtrara la columna `OutputCase` para los casos `SISMOX` y `SPX` (direccion X) y se usaran los valores de la columna `FX` para calcular:

- Cortante basal estatico \(V_\text{est}\) (caso `SISMOX`).
- Cortante basal dinamico \(V_\text{din}\) (caso `SPX`).

De la misma manera se procedera para la direccion Y con los casos `SISMOY` y `SPY` usando la columna `FY`:

- Cortante basal estatico \(V_\text{est}\) (caso `SISMOY`).
- Cortante basal dinamico \(V_\text{din}\) (caso `SPY`).

Definimos el **umbral de cortante minima** \(\alpha\) segun las irregularidades:

- \(\alpha = 0.80\) si Ia = 1 e Ip = 1 (edificio regular).
- \(\alpha = 0.90\) si Ia > 1 o Ip > 1 (edificio irregular).

La **cortante dinamica minima requerida** en cada direccion es:

\[
V_{\text{din,min}} = \alpha \cdot V_\text{est}
\]

Se calcula el **factor de escalamiento dinamico** necesario para alcanzar esa condicion:

\[
\gamma = \frac{V_{\text{din,min}}}{V_\text{din}}
\]

- Si \(V_\text{din} \ge V_{\text{din,min}}\), entonces \(\gamma = 1.0\) y **no se requiere escalar**; la verificacion de cortante minima se realiza directamente con el valor dinamico obtenido.
- Si \(V_\text{din} < V_{\text{din,min}}\), entonces \(\gamma > 1.0\) y **se debe escalar** la respuesta dinamica:

\[
V_{\text{din,esc}} = \gamma \cdot V_\text{din}
\]

La verificacion final de cortante minima se realiza comparando el cortante basal dinamico escalado con el umbral:

\[
V_{\text{din,esc}} \ge V_{\text{din,min}}
\]

En el reporte se debe indicar, para cada direccion:

- Cortante basal estatico \(V_\text{est}\).
- Cortante basal dinamico sin escalar \(V_\text{din}\).
- Umbral \(\alpha\) usado (80% o 90% segun irregularidades Ia, Ip).
- Cortante dinamica minima requerida \(V_{\text{din,min}}\).
- Factor de escalamiento \(\gamma\) (y si se requiere o no escalar).
- Cortante basal dinamica escalada \(V_{\text{din,esc}}\).
- Resultado de la verificacion de cortante minima (cumple / no cumple).

ETAPA 4 – VALIDACION DE LA ESTRUCTURA

Paso 12: Revision de las hipotesis de an analisis: Se verificara que el R haya sido el adecuado.

Se obtendra la tabla de Etabs obtenida con la API. Para el sentido X Se filtrara la columna Story = Story1; OutputCase = SPX; Station = 0; Solo quiero que queden las columnas Story, Column, OutputCase y V3. Para el sentido Y Se filtrara la columna Story = Story1; OutputCase = SPY; Station = 0; Solo quiero que queden las columnas Story, Column, OutputCase y V2. En cada tabla se sumara el V3 para la direccion X y el V2 para la direccion Y; y se obtendra que porcentaje de representa de toda la cortante basal obtenida en el paso 10 (que corresponde al story1).

A partir de esto se clasificara la estructura en:


| Sistema                  | % Cortante tomado por Muros | % Cortante tomado por Pórticos |
|--------------------------|-----------------------------|--------------------------------|
| **Pórtico**              | < 20%                       | ≥ 80%                          |
| **Dual**                 | > 20% y < 70%               | Complementario                 |
| **Muros estructurales**  | ≥ 70%                       | ≤ 30%                          |

Paso 13 Distorsion Admisible:

Se obtendra de la tabla de ETABS obtenido por la API, la tabla se llama Story Drifts, Para x se filtrara la columna OutputCase = SPX, Direction = X; quiero que solo queden las columnas Story, OutputCase, Direction y DriftX. Para y se filtrara la columna OutputCase = SPY, Direction = Y; quiero que solo queden las columnas Story, OutputCase, Direction y DriftY.

a cada valor de la columna DriftX y DriftY se le multiplicara por 0.75 y R0. Se obtendra el valor de la distorsion admisible para cada sentido. Se debera verificar esto segun el material predominante de la estructura.


| Material Predominante                                  | Distorsión Máxima Admisible (Δ/h) |
|--------------------------------------------------------|------------------------------------|
| Concreto Armado                                       | 0.007                              |
| Acero                                                  | 0.010                              |
| Albañilería                                            | 0.005                              |
| Madera                                                 | 0.010                              |
| Concreto Armado con Muros de Ductilidad Limitada      | 0.005                              |


Paso 14: Separacion de edificios:

s mayor a 2/3 de la suma de los desplazamientos maximos de los edificios adycentes.

s = 0.006 *h >= 0.03
el mayor de todos estos valores sera el valor de s.












