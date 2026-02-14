# AXIS — Core Architecture Specification

## 🎯 Objetivo

Construir el núcleo estable de un motor modular de diseño estructural.

⚠️ En esta fase NO se implementa ningún tipo de diseño.
⚠️ No existen vigas, columnas ni cálculos aún.
⚠️ Solo se implementa infraestructura extensible.

El sistema debe permitir agregar funcionalidades futuras sin modificar el núcleo.

---

# 🧠 Filosofía del Sistema

1. Arquitectura extensible basada en registro dinámico (plugin system).
2. Núcleo cerrado para modificación.
3. Nuevas funcionalidades se agregan como módulos independientes.
4. Todo cálculo futuro generará un archivo CSV.
5. Separación estricta entre:
   - Proyecto
   - Motor
   - Registro
   - CLI
   - Base de datos
6. El CLI debe ser minimalista:
axis <scope> <operation>


---

# 🏗 Estructura Base del Proyecto

axis/
│
├── core/
│ ├── registry.py
│ ├── project.py
│ ├── database.py
│ ├── tree.py
│ ├── context.py
│ └── exceptions.py
│
├── engine/
│ └── engine.py
│
├── operations/
│ ├── init.py
│ └── placeholder.py
│
├── cli/
│ └── cli.py
│
├── config/
│ └── defaults.json
│
├── logs/
│
├── main.py
└── axis_active_project.json


---

# 1️⃣ Sistema de Registro

## core/registry.py

Responsabilidad:
Registrar dinámicamente operaciones futuras.

Requisitos:

- Crear diccionario REGISTRY
- Crear decorador register(scope, operation)
- No depender de ningún elemento estructural
- No contener lógica de diseño

Estructura conceptual:

```python
REGISTRY = {}

def register(scope: str, operation: str):
    def decorator(func):
        REGISTRY[(scope, operation)] = func
        return func
    return decorator
Este archivo nunca debe modificarse después de esta fase.

2️⃣ Motor Central
engine/engine.py
Responsabilidad:
Ejecutar operaciones registradas.

Requisitos:

Recibir:

scope

operation

data

Buscar operación en REGISTRY

Ejecutar función correspondiente

Retornar resultado

Manejar error si no existe operación

No debe conocer:

Sistema de archivos

Tipos de elementos

Normas

Matemática

Debe ser genérico.

3️⃣ Gestión de Proyecto
core/project.py
Responsabilidad:
Crear y manejar proyectos.

Funciones requeridas:

create_project(name)

list_projects()

set_active_project(name)

get_active_project()

validate_project_structure()

Al ejecutar:

axis new edificio1
Debe crearse:

edificio1/
│
├── axis_project.json
├── elements/
│   └── data.csv
├── results/
└── reports/
No se crean elementos específicos todavía.

4️⃣ Proyecto Activo
Archivo global:

axis_active_project.json
Debe contener:

{
  "active_project": "edificio1"
}
Permite que el sistema sepa dónde trabajar.

5️⃣ Base de Datos
core/database.py
Responsabilidad:

Crear data.csv si no existe

Leer CSV

Guardar resultados CSV

Verificar existencia de archivos

Reglas:

El motor no debe manejar archivos directamente.

Solo database.py interactúa con CSV.

6️⃣ Sistema de Árbol
core/tree.py
Responsabilidad:

Leer estructura del proyecto activo

Mostrar:

Proyecto

Archivos de data

Resultados existentes

Reportes

Comando:

axis tree
Debe funcionar incluso si no hay diseños implementados.

7️⃣ Manejo de Contexto
core/context.py
Responsabilidad:

Determinar si:

Existe proyecto activo

Es modo cálculo directo

Centralizar configuración global

8️⃣ Manejo de Errores
core/exceptions.py
Definir:

ProjectNotFound

NoActiveProject

OperationNotRegistered

InvalidInput

Evitar que el sistema colapse.

9️⃣ CLI Minimalista
cli/cli.py
Formato obligatorio:

axis <scope> <operation>
Comandos base obligatorios:

axis new <project>
axis use <project>
axis tree
axis info
axis list-projects
Debe:

Parsear argumentos

Detectar modo directo si hay parámetros

Llamar a engine.run()

No debe contener:

Lógica matemática

Acceso directo a archivos

Registro manual de operaciones

🔟 Placeholder de Operaciones
operations/placeholder.py
Registrar una operación dummy para probar arquitectura:

@register("test", "run")
def test_operation(data):
    return {"status": "ok"}
Permite probar que el núcleo funciona.

11️⃣ Reglas Arquitectónicas Inquebrantables
engine.py nunca se modifica después de esta fase.

registry.py nunca se modifica.

CLI no contiene lógica de negocio.

Las operaciones futuras no modifican archivos del núcleo.

Todo cálculo futuro generará un CSV.

El sistema debe poder crecer sin alterar código existente.

12️⃣ Fase Actual
Esta fase implementa:

✔ Infraestructura completa
✔ Sistema extensible
✔ CLI funcional
✔ Gestión de proyecto
✔ Árbol
✔ Registro dinámico
✔ Motor genérico

NO implementa:

✖ Vigas
✖ Columnas
✖ Flexión
✖ Corte
✖ Interacción
✖ Esbeltez

🎯 Resultado Esperado
Un núcleo estable, profesional y extensible sobre el cual se podrán agregar:

Elementos estructurales

Tipos de diseño

Normas

Reportes

Validaciones

Módulos adicionales

Sin romper nada existente.


---

Santiago, este documento define un **framework serio y estable**.

Si Cursor construye exactamente esto, tendrás una base que no se rompe.

Si quieres, el siguiente paso puede ser:

- Especificación exacta del CLI con ejemplos
- O diseño del primer plugin real (pero bien estructurado)
- O diseño del sistema de pruebas automáticas para que nunca se rompa

Tú decides el siguiente nivel.