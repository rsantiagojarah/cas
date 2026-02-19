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

Paso 2: Factor de Suelo (S): Se debe ingresar el perfil de la categoria de suelo de la ciudad de la edificacion. Se ingresara (s0, s1, s2, s3, s4).

| Perfil | Descripción General                                      | Vs30 (m/s)        | N60 (SPT) | Su (kPa) |
|--------|----------------------------------------------------------|------------------|-----------|----------|
| S0     | Roca muy dura                                            | > 1500           | —         | —        |
| S1     | Roca o suelo muy rígido                                  | 760 – 1500       | > 50      | > 100    |
| S2     | Suelos intermedios (densos o consistentes)               | 360 – 760        | 15 – 50   | 50 – 100 |
| S3     | Suelos blandos                                           | 180 – 360        | < 15      | < 50     |
| S4     | Suelos muy blandos o especiales (condición particular)   | < 180            | —         | —        |


Paso 3: Parametro de sitio S, Tp y Tl: Deacuerdo al Factor de suelo (S), el programa debe ubicar el S, Tp y Tl de la tabla

| Perfil | Factor de Suelo (S) | Tp (s) | Tl (s) |
|--------|---------------------|--------|--------|
| S0     | 0.80                | 0.30   | 3.0    |
| S1     | 1.00                | 0.40   | 2.5    |
| S2     | 1.20                | 0.60   | 2.0    |
| S3     | 1.40                | 0.90   | 1.6    |
| S4     | Según estudio específico |

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

Paso 5: Categoria de la edificacion y el factor de uso (U): Ingresar la categoria de la edificacion y el factor de uso (U) de la tabla. Se ingresara (A, B, C, D).


| Categoría | Tipo de Edificación                                   | U    |
|------------|------------------------------------------------------|------|
| A (A1–A2)  | Edificaciones esenciales (hospitales, emergencia)    | 1.50 |
| B          | Alta concentración de personas (colegios, públicos)  | 1.30 |
| C          | Edificaciones comunes (vivienda, oficinas)           | 1.00 |
| D          | Temporales o de bajo riesgo                          | 0.80 |

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

Paso 8: Coeficiente de Reduccion de la fuerza sismica (R):

R = R₀ * Ia * Ip

ETAPA 3 ANALISIS ESTRUCTURAL

Paso 9: Periodo fundamental de la edificacion (T):

Se obtendra de la tabla de Etabs obtenida con la API, la tabla se llama "Modal Participating Mass Ratio", quiero que solo aparezcan la tabla las columnas Case, Period pero antes quiero que ubiques el mayor UX y UY y ese valor corresponde en la misma fila al periodo fundamental tanto para X como para Y. quiero que lo indiques


Paso 10: Porcentaje de masa participante:

Se obtendra de la tabla de Etabs obtenida con la API, la tabla se llama "Modal Participating Mass Ratio", quiero que solo aparezcan la tabla las columnas Case, Period,UX, UY, UZ,SumUX, SumUY, SumUZ. Quiero que verifiques que el porcentaje de masa participante sea mayor al 90% para cada caso.


Paso 9: Estimacion de Peso de la edificacion (P):
Esto se obtendra de una tabla de etabs obtenida con la API, la tabla se llama "Mass Summary by Story", se utilizara todos los pisos a excepcion de la base y se umtiplicara  a las columnas UX, UY por 9.80665 para generar las columnas Peso X y Peso Y y las columnas UX y Uy no deben aparecer; solo Story, Peso X y Peso Y.

Paso 10: Analisis estatico:

Se obtendra la tabla de Etabs obtenida con la API, la tabla de llama Story Forces, Se filtrara la columna OutputCase=SISMOX, y Location=Bottom y solo quiero las columnas Story,Output Case y VX de igual manera para el caso de SISMOY se filtrara la columna OutputCase=SISMOY, y Location=Bottom y solo quiero las columnas Story,Output Case y VY

Paso 11: Analisis dinamico: 

Se obtendra la tabla de Etabs obtenida con la API, la tabla de llama Story Forces, Se filtrara la columna OutputCase=SPX, y Location=Bottom y solo quiero las columnas Story,Output Case y VX de igual manera para el caso de SISMOY se filtrara la columna OutputCase=SPY, y Location=Bottom y solo quiero las columnas Story,Output Case y VY

Paso 12: Verficacion de cortante minima en cada direccion:

Se verificara que el cortante basal en cada direccion sea mayor al 80% del cortante basal estatico. Para esto se obtendra la tabla de Etabs obtenida con la API, la tabla de llama Base Reactions, se filtrara la columna OutputCase=SISMOX y SPX, y se calculara con los valores de la columna FX que el sismo dinamico (SPX) sea mayor al 80% del sismo estatico (SISMOX). de la misma manera para el caso de SISMOY y SPY.

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












