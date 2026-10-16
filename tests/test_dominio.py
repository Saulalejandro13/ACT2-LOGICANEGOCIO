"""Pruebas del Domain Model de EduTech Academy (sin base de datos).
Trazabilidad: BR-03/US-04 (cupo), US-08 (nota), US-05 (pago), US-07/09 (registro
academico), US-10/11 (certificacion), US-12 (cancelacion), US-17 (instructor), RNF-03.
AJUSTAR imports/firmas a src/edutech/dominio/ si difieren.
"""
from datetime import date, timedelta

import pytest

from edutech.dominio.entidades import (
    Bitacora, Certificado, Curso, Inscripcion, RegistroAcademico, SolicitudCambioGrupo,
)
from edutech.dominio.enumeraciones import (
    EstadoCertificacion, EstadoCurso, EstadoInscripcion, EstadoPago, EstadoSolicitud,
)
from edutech.dominio.value_objects import Cupo, Dinero, Nota, PorcentajeAsistencia

# Regla PENDIENTE (ADR-008): se inyecta, no se fija en el codigo del dominio.
ASISTENCIA_MINIMA = 80


@pytest.fixture
def curso():
    c = Curso(id="C1", nombre="Python", instructor_id="I1", precio=Dinero(1500, "MXN"))
    c.agregar_grupo(grupo_id="G1")
    return c


# ---------------- Value Objects ----------------
class TestNota:
    @pytest.mark.parametrize("valor,aprueba", [(69, False), (70, True), (100, True), (0, False)])
    def test_nota_minima_aprobatoria_es_70(self, valor, aprueba):
        assert Nota(valor).aprueba() is aprueba

    @pytest.mark.parametrize("invalida", [-1, 101])
    def test_nota_fuera_de_rango_se_rechaza(self, invalida):
        with pytest.raises(ValueError):
            Nota(invalida)


class TestCupo:
    def test_cupo_nuevo_tiene_limites_5_y_25(self):
        c = Cupo()
        assert (c.minimo, c.maximo, c.ocupados) == (5, 25, 0)

    def test_ocupar_lugar_reduce_restantes(self):
        assert Cupo().ocupar().restantes == 24

    def test_no_se_puede_superar_el_maximo(self):
        c = Cupo(ocupados=25)
        with pytest.raises(Exception, match="(?i)sin cupo"):
            c.ocupar()

    def test_cupo_es_inmutable(self):
        c = Cupo()
        c.ocupar()
        assert c.ocupados == 0  # ocupar() devuelve un Cupo nuevo

    def test_igualdad_por_valor(self):
        assert Cupo(ocupados=3) == Cupo(ocupados=3)


class TestPorcentajeAsistencia:
    def test_calculo(self):
        assert PorcentajeAsistencia(asistidas=8, total=10).valor == 80

    def test_cumple_segun_minimo_configurable(self):
        p = PorcentajeAsistencia(asistidas=7, total=10)
        assert p.cumple(minimo=70) and not p.cumple(minimo=80)


class TestDinero:
    def test_igualdad_por_valor(self):
        assert Dinero(500, "MXN") == Dinero(500, "MXN")

    def test_monto_negativo_falla(self):
        with pytest.raises(ValueError):
            Dinero(-1, "MXN")


# ---------------- Aggregate Curso ----------------
class TestCurso:
    def test_curso_nuevo_esta_disponible(self, curso):
        assert curso.estado == EstadoCurso.DISPONIBLE

    def test_al_llegar_a_25_el_curso_queda_sin_cupo_disponible(self, curso):
        for _ in range(25):
            curso.ocupar_lugar("G1")
        assert curso.estado == EstadoCurso.SIN_CUPO_DISPONIBLE

    def test_inscribir_en_grupo_lleno_se_rechaza(self, curso):
        for _ in range(25):
            curso.ocupar_lugar("G1")
        with pytest.raises(Exception, match="(?i)sin cupo"):
            curso.ocupar_lugar("G1")

    def test_cerrar_inscripcion_bajo_minimo_emite_evento(self, curso):
        for _ in range(4):
            curso.ocupar_lugar("G1")
        curso.cerrar_inscripcion()
        nombres = [type(e).__name__ for e in curso.eventos]
        assert "InscripcionCerradaSinCupoMinimo" in nombres

    def test_cancelar_curso_cambia_estado(self, curso):
        curso.cancelar()
        assert curso.estado == EstadoCurso.CANCELADO

    def test_no_se_inscribe_en_curso_cancelado(self, curso):
        curso.cancelar()
        with pytest.raises(Exception):
            curso.ocupar_lugar("G1")

    def test_sustituir_instructor_emite_evento(self, curso):
        curso.sustituir_instructor("I2")
        assert curso.instructor_id == "I2"
        assert "InstructorSustituido" in [type(e).__name__ for e in curso.eventos]


