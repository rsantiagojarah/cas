---
name: reportes-latex-memoria-calculo
description: Genera memorias de calculo en LaTeX para ingenieria estructural con formato tecnico formal (margenes, tablas, secciones, ecuaciones y grafica de espectro). Usar cuando el usuario pida crear, adaptar o estandarizar reportes PDF de calculo desde datos en Markdown, texto, tablas o resultados de software de analisis.
---

# Reportes LaTeX de Memoria de Calculo

## Objetivo

Estandarizar la creacion de reportes tecnicos de memoria de calculo en LaTeX con estilo profesional, listos para compilar a PDF y consistentes entre proyectos.

Este skill prioriza:
- estructura clara por secciones tecnicas,
- tablas bien ubicadas en su contexto,
- ecuaciones y unidades consistentes,
- formato visual estable y legible.

## Cuándo usar este skill

Aplicar este skill cuando el usuario solicite:
- "generar reporte", "memoria de calculo", "pasar markdown a latex",
- "dar formato tecnico al PDF",
- "corregir tablas que se van al final",
- "ajustar margenes, titulos, subtitulos, interlineado",
- "incluir grafica de espectro sismico" u otras graficas tecnicas.

## Resultado esperado

Entregar siempre:
1. Archivo `.tex` listo para compilar.
2. PDF compilado sin errores fatales.
3. Formato tecnico consistente (margenes, tipografia, tablas y secciones).
4. Breve resumen de cambios realizados.

---

## Flujo recomendado

### 1) Levantamiento de insumos

Identificar:
- archivo fuente de datos (`.md`, `.txt`, `.csv`, tablas exportadas),
- plantilla base (`.tex`) existente en el proyecto,
- requisitos visuales del usuario (1 o 2 columnas, margenes, tamanos de titulos).

Si existe una plantilla previa en el proyecto, tratarla como fuente de verdad del estilo.

### 2) Mapeo de contenido tecnico

Transformar el contenido fuente a bloques LaTeX:
- encabezados -> `\section*{...}` / `\subsection*{...}`,
- formulas -> entorno matematico `\[ ... \]`,
- tablas -> `table` + `tabular` + `booktabs`,
- criterios normativos -> texto tecnico breve y verificable.

No copiar arte ASCII en crudo al PDF si ya puede representarse con tabla o figura nativa de LaTeX.

### 3) Aplicar formato estandar

Usar este baseline (ajustable por pedido del usuario):
- clase: `scrartcl`, `a4`, `10pt`,
- idioma: `spanish` con `babel`,
- margenes por defecto del skill: `2.5 cm`,
- interlineado: `\onehalfspacing`,
- tablas ancladas con `[H]` (paquete `float`) para evitar que migren al final,
- secciones compactas: titulo principal, secciones y subtitulos en tamano moderado.

### 4) Compilacion y validacion

Compilar minimo una vez con:
- `pdflatex -interaction=nonstopmode -halt-on-error archivo.tex`

Si hay referencias cruzadas (LastPage, labels), compilar dos veces.

Revisar:
- que no haya errores fatales,
- que tablas y figuras queden cerca del texto que las menciona,
- que no se rompa la legibilidad por sobrecarga visual.

### 5) Entrega

Informar:
- ruta del PDF generado,
- cambios clave de formato,
- pendientes opcionales (solo si el usuario quiere ajustes finos).

---

## Reglas de formato tecnico (estilo de memoria)

## Documento

- Preferir una columna para memorias largas con tablas anchas.
- Evitar titulos gigantes tipo poster.
- Mantener consistencia de unidades (`s`, `ton`, `g`, etc.).

## Preambulo minimo recomendado

```tex
\documentclass[paper=a4,fontsize=10pt]{scrartcl}
\usepackage[top=2.5cm,bottom=2.5cm,left=2.5cm,right=2.5cm]{geometry}
\usepackage[spanish]{babel}
\usepackage{setspace}
\usepackage{amsmath,amsfonts,amsthm}
\usepackage{booktabs}
\usepackage{float}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
```

## Interlineado

Aplicar al inicio del documento:

```tex
\begin{document}
\onehalfspacing
```

## Tablas

Usar:

```tex
\begin{table}[H]
\centering
\caption{...}
\begin{tabular}{...}
\toprule
...
\bottomrule
\end{tabular}
\end{table}
```

Regla: si una tabla no cabe, primero simplificar columnas o abreviar texto; solo si es necesario, dividir en dos tablas.

## Graficas tecnicas (ejemplo: espectro sismico)

Para curvas normativas, usar `pgfplots` (no ASCII art).  
Incluir ejes, unidades y caption tecnico.

---

## Estructura recomendada de memoria de calculo sismico

Usar esta secuencia como plantilla base:

1. Factor de zona sismica.
2. Perfil y factor de suelo.
3. Parametros de sitio (`S`, `Tp`, `Tl`).
4. Categoria de edificacion y `U`.
5. Sistema estructural y `R0`.
6. Factores de irregularidad.
7. Coeficiente de reduccion `R`.
8. Periodo fundamental.
9. Masa participante modal.
10. Peso sismico por nivel.
11. Analisis estatico.
12. Analisis dinamico.
13. Espectro sismico.
14. Verificacion de cortante minimo.
15. Revision de hipotesis estructural.
16. Derivas / distorsiones admisibles.

---

## Criterios de calidad antes de finalizar

- [ ] El PDF compila sin errores fatales.
- [ ] Se respeta el idioma tecnico (espanol, terminologia coherente).
- [ ] Tablas y figuras no quedan apiladas al final sin contexto.
- [ ] Titulos/subtitulos legibles y proporcionados.
- [ ] Margenes e interlineado cumplen lo pedido por el usuario.
- [ ] Ecuaciones y variables usan notacion consistente.
- [ ] Se reportan claramente los valores finales y verificaciones de cumplimiento.

---

## Plantillas y recursos del skill

- Para ejemplos de prompts de uso: ver [examples.md](examples.md)
- Para checklist operativo rapido: ver [checklist.md](checklist.md)
- Para base editable de reporte: ver [plantilla_reporte.tex](plantilla_reporte.tex)

---

## Modo de respuesta sugerido al usuario

Cuando se complete una tarea con este skill:
- resumir en 3-6 bullets lo modificado,
- indicar ruta del `.tex` y del `.pdf`,
- proponer 1-3 ajustes opcionales (sin sobre-explicar).

