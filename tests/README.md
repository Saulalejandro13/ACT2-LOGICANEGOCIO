# Pruebas – EduTech Academy

Estructura (igual que `tests/` del repo de referencia):

| Archivo | Qué prueba |
|---|---|
| `test_dominio.py` | Reglas del Domain Model: Nota 70, Cupo 5–25, Inscripción/Pago, RegistroAcademico, Certificado, Cambio de grupo, Bitácora inmutable |
| `test_aplicacion.py` | Service Layer + CQRS con dobles en memoria (commit / rollback, eventos publicados) |
| `prueba_arquitectura.py` | Regla de dependencias entre capas y eventos en pasado (funciona sin ajustes) |
| `fakes.py` | Repositorios, UnitOfWork y EventBus en memoria (dobles de prueba) |
| `escenarios/escenarios.feature` | Escenarios Gherkin 1.1, 1.2, 2.1, 3.1, 3.2 |

Ejecutar desde la raíz del repo: `pip install pytest && pytest tests/ -v`

Nota: la asistencia mínima, el plazo de pago y otras reglas "por definir" (ADR-008) se pasan como
parámetros en las pruebas; no hay valores fijos en el dominio.
