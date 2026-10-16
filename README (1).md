# EduTech Academy — Arquitectura del Sistema de Gestión de Cursos y Certificaciones

**Materia:** Componentes de Lógica de Negocio  
**Institución:** FIME — UANL  
**Profesor:** Miguel Ángel Gómez Marroquín  
**Actividad:** Unidad 3 — Diseño arquitectural del sistema con IA

## Integrantes

| Integrante | Matrícula |
|---|---:|
| Carlos Hugo García Gómez | 2226690 |
| Alan Bertín Castillo Martínez | 2226653 |
| Saúl Alejandro Hernández Garza | 2226664 |

## Descripción

Propuesta de arquitectura de software para **EduTech Academy**, construida a partir del análisis de negocio de la Unidad 2 (BRD, historias de usuario, BPMN, glosario y matriz de trazabilidad). El diseño separa **dominio**, **aplicación** e **infraestructura** y cubre procesos como inscripción, control de cupo, pagos pendientes, cancelación de cursos, cambios de grupo, sustitución de instructor y emisión de certificados.

Patrones y principios aplicados:

- Domain Model con lenguaje ubicuo, entidades, Value Objects, Aggregates y Domain Events.
- Service Layer para coordinar los casos de uso.
- Repository y Unit of Work para la persistencia.
- Commands y Queries (CQRS básico).
- Principios SOLID y decisiones registradas en ADR.

## Estructura del proyecto

```text
EduTech/
├── Diagrams/
│   ├── dominio/
│   │   └── DiagramaDeDominio.pdf
│   └── secuencia/
│       ├── Flujo_cancelacion.pdf
│       └── Flujo_certificado.pdf
├── docs/
│   ├── adr/
│   │   ├── ADR.docx
│   │   └── ADR.pdf
│   ├── bitacora_ia/
│   │   ├── Bitacora_IA_EduTech.docx
│   │   └── Bitacora_IA_EduTech.pdf
│   ├── informe/
│   │   └── ACT3_edutech (1).pdf
│   └── trazabilidad/
│       ├── Trazabilidad_EduTech.docx
│       └── Trazabilidad_EduTech.pdf
└── src/
    ├── __pycache__/
    │   ├── __init__.cpython-314.pyc
    │   └── composicion.cpython-314.pyc
    └── aplicacion/
        ├── __pycache__/
        ├── __init__.py
        ├── abstracciones.py
        ├── comandos.py
        ├── consultas.py
        ├── dtos.py
        ├── handlers.py
        └── servicios.py
        # ... (el resto de carpetas de src/ no es visible en la captura)
```

## Descripción de carpetas y archivos

| Carpeta o archivo | Descripción |
|---|---|
| `Diagrams/` | Contiene los diagramas de dominio y de secuencia del sistema. |
| `Diagrams/dominio/` | Diagrama de dominio (`DiagramaDeDominio.pdf`). |
| `Diagrams/secuencia/` | Flujos de cancelación de curso y de emisión de certificado. |
| `docs/` | Reúne la documentación y las evidencias del proyecto. |
| `docs/adr/` | Contiene las decisiones de arquitectura (ADR). |
| `docs/bitacora_ia/` | Incluye el registro del uso de inteligencia artificial. |
| `docs/informe/` | Contiene el informe de la actividad (`ACT3_edutech`). |
| `docs/trazabilidad/` | Matriz que relaciona necesidades, reglas, historias de usuario, casos de uso, componentes y ADR. |
| `src/` | Contiene el código fuente del sistema. |
| `src/aplicacion/` | Coordina los casos de uso (servicios, comandos, consultas, DTOs y handlers). |
| `src/aplicacion/abstracciones.py` | Interfaces y contratos que usa la capa de aplicación. |
| `src/aplicacion/comandos.py` | Commands que representan operaciones que modifican el estado. |
| `src/aplicacion/consultas.py` | Queries para lectura de información. |
| `src/aplicacion/dtos.py` | Objetos de transferencia de datos. |
| `src/aplicacion/handlers.py` | Manejadores de comandos y consultas. |
| `src/aplicacion/servicios.py` | Servicios de aplicación que orquestan los casos de uso. |
| `src/composicion.py` | Composición e inyección de dependencias del sistema. |
| `__pycache__/` | Archivos compilados de Python generados automáticamente. |
