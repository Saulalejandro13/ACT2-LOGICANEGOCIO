"""Pruebas de la Service Layer / CQRS con dobles en memoria (ADR-002, ADR-003, ADR-009).
Los servicios solo COORDINAN: las reglas ya se prueban en test_dominio.py.
"""
from datetime import date

import pytest

from edutech.aplicacion.comandos import (
    EmitirCertificadoCommand, RegistrarInscripcionCommand, ValidarRequisitosCommand,
)
from edutech.aplicacion.consultas import (
    ConsultarCatalogoQuery, ConsultarPagosPendientesHandler, ConsultarPagosPendientesQuery,
)
from edutech.aplicacion.servicios import (
    CancelacionService, CatalogoService, CertificacionService, InscripcionService,
)
from edutech.dominio.entidades import Curso, Estudiante, RegistroAcademico
from edutech.dominio.enumeraciones import EstadoCertificacion
from edutech.dominio.value_objects import CalendarioCurso, Dinero, Nota, ReglasConfigurables

from tests.fakes import (
    CancelacionRepositoryMemoria, CertificadoRepositoryMemoria, CursoRepositoryMemoria,
    EstudianteRepositoryMemoria, FakeEventBus, FakeUnitOfWork, InscripcionRepositoryMemoria,
    RegistroAcademicoRepositoryMemoria,
)

# Regla PENDIENTE (ADR-008): se inyecta como configuracion.
REGLAS = ReglasConfigurables(asistencia_minima=80, plazo_pago_dias=7)


@pytest.fixture
def ctx():
    cursos, inscripciones, estudiantes = (
        CursoRepositoryMemoria(), InscripcionRepositoryMemoria(), EstudianteRepositoryMemoria())
    curso = Curso(id="C1", nombre="Python", instructor_id="I1", precio=Dinero(1500, "MXN"),
                  calendario=CalendarioCurso(date(2026, 1, 1), date(2026, 2, 1)))  # ya concluido
    curso.agregar_grupo(grupo_id="G1")
    cursos.save(curso)
    estudiantes.save(Estudiante(id="E1", nombre="Ana"))
    return dict(cursos=cursos, inscripciones=inscripciones, estudiantes=estudiantes,
                registros=RegistroAcademicoRepositoryMemoria(),
                certificados=CertificadoRepositoryMemoria(),
                cancelaciones=CancelacionRepositoryMemoria(),
                uow=FakeUnitOfWork(), bus=FakeEventBus())


@pytest.fixture
def inscripcion_service(ctx):
    return InscripcionService(ctx["estudiantes"], ctx["cursos"], ctx["inscripciones"],
                              ctx["uow"], ctx["bus"])


# ---------- CU-02 Inscripcion ----------
class TestRegistrarInscripcion:
    def test_flujo_normal_crea_inscripcion_con_pago_pendiente(self, inscripcion_service, ctx):
        cmd = RegistrarInscripcionCommand(estudiante_id="E1", curso_id="C1", grupo_id="G1")
        resultado = inscripcion_service.registrar_inscripcion(cmd)
        guardada = ctx["inscripciones"].find_by_id(resultado.id)
        assert guardada.pago.esta_pendiente()
        assert ctx["uow"].confirmado

    def test_publica_evento_inscripcion_realizada(self, inscripcion_service, ctx):
        inscripcion_service.registrar_inscripcion(RegistrarInscripcionCommand("E1", "C1", "G1"))
        assert "InscripcionRealizada" in ctx["bus"].tipos()

    def test_ocupa_un_lugar_del_grupo(self, inscripcion_service, ctx):
        inscripcion_service.registrar_inscripcion(RegistrarInscripcionCommand("E1", "C1", "G1"))
        assert ctx["cursos"].find_by_id("C1").lugares_ocupados("G1") == 1

    def test_flujo_de_rechazo_sin_cupo_revierte_todo(self, inscripcion_service, ctx):
        curso = ctx["cursos"].find_by_id("C1")
        for _ in range(25):
            curso.ocupar_lugar("G1")
        with pytest.raises(Exception, match="(?i)sin cupo"):
            inscripcion_service.registrar_inscripcion(RegistrarInscripcionCommand("E1", "C1", "G1"))
        assert ctx["uow"].revertido and not ctx["uow"].confirmado
        assert ctx["inscripciones"].find_by_estudiante("E1") == []

    def test_estudiante_inexistente_se_rechaza(self, inscripcion_service):
        with pytest.raises(Exception, match="(?i)no encontrado"):
            inscripcion_service.registrar_inscripcion(
                RegistrarInscripcionCommand("NOEXISTE", "C1", "G1"))


