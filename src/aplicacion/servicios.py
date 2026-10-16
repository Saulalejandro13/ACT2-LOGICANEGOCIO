"""Application Services (Service Layer, ADR-002).
COORDINAN: obtienen aggregates por Repository, invocan el dominio, persisten dentro de un
Unit of Work y publican eventos. NO contienen reglas de negocio (esas viven en dominio/).
"""
from datetime import date
from typing import Optional

from ..dominio.comun import ErrorDeDominio
from ..dominio.entidades import CancelacionCurso, Certificado, Inscripcion, RegistroAcademico
from ..dominio.value_objects import Nota, ReglasConfigurables
from .comandos import (
    CancelarCursoCommand, EmitirCertificadoCommand, RegistrarInscripcionCommand,
    ValidarRequisitosCommand,
)
from .consultas import ConsultarCatalogoHandler, ConsultarCatalogoQuery
from .dtos import CancelacionDTO, CertificadoDTO, InscripcionDTO


class _ServicioBase:
    def __init__(self, uow, bus):
        self._uow, self._bus = uow, bus

    def _publicar(self, *agregados) -> None:
        for agregado in agregados:
            for evento in agregado.extraer_eventos():
                self._bus.publicar(evento)


def _inscripcion_o_error(repo, inscripcion_id):
    inscripcion = repo.find_by_id(inscripcion_id)
    if inscripcion is None:
        raise ErrorDeDominio("Inscripción no encontrada")
    return inscripcion


# ---------------- CU-01 ----------------
class CatalogoService:
    def __init__(self, cursos):
        self._handler = ConsultarCatalogoHandler(cursos)

    def consultar_catalogo(self, query: Optional[ConsultarCatalogoQuery] = None):
        return self._handler.handle(query or ConsultarCatalogoQuery())


# ---------------- CU-02 ----------------
class InscripcionService(_ServicioBase):
    def __init__(self, estudiantes, cursos, inscripciones, uow, bus):
        super().__init__(uow, bus)
        self._estudiantes, self._cursos, self._inscripciones = estudiantes, cursos, inscripciones

    def registrar_inscripcion(self, cmd: RegistrarInscripcionCommand) -> InscripcionDTO:
        with self._uow:
            estudiante = self._estudiantes.find_by_id(cmd.estudiante_id)
            if estudiante is None:
                raise ErrorDeDominio("Estudiante no encontrado")
            curso = self._cursos.find_by_id(cmd.curso_id)
            if curso is None:
                raise ErrorDeDominio("Curso no encontrado")
            curso.ocupar_lugar(cmd.grupo_id)                      # el dominio valida cupo y periodo
            inscripcion = Inscripcion.crear(estudiante.id, curso.id, cmd.grupo_id, curso.precio)
            self._cursos.save(curso)
            self._inscripciones.save(inscripcion)
            self._uow.commit()
        self._publicar(curso, inscripcion)
        return InscripcionDTO(inscripcion.id, estudiante.id, curso.id, cmd.grupo_id,
                              inscripcion.estado.value, inscripcion.pago.estado.value)


# ---------------- CU-03 ----------------
class CursoService(_ServicioBase):
    def __init__(self, cursos, uow, bus):
        super().__init__(uow, bus)
        self._cursos = cursos

    def cerrar_inscripcion(self, curso_id: str) -> None:
        with self._uow:
            curso = self._cursos.find_by_id(curso_id)
            if curso is None:
                raise ErrorDeDominio("Curso no encontrado")
            curso.cerrar_inscripcion()
            self._cursos.save(curso)
            self._uow.commit()
        self._publicar(curso)

    def sustituir_instructor(self, curso_id: str, nuevo_instructor_id: str) -> None:
        with self._uow:
            curso = self._cursos.find_by_id(curso_id)
            if curso is None:
                raise ErrorDeDominio("Curso no encontrado")
            curso.sustituir_instructor(nuevo_instructor_id)
            self._cursos.save(curso)
            self._uow.commit()
        self._publicar(curso)


# ---------------- US-05 ----------------
class PagoService(_ServicioBase):
    def __init__(self, inscripciones, uow, bus, reglas: ReglasConfigurables = ReglasConfigurables()):
        super().__init__(uow, bus)
        self._inscripciones, self._reglas = inscripciones, reglas

    def registrar_pago(self, inscripcion_id: str, fecha: Optional[date] = None) -> None:
        with self._uow:
            inscripcion = _inscripcion_o_error(self._inscripciones, inscripcion_id)
            inscripcion.registrar_pago(fecha or date.today())
            self._inscripciones.save(inscripcion)
            self._uow.commit()
        self._publicar(inscripcion)

    def revisar_pagos_vencidos(self, hoy: Optional[date] = None) -> None:
        with self._uow:
            pendientes = self._inscripciones.pendientes_de_pago()
            for inscripcion in pendientes:
                inscripcion.verificar_plazo_de_pago(hoy or date.today(), self._reglas.plazo_pago_dias)
                self._inscripciones.save(inscripcion)
            self._uow.commit()
        self._publicar(*pendientes)


