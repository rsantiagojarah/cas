# Checklist operativo rapido

Copiar y marcar durante la ejecucion:

## 1) Entrada y contexto
- [ ] Identifique el archivo fuente principal (`.md`, `.txt`, etc.).
- [ ] Identifique plantilla `.tex` existente (si aplica).
- [ ] Confirme requisitos de formato (margenes, columnas, tamanos).

## 2) Transformacion tecnica
- [ ] Convierta encabezados a secciones LaTeX.
- [ ] Convierta formulas a entorno matematico.
- [ ] Convierta tablas a `booktabs`.
- [ ] Elimine arte ASCII no necesario.

## 3) Formato
- [ ] Margenes correctos segun pedido.
- [ ] Interlineado aplicado.
- [ ] Titulo/subtitulos proporcionados.
- [ ] Tablas en `[H]` para evitar reubicacion indeseada.

## 4) Compilacion
- [ ] Compile con `pdflatex -interaction=nonstopmode -halt-on-error`.
- [ ] Recompile si hay referencias cruzadas.
- [ ] Verifique PDF final.

## 5) Salida
- [ ] Informe ruta de `.tex` y `.pdf`.
- [ ] Resuma cambios clave.
- [ ] Proponga ajustes opcionales puntuales.