# ---------- CU-05 Certificacion ----------
class TestCertificacion:
    @pytest.fixture
    def servicio(self, ctx):
        return CertificacionService(ctx["inscripciones"], ctx["registros"], ctx["certificados"],
                                    ctx["cursos"], ctx["uow"], ctx["bus"], REGLAS)

    def _preparar(self, ctx, inscripcion_service, pagado=True, asistencias=10):
        dto = inscripcion_service.registrar_inscripcion(RegistrarInscripcionCommand("E1", "C1", "G1"))
        if pagado:
            ctx["inscripciones"].find_by_id(dto.id).registrar_pago(fecha=date.today())
        registro = RegistroAcademico(inscripcion_id=dto.id)
        for _ in range(asistencias):
            registro.registrar_asistencia(presente=True)
        registro.registrar_calificacion("EV1", Nota(90))
        ctx["registros"].save(registro)
        return dto.id

    def test_validar_estudiante_que_cumple_queda_apto(self, servicio, ctx, inscripcion_service):
        id_ = self._preparar(ctx, inscripcion_service)
        dto = servicio.validar_requisitos(ValidarRequisitosCommand(id_))
        assert dto.estado == EstadoCertificacion.APTO
        assert "EstudianteMarcadoApto" in ctx["bus"].tipos()

    def test_validar_con_pago_pendiente_queda_no_certificado(self, servicio, ctx, inscripcion_service):
        id_ = self._preparar(ctx, inscripcion_service, pagado=False)
        dto = servicio.validar_requisitos(ValidarRequisitosCommand(id_))
        assert dto.estado == EstadoCertificacion.NO_CERTIFICADO
        assert "pago" in dto.motivo.lower()

    def test_validar_sin_asistencia_minima_definida_se_rechaza(self, ctx, inscripcion_service):
        sin_regla = CertificacionService(ctx["inscripciones"], ctx["registros"], ctx["certificados"],
                                         ctx["cursos"], ctx["uow"], ctx["bus"], ReglasConfigurables())
        id_ = self._preparar(ctx, inscripcion_service)
        with pytest.raises(Exception, match="(?i)no ha sido definida"):
            sin_regla.validar_requisitos(ValidarRequisitosCommand(id_))

    def test_emitir_despues_de_validar_emite_certificado(self, servicio, ctx, inscripcion_service):
        id_ = self._preparar(ctx, inscripcion_service)
        servicio.validar_requisitos(ValidarRequisitosCommand(id_))
        dto = servicio.emitir_certificado(EmitirCertificadoCommand(id_))
        assert dto.estado == EstadoCertificacion.CERTIFICADO
        assert "CertificadoEmitido" in ctx["bus"].tipos()

    def test_emitir_certificado_de_estudiante_no_apto_se_rechaza(self, servicio, ctx, inscripcion_service):
        id_ = self._preparar(ctx, inscripcion_service, pagado=False)
        servicio.validar_requisitos(ValidarRequisitosCommand(id_))
        with pytest.raises(Exception, match="(?i)no apto"):
            servicio.emitir_certificado(EmitirCertificadoCommand(id_))
        assert ctx["uow"].revertido
        assert "CertificadoEmitido" not in ctx["bus"].tipos()

    def test_emitir_sin_validar_se_rechaza(self, servicio, ctx):
        with pytest.raises(Exception, match="(?i)no apto"):
            servicio.emitir_certificado(EmitirCertificadoCommand("N1"))
        assert ctx["uow"].revertido


# ---------- Flujo EX-01 Cancelacion ----------
class TestCancelacion:
    def test_cancelar_curso_genera_un_caso_de_resolucion_por_inscrito(self, ctx, inscripcion_service):
        inscripcion_service.registrar_inscripcion(RegistrarInscripcionCommand("E1", "C1", "G1"))
        servicio = CancelacionService(ctx["cursos"], ctx["inscripciones"], ctx["cancelaciones"],
                                      ctx["uow"], ctx["bus"])
        cancelacion = servicio.cancelar_curso("C1", motivo="Cupo minimo no alcanzado",
                                              autorizado_por="ADM1")
        assert len(cancelacion.casos) == 1
        assert "CursoCancelado" in ctx["bus"].tipos()
        assert ctx["uow"].confirmado

    def test_cancelar_sin_quien_autoriza_se_rechaza(self, ctx):
        servicio = CancelacionService(ctx["cursos"], ctx["inscripciones"], ctx["cancelaciones"],
                                      ctx["uow"], ctx["bus"])
        with pytest.raises(Exception, match="(?i)autoriza"):
            servicio.cancelar_curso("C1", motivo="Cupo minimo", autorizado_por="")
        assert ctx["uow"].revertido


# ---------- Queries (CQRS, solo lectura) ----------
class TestQueries:
    def test_consultar_catalogo_devuelve_dto_y_no_modifica_estado(self, ctx):
        antes = ctx["cursos"].find_by_id("C1").estado
        resultado = CatalogoService(ctx["cursos"]).consultar_catalogo(ConsultarCatalogoQuery())
        assert resultado[0].nombre == "Python"
        assert not hasattr(resultado[0], "ocupar_lugar")  # DTO, no el aggregate
        assert ctx["cursos"].find_by_id("C1").estado == antes
        assert not ctx["uow"].confirmado

    def test_pagos_pendientes_lista_inscripciones_sin_pagar(self, ctx, inscripcion_service):
        inscripcion_service.registrar_inscripcion(RegistrarInscripcionCommand("E1", "C1", "G1"))
        lista = ConsultarPagosPendientesHandler(ctx["inscripciones"]).handle(
            ConsultarPagosPendientesQuery())
        assert len(lista) == 1 and lista[0].estudiante_id == "E1"
