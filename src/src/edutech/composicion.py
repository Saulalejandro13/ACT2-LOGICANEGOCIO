"""Composition root: único lugar que conoce las implementaciones concretas y las conecta."""
from dataclasses import dataclass

from .aplicacion.servicios import (
    AcademicoService, CancelacionService, CatalogoService, CertificacionService,
    CursoService, InscripcionService, PagoService,
)
from .dominio import eventos as ev
from .dominio.entidades import Bitacora
from .dominio.value_objects import ReglasConfigurables
from .infraestructura.persistencia import (
    CancelacionRepositoryMemoria, CertificadoRepositoryMemoria, CursoRepositoryMemoria,
    EstudianteRepositoryMemoria, InscripcionRepositoryMemoria, RegistroAcademicoRepositoryMemoria,
)
from .infraestructura.servicios import EventBusSincrono, UnitOfWorkMemoria


@dataclass
class Sistema:
    cursos: object
    estudiantes: object
    inscripciones: object
    bitacora: Bitacora
    bus: EventBusSincrono
    catalogo: CatalogoService
    inscripcion: InscripcionService
    curso: CursoService
    pagos: PagoService
    academico: AcademicoService
    certificacion: CertificacionService
    cancelacion: CancelacionService


def construir_sistema(reglas: ReglasConfigurables = ReglasConfigurables()) -> Sistema:
    cursos, estudiantes = CursoRepositoryMemoria(), EstudianteRepositoryMemoria()
    inscripciones, registros = InscripcionRepositoryMemoria(), RegistroAcademicoRepositoryMemoria()
    certificados, cancelaciones = CertificadoRepositoryMemoria(), CancelacionRepositoryMemoria()
    uow, bus, bitacora = UnitOfWorkMemoria(), EventBusSincrono(), Bitacora()

    # La Bitácora (RNF-03 / ADR-007) reacciona a los eventos relevantes sin acoplar a los aggregates.
    bus.suscribir(ev.CalificacionModificada, lambda e: bitacora.registrar(
        quien="Control Escolar", que=f"Calificación {e.evaluacion_id}",
        anterior=e.valor_anterior, nuevo=e.valor_nuevo, autorizo=e.autorizado_por))
    bus.suscribir(ev.InstructorSustituido, lambda e: bitacora.registrar(
        quien="Administración", que=f"Instructor del curso {e.curso_id}",
        anterior=e.instructor_anterior, nuevo=e.instructor_nuevo, autorizo="Administración"))
    bus.suscribir(ev.CursoCancelado, lambda e: bitacora.registrar(
        quien=e.autorizado_por, que=f"Cancelación del curso {e.curso_id}",
        anterior="Activo", nuevo="Cancelado", autorizo=e.autorizado_por))

    return Sistema(
        cursos=cursos, estudiantes=estudiantes, inscripciones=inscripciones, bitacora=bitacora, bus=bus,
        catalogo=CatalogoService(cursos),
        inscripcion=InscripcionService(estudiantes, cursos, inscripciones, uow, bus),
        curso=CursoService(cursos, uow, bus),
        pagos=PagoService(inscripciones, uow, bus, reglas),
        academico=AcademicoService(registros, inscripciones, uow, bus),
        certificacion=CertificacionService(inscripciones, registros, certificados, cursos, uow, bus, reglas),
        cancelacion=CancelacionService(cursos, inscripciones, cancelaciones, uow, bus),
    )
