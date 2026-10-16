"""Demostración del flujo principal de EduTech Academy (CU-02 -> CU-04 -> CU-05 y EX-01).
Ejecutar:  python main.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from edutech.aplicacion.comandos import (  # noqa: E402
    EmitirCertificadoCommand, RegistrarInscripcionCommand, ValidarRequisitosCommand,
)
from edutech.composicion import construir_sistema  # noqa: E402
from edutech.dominio.entidades import Curso, Estudiante  # noqa: E402
from edutech.dominio.value_objects import CalendarioCurso, Dinero, ReglasConfigurables  # noqa: E402


def main():
    # Reglas POR DEFINIR por EduTech (ADR-008): se configuran aquí, no en el dominio.
    s = construir_sistema(ReglasConfigurables(asistencia_minima=80, plazo_pago_dias=7))

    curso = Curso("PY-101", "Python", "I1", Dinero(1500, "MXN"),
                  calendario=CalendarioCurso(date(2026, 1, 5), date(2026, 2, 5)))
    curso.agregar_grupo("G1")
    s.cursos.save(curso)
    s.estudiantes.save(Estudiante("E1", "Ana"))

    print("== CU-01 Catálogo ==")
    for c in s.catalogo.consultar_catalogo():
        print(f"  {c.nombre} ({c.modalidad}) - {c.estado}")

    print("== CU-02 Inscripción ==")
    insc = s.inscripcion.registrar_inscripcion(RegistrarInscripcionCommand("E1", "PY-101", "G1"))
    print(f"  Inscripción {insc.id}: {insc.estado}, pago {insc.estado_pago}")

    print("== Pago + CU-04 Registro académico ==")
    s.pagos.registrar_pago(insc.id)
    for _ in range(10):
        s.academico.registrar_asistencia(insc.id, presente=True)
    s.academico.registrar_calificacion(insc.id, "EV1", 65)
    s.academico.modificar_calificacion(insc.id, "EV1", 85, motivo="Error de captura",
                                       autorizado_por="Control Escolar")

    print("== CU-05 Certificación ==")
    r = s.certificacion.validar_requisitos(ValidarRequisitosCommand(insc.id))
    print(f"  Resultado: {r.estado.value}")
    r = s.certificacion.emitir_certificado(EmitirCertificadoCommand(insc.id))
    print(f"  Resultado: {r.estado.value}")

    print("== Rechazo: inscripción sin cupo ==")
    s.cursos.find_by_id("PY-101")  # mismo aggregate
    for i in range(24):
        s.estudiantes.save(Estudiante(f"X{i}", f"Est{i}"))
        s.inscripcion.registrar_inscripcion(RegistrarInscripcionCommand(f"X{i}", "PY-101", "G1"))
    try:
        s.estudiantes.save(Estudiante("X99", "Extra"))
        s.inscripcion.registrar_inscripcion(RegistrarInscripcionCommand("X99", "PY-101", "G1"))
    except Exception as e:
        print(f"  Rechazado: {e}")

    print("== EX-01 Cancelación ==")
    c = s.cancelacion.cancelar_curso("PY-101", "Reestructura del programa", "Administración")
    print(f"  Casos de resolución generados: {len(c.casos)}")

    print("== Bitácora (RNF-03) ==")
    for reg in s.bitacora.registros:
        print(f"  {reg.que}: {reg.anterior} -> {reg.nuevo} (autorizó: {reg.autorizo})")

    print("== Eventos publicados ==")
    print("  " + ", ".join(sorted({type(e).__name__ for e in s.bus.historial})))


if __name__ == "__main__":
    main()
