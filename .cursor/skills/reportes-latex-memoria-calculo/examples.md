# Ejemplos de uso

## Ejemplo 1: Convertir Markdown a memoria en LaTeX

**Prompt del usuario**
```text
Convierte este archivo .md a un reporte LaTeX de memoria de calculo estructural y genera el PDF.
```

**Comportamiento esperado**
- Leer el `.md` completo.
- Mapear secciones y tablas al formato LaTeX tecnico.
- Aplicar estilo del skill (margenes, interlineado, tablas [H]).
- Compilar PDF y reportar ruta final.

---

## Ejemplo 2: Ajuste de formato visual

**Prompt del usuario**
```text
Los titulos estan muy grandes y las tablas se van al final. Corrigelo.
```

**Comportamiento esperado**
- Reducir tamano de titulo, secciones y subtitulos.
- Usar `\begin{table}[H]` con `float`.
- Recompilar y validar ubicacion de tablas.

---

## Ejemplo 3: Incluir grafica de espectro

**Prompt del usuario**
```text
Agrega la grafica del espectro sismico Sa vs T usando Z=0.35, U=1.0, S=1.15, R=5.4, Tp=0.6, Tl=2.0.
```

**Comportamiento esperado**
- Insertar grafica con `pgfplots`.
- Etiquetar ejes y unidades.
- Mantener coherencia con las ecuaciones del documento.

---

## Ejemplo 4: Estandar para nuevos proyectos

**Prompt del usuario**
```text
Crea una memoria base para mis proximos proyectos con este mismo formato.
```

**Comportamiento esperado**
- Crear `.tex` base reutilizable.
- Incluir portada tecnica, secciones tipo, tablas ejemplo y bibliografia normativa.
- Dejar instrucciones claras para reemplazar datos.