# ---------------- CU-04 ----------------
class AcademicoService(_ServicioBase):
    def __init__(self, registros, inscripciones, uow, bus):
        super().__init__(uow, bus)
        self._registros, self._inscripciones = registros, inscripciones

    def _registro(self, inscripcion_id: str) -> RegistroAcademico:
        _inscripcion_o_error(self._inscripciones, inscripcion_id)
        return (self._registros.find_by_inscripcion(inscripcion_id)
                or RegistroAcademico(inscripcion_id))

    def registrar_asistencia(self, inscripcion_id: str, presente: bool) -> None:
        with self._uow:
            registro = self._registro(inscripcion_id)
            registro.registrar_asistencia(presente)
            self._registros.save(registro)
            self._uow.commit()
        self._publicar(registro)

    def registrar_calificacion(self, inscripcion_id: str, evaluacion_id: str, nota: float) -> None:
        with self._uow:
            registro = self._registro(inscripcion_id)
            registro.registrar_calificacion(evaluacion_id, Nota(nota))
            self._registros.save(registro)
            self._uow.commit()
        self._publicar(registro)

    def modificar_calificacion(self, inscripcion_id: str, evaluacion_id: str, nota: float,
                               motivo: str, autorizado_por: Optional[str]) -> None:
        with self._uow:
            registro = self._registro(inscripcion_id)
            registro.modificar_calificacion(evaluacion_id, Nota(nota), motivo, autorizado_por)
            self._registros.save(registro)
            self._uow.commit()
        self._publicar(registro)


# ---------------- CU-05 ----------------
class CertificacionService(_ServicioBase):
    def __init__(self, inscripciones, registros, certificados, cursos, uow, bus,
                 reglas: ReglasConfigurables = ReglasConfigurables()):
        super().__init__(uow, bus)
        self._inscripciones, self._registros = inscripciones, registros
        self._certificados, self._cursos, self._reglas = certificados, cursos, reglas

    def validar_requisitos(self, cmd: ValidarRequisitosCommand) -> CertificadoDTO:
        with self._uow:
            inscripcion = _inscripcion_o_error(self._inscripciones, cmd.inscripcion_id)
            registro = self._registros.find_by_inscripcion(cmd.inscripcion_id)
            if registro is None:
                raise ErrorDeDominio("La inscripción no tiene registro académico")
            curso = self._cursos.find_by_id(inscripcion.curso_id)
            certificado = (self._certificados.find_by_inscripcion(cmd.inscripcion_id)
                           or Certificado(cmd.inscripcion_id))
            certificado.validar_requisitos(
                nota=registro.promedio(),
                asistencia=registro.porcentaje_asistencia(),
                curso_concluido=curso.ha_concluido(),
                pago_regularizado=inscripcion.pago_regularizado(),
                asistencia_minima=self._reglas.asistencia_minima,
            )
            self._certificados.save(certificado)
            self._uow.commit()
        self._publicar(certificado)
        return CertificadoDTO(cmd.inscripcion_id, certificado.estado, certificado.motivo)

    def emitir_certificado(self, cmd: EmitirCertificadoCommand) -> CertificadoDTO:
        with self._uow:
            certificado = self._certificados.find_by_inscripcion(cmd.inscripcion_id)
            if certificado is None:
                raise ErrorDeDominio("Estudiante no apto para certificación: requisitos no validados")
            certificado.emitir()                                   # el dominio exige estado Apto
            self._certificados.save(certificado)
            self._uow.commit()
        self._publicar(certificado)
        return CertificadoDTO(cmd.inscripcion_id, certificado.estado)


# ---------------- EX-01 ----------------
class CancelacionService(_ServicioBase):
    def __init__(self, cursos, inscripciones, cancelaciones, uow, bus):
        super().__init__(uow, bus)
        self._cursos, self._inscripciones, self._cancelaciones = cursos, inscripciones, cancelaciones

    def cancelar_curso(self, curso_id: str, motivo: str, autorizado_por: str) -> CancelacionDTO:
        with self._uow:
            curso = self._cursos.find_by_id(curso_id)
            if curso is None:
                raise ErrorDeDominio("Curso no encontrado")
            curso.cancelar()
            afectadas = [i.id for i in self._inscripciones.find_by_curso(curso_id)]
            cancelacion = CancelacionCurso.registrar(curso_id, motivo, autorizado_por, afectadas)
            self._cursos.save(curso)
            self._cancelaciones.save(cancelacion)
            self._uow.commit()
        self._publicar(curso, cancelacion)
        return CancelacionDTO(curso_id, [c.inscripcion_id for c in cancelacion.casos])