# ---------------- Aggregate Inscripcion ----------------
class TestInscripcion:
    def test_nueva_inscripcion_genera_pago_pendiente(self):
        i = Inscripcion.crear("E1", "C1", "G1", Dinero(1500, "MXN"))
        assert i.estado == EstadoInscripcion.INSCRITO
        assert i.pago.estado == EstadoPago.PENDIENTE
        assert "InscripcionRealizada" in [type(e).__name__ for e in i.eventos]

    def test_registrar_pago_marca_pagado(self):
        i = Inscripcion.crear("E1", "C1", "G1", Dinero(1500, "MXN"))
        i.registrar_pago(fecha=date.today())
        assert i.pago.estado == EstadoPago.PAGADO
        assert "PagoRegistrado" in [type(e).__name__ for e in i.eventos]

    def test_no_se_paga_dos_veces(self):
        i = Inscripcion.crear("E1", "C1", "G1", Dinero(1500, "MXN"))
        i.registrar_pago(fecha=date.today())
        with pytest.raises(Exception):
            i.registrar_pago(fecha=date.today())

    def test_plazo_vencido_emite_evento(self):
        i = Inscripcion.crear("E1", "C1", "G1", Dinero(1500, "MXN"))
        i.verificar_plazo_de_pago(hoy=date.today() + timedelta(days=30), plazo_dias=7)
        assert "PlazoDePagoVencido" in [type(e).__name__ for e in i.eventos]


# ---------------- Aggregate RegistroAcademico ----------------
class TestRegistroAcademico:
    def test_calcula_porcentaje_de_asistencia(self):
        r = RegistroAcademico(inscripcion_id="N1")
        for presente in (True, True, True, False):
            r.registrar_asistencia(presente=presente)
        assert r.porcentaje_asistencia().valor == 75

    def test_modificar_calificacion_exige_motivo_y_autorizacion(self):
        r = RegistroAcademico(inscripcion_id="N1")
        r.registrar_calificacion("EV1", Nota(60))
        with pytest.raises(Exception):
            r.modificar_calificacion("EV1", Nota(80), motivo="", autorizado_por=None)

    def test_modificar_calificacion_conserva_historial(self):
        r = RegistroAcademico(inscripcion_id="N1")
        r.registrar_calificacion("EV1", Nota(60))
        r.modificar_calificacion("EV1", Nota(80), motivo="Error de captura", autorizado_por="CE1")
        evento = [e for e in r.eventos if type(e).__name__ == "CalificacionModificada"][0]
        assert (evento.valor_anterior, evento.valor_nuevo) == (60, 80)


# ---------------- Aggregate Certificado ----------------
class TestCertificado:
    def _validar(self, **kw):
        datos = dict(nota=Nota(85), asistencia=PorcentajeAsistencia(9, 10),
                     curso_concluido=True, pago_regularizado=True,
                     asistencia_minima=ASISTENCIA_MINIMA)
        datos.update(kw)
        c = Certificado(inscripcion_id="N1")
        c.validar_requisitos(**datos)
        return c

    def test_cumple_los_cuatro_requisitos_queda_apto(self):
        assert self._validar().estado == EstadoCertificacion.APTO

    @pytest.mark.parametrize("falla,motivo", [
        ({"nota": Nota(69)}, "calific"),
        ({"asistencia": PorcentajeAsistencia(5, 10)}, "asistencia"),
        ({"curso_concluido": False}, "concluido"),
        ({"pago_regularizado": False}, "pago"),
    ])
    def test_si_falla_un_requisito_queda_no_certificado_con_motivo(self, falla, motivo):
        c = self._validar(**falla)
        assert c.estado == EstadoCertificacion.NO_CERTIFICADO
        assert motivo in c.motivo.lower()

    def test_emitir_solo_si_es_apto(self):
        c = self._validar(pago_regularizado=False)
        with pytest.raises(Exception, match="(?i)no apto"):
            c.emitir()

    def test_emitir_certificado_apto(self):
        c = self._validar()
        c.emitir()
        assert c.estado == EstadoCertificacion.CERTIFICADO
        assert "CertificadoEmitido" in [type(e).__name__ for e in c.eventos]


# ---------------- Cambio de grupo ----------------
class TestSolicitudCambioGrupo:
    def test_nace_pendiente_de_autorizacion(self):
        s = SolicitudCambioGrupo(inscripcion_id="N1", grupo_destino="G2")
        assert s.estado == EstadoSolicitud.PENDIENTE

    def test_autorizar_y_rechazar(self):
        a = SolicitudCambioGrupo(inscripcion_id="N1", grupo_destino="G2")
        a.autorizar(por="CE1")
        assert a.estado == EstadoSolicitud.AUTORIZADA
        r = SolicitudCambioGrupo(inscripcion_id="N2", grupo_destino="G2")
        r.rechazar(por="CE1")
        assert r.estado == EstadoSolicitud.RECHAZADA

    def test_no_se_autoriza_dos_veces(self):
        s = SolicitudCambioGrupo(inscripcion_id="N1", grupo_destino="G2")
        s.autorizar(por="CE1")
        with pytest.raises(Exception):
            s.autorizar(por="CE1")


# ---------------- Bitacora inmutable (RNF-03 / ADR-007) ----------------
class TestBitacora:
    def test_registro_guarda_quien_que_cuando_anterior_nuevo_y_autorizo(self):
        b = Bitacora()
        b.registrar(quien="I1", que="Calificacion", anterior=60, nuevo=80, autorizo="CE1")
        reg = b.registros[0]
        assert (reg.quien, reg.anterior, reg.nuevo, reg.autorizo) == ("I1", 60, 80, "CE1")

    def test_registro_no_se_puede_modificar(self):
        b = Bitacora()
        b.registrar(quien="I1", que="Calificacion", anterior=60, nuevo=80, autorizo="CE1")
        with pytest.raises(Exception):  # dataclass(frozen=True) -> FrozenInstanceError
            b.registros[0].nuevo = 100
