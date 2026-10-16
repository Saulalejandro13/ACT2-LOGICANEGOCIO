"""Aggregates, entidades y reglas de negocio de EduTech Academy (ADR-001, ADR-004).
Cada raíz protege sus invariantes y referencia a otros aggregates solo por ID.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from . import eventos as ev
from .comun import AggregateRoot, ErrorDeDominio, nuevo_id
from .enumeraciones import (
    EstadoCaso, EstadoCertificacion, EstadoCurso, EstadoInscripcion, EstadoPago,
    EstadoSolicitud, Modalidad, TipoEvaluacion,
)
from .value_objects import (
    CalendarioCurso, Cupo, Dinero, Nota, PeriodoInscripcion, PorcentajeAsistencia,
)


# ======================= Aggregate Curso =======================
class Grupo:
    """Entidad interna de Curso: solo se modifica a través de su raíz."""

    def __init__(self, id: str, cupo: Optional[Cupo] = None):
        self.id = id
        self.cupo = cupo or Cupo()


class Evaluacion:
    def __init__(self, id: str, tipo: TipoEvaluacion, fecha: Optional[date] = None):
        self.id, self.tipo, self.fecha = id, tipo, fecha


class Curso(AggregateRoot):
    def __init__(self, id: str, nombre: str, instructor_id: str, precio: Dinero,
                 modalidad: Modalidad = Modalidad.PRESENCIAL,
                 calendario: Optional[CalendarioCurso] = None,
                 periodo_inscripcion: Optional[PeriodoInscripcion] = None):
        super().__init__()
        self.id, self.nombre, self.instructor_id, self.precio = id, nombre, instructor_id, precio
        self.modalidad, self.calendario = modalidad, calendario
        self.periodo_inscripcion = periodo_inscripcion
        self.estado = EstadoCurso.DISPONIBLE
        self.inscripcion_cerrada = False
        self.en_revision = False
        self._grupos: dict[str, Grupo] = {}
        self._evaluaciones: dict[str, Evaluacion] = {}

    # --- composición ---
    def agregar_grupo(self, grupo_id: str) -> Grupo:
        if grupo_id in self._grupos:
            raise ErrorDeDominio("El grupo ya existe en el curso")
        self._grupos[grupo_id] = Grupo(grupo_id)
        return self._grupos[grupo_id]

    def agregar_evaluacion(self, evaluacion_id: str, tipo: TipoEvaluacion, fecha=None) -> Evaluacion:
        self._evaluaciones[evaluacion_id] = Evaluacion(evaluacion_id, tipo, fecha)
        return self._evaluaciones[evaluacion_id]

    def _grupo(self, grupo_id: str) -> Grupo:
        if grupo_id not in self._grupos:
            raise ErrorDeDominio("Grupo no encontrado")
        return self._grupos[grupo_id]

    # --- cupo ---
    def ocupar_lugar(self, grupo_id: str, hoy: Optional[date] = None) -> None:
        if self.estado == EstadoCurso.CANCELADO:
            raise ErrorDeDominio("Curso cancelado")
        if self.inscripcion_cerrada:
            raise ErrorDeDominio("Inscripción cerrada")
        if self.periodo_inscripcion and not self.periodo_inscripcion.esta_abierto(hoy or date.today()):
            raise ErrorDeDominio("Fuera del periodo de inscripción")
        grupo = self._grupo(grupo_id)
        grupo.cupo = grupo.cupo.ocupar()
        if grupo.cupo.esta_lleno:
            self._emitir(ev.CupoMaximoAlcanzado(self.id, grupo_id))
        self._actualizar_estado()

    def liberar_lugar(self, grupo_id: str) -> None:
        grupo = self._grupo(grupo_id)
        grupo.cupo = grupo.cupo.liberar()
        self._actualizar_estado()

    def lugares_ocupados(self, grupo_id: str) -> int:
        return self._grupo(grupo_id).cupo.ocupados

    @property
    def total_inscritos(self) -> int:
        return sum(g.cupo.ocupados for g in self._grupos.values())

    def _actualizar_estado(self) -> None:
        if self.estado in (EstadoCurso.DISPONIBLE, EstadoCurso.SIN_CUPO_DISPONIBLE):
            todos_llenos = bool(self._grupos) and all(g.cupo.esta_lleno for g in self._grupos.values())
            self.estado = EstadoCurso.SIN_CUPO_DISPONIBLE if todos_llenos else EstadoCurso.DISPONIBLE

    def cerrar_inscripcion(self) -> None:
        """Qué ocurre si no se alcanza el cupo mínimo está POR DEFINIR: se marca para revisión."""
        self.inscripcion_cerrada = True
        if any(not g.cupo.alcanza_minimo for g in self._grupos.values()):
            self.en_revision = True
            self._emitir(ev.InscripcionCerradaSinCupoMinimo(self.id, self.total_inscritos))

    # --- ciclo de vida ---
    def cancelar(self) -> None:
        if self.estado == EstadoCurso.CANCELADO:
            raise ErrorDeDominio("El curso ya está cancelado")
        self.estado = EstadoCurso.CANCELADO

    def sustituir_instructor(self, nuevo_instructor_id: str) -> None:
        if nuevo_instructor_id == self.instructor_id:
            raise ErrorDeDominio("El instructor sustituto debe ser distinto")
        anterior, self.instructor_id = self.instructor_id, nuevo_instructor_id
        self._emitir(ev.InstructorSustituido(self.id, anterior, nuevo_instructor_id))

    def ha_concluido(self, hoy: Optional[date] = None) -> bool:
        return bool(self.calendario) and (hoy or date.today()) > self.calendario.fin


# ======================= Aggregate Inscripcion =======================
class Pago:
    """Entidad interna de Inscripcion: cambia de estado junto con ella."""

    def __init__(self, monto: Dinero):
        self.id = nuevo_id()
        self.monto = monto
        self.estado = EstadoPago.PENDIENTE
        self.fecha_pago: Optional[date] = None

    def esta_pendiente(self) -> bool:
        return self.estado == EstadoPago.PENDIENTE


class Inscripcion(AggregateRoot):
    def __init__(self, id: str, estudiante_id: str, curso_id: str, grupo_id: str,
                 monto: Dinero, fecha_creacion: Optional[date] = None):
        super().__init__()
        self.id, self.estudiante_id, self.curso_id, self.grupo_id = id, estudiante_id, curso_id, grupo_id
        self.fecha_creacion = fecha_creacion or date.today()
        self.estado = EstadoInscripcion.INSCRITO
        self.pago = Pago(monto)
        self.riesgo_perdida_lugar = False

    @classmethod
    def crear(cls, estudiante_id: str, curso_id: str, grupo_id: str, monto: Dinero) -> "Inscripcion":
        i = cls(nuevo_id(), estudiante_id, curso_id, grupo_id, monto)
        i._emitir(ev.InscripcionRealizada(i.id, estudiante_id, curso_id, grupo_id))
        return i

    def registrar_pago(self, fecha: date) -> None:
        if not self.pago.esta_pendiente():
            raise ErrorDeDominio("El pago ya fue registrado")
        self.pago.estado, self.pago.fecha_pago = EstadoPago.PAGADO, fecha
        self.riesgo_perdida_lugar = False
        self._emitir(ev.PagoRegistrado(self.id, self.pago.monto.monto, fecha))

    def verificar_plazo_de_pago(self, hoy: date, plazo_dias: Optional[int]) -> None:
        if plazo_dias is None:
            raise ErrorDeDominio("El plazo de pago aún no ha sido definido por EduTech")
        if self.pago.esta_pendiente() and (hoy - self.fecha_creacion).days > plazo_dias:
            self.riesgo_perdida_lugar = True
            self._emitir(ev.PlazoDePagoVencido(self.id))

    def pago_regularizado(self) -> bool:
        return self.pago.estado == EstadoPago.PAGADO

    def cambiar_grupo(self, nuevo_grupo_id: str) -> None:
        self.grupo_id = nuevo_grupo_id

    def solicitar_reembolso(self) -> None:
        self.estado = EstadoInscripcion.REEMBOLSO_SOLICITADO
        self._emitir(ev.ReembolsoSolicitado(self.id))


# ======================= Aggregate RegistroAcademico =======================
class RegistroAcademico(AggregateRoot):
    """Expediente de una inscripción: asistencias y calificaciones evaluables juntas."""

    def __init__(self, inscripcion_id: str):
        super().__init__()
        self.id = nuevo_id()
        self.inscripcion_id = inscripcion_id
        self._asistencias: list[bool] = []
        self._calificaciones: dict[str, Nota] = {}

    def registrar_asistencia(self, presente: bool) -> None:
        self._asistencias.append(presente)
        self._emitir(ev.AsistenciaRegistrada(self.inscripcion_id, presente))

    def corregir_asistencia(self, sesion: int, presente: bool, motivo: str) -> None:
        if not motivo or not motivo.strip():
            raise ErrorDeDominio("La corrección de asistencia requiere motivo")
        if not 0 <= sesion < len(self._asistencias):
            raise ErrorDeDominio("Sesión inexistente")
        self._asistencias[sesion] = presente
        self._emitir(ev.AsistenciaCorregida(self.inscripcion_id, sesion, motivo))

    def porcentaje_asistencia(self) -> PorcentajeAsistencia:
        return PorcentajeAsistencia(sum(self._asistencias), len(self._asistencias))

    def registrar_calificacion(self, evaluacion_id: str, nota: Nota) -> None:
        if evaluacion_id in self._calificaciones:
            raise ErrorDeDominio("La evaluación ya tiene calificación; use modificar con autorización")
        self._calificaciones[evaluacion_id] = nota
        self._emitir(ev.CalificacionRegistrada(self.inscripcion_id, evaluacion_id, nota.valor))

    def modificar_calificacion(self, evaluacion_id: str, nota: Nota, motivo: str,
                               autorizado_por: Optional[str]) -> None:
        if not autorizado_por:
            raise ErrorDeDominio("Cambio de calificación no autorizado")
        if not motivo or not motivo.strip():
            raise ErrorDeDominio("La modificación de calificación requiere motivo")
        if evaluacion_id not in self._calificaciones:
            raise ErrorDeDominio("La evaluación no tiene calificación registrada")
        anterior = self._calificaciones[evaluacion_id]
        self._calificaciones[evaluacion_id] = nota
        self._emitir(ev.CalificacionModificada(
            self.inscripcion_id, evaluacion_id, anterior.valor, nota.valor, motivo, autorizado_por))

    def promedio(self) -> Optional[Nota]:
        if not self._calificaciones:
            return None
        valores = [n.valor for n in self._calificaciones.values()]
        return Nota(round(sum(valores) / len(valores), 2))


# ======================= Aggregate Certificado =======================
class Certificado(AggregateRoot):
    def __init__(self, inscripcion_id: str):
        super().__init__()
        self.id = nuevo_id()
        self.inscripcion_id = inscripcion_id
        self.estado: Optional[EstadoCertificacion] = None
        self.motivo: str = ""

    def validar_requisitos(self, nota: Optional[Nota], asistencia: PorcentajeAsistencia,
                           curso_concluido: bool, pago_regularizado: bool,
                           asistencia_minima: Optional[float]) -> None:
        """Cuatro condiciones: calificación >= 70, asistencia mínima, curso concluido, pago al corriente."""
        if asistencia_minima is None:
            raise ErrorDeDominio("La asistencia mínima aún no ha sido definida por EduTech")
        motivos = []
        if nota is None or not nota.aprueba():
            motivos.append("Calificación insuficiente")
        if not asistencia.cumple(asistencia_minima):
            motivos.append("Asistencia insuficiente")
        if not curso_concluido:
            motivos.append("Curso no concluido")
        if not pago_regularizado:
            motivos.append("Pago pendiente")
        if motivos:
            self.estado, self.motivo = EstadoCertificacion.NO_CERTIFICADO, "; ".join(motivos)
            self._emitir(ev.EstudianteMarcadoNoCertificado(self.inscripcion_id, self.motivo))
        else:
            self.estado, self.motivo = EstadoCertificacion.APTO, ""
            self._emitir(ev.EstudianteMarcadoApto(self.inscripcion_id))

    def emitir(self) -> None:
        if self.estado != EstadoCertificacion.APTO:
            raise ErrorDeDominio("Estudiante no apto para certificación")
        self.estado = EstadoCertificacion.CERTIFICADO
        self._emitir(ev.CertificadoEmitido(self.inscripcion_id, self.id))


# ======================= Aggregate SolicitudCambioGrupo =======================
class SolicitudCambioGrupo(AggregateRoot):
    def __init__(self, inscripcion_id: str, grupo_destino: str):
        super().__init__()
        self.id = nuevo_id()
        self.inscripcion_id, self.grupo_destino = inscripcion_id, grupo_destino
        self.estado = EstadoSolicitud.PENDIENTE
        self._emitir(ev.SolicitudCambioGrupoRegistrada(inscripcion_id, grupo_destino))

    def _exigir_pendiente(self) -> None:
        if self.estado != EstadoSolicitud.PENDIENTE:
            raise ErrorDeDominio("La solicitud ya fue resuelta")

    def autorizar(self, por: str) -> None:
        self._exigir_pendiente()
        self.estado = EstadoSolicitud.AUTORIZADA
        self._emitir(ev.CambioGrupoAutorizado(self.inscripcion_id, self.grupo_destino, por))

    def rechazar(self, por: str) -> None:
        self._exigir_pendiente()
        self.estado = EstadoSolicitud.RECHAZADA
        self._emitir(ev.CambioGrupoRechazado(self.inscripcion_id, por))


# ======================= Aggregate CancelacionCurso =======================
class CasoResolucion:
    def __init__(self, inscripcion_id: str):
        self.id = nuevo_id()
        self.inscripcion_id = inscripcion_id
        self.estado = EstadoCaso.PENDIENTE


class CancelacionCurso(AggregateRoot):
    """EX-01: cada inscrito de un curso cancelado tiene un caso de resolución."""

    def __init__(self, curso_id: str, motivo: str, autorizado_por: str, inscripciones_ids: list):
        super().__init__()
        self.id = nuevo_id()
        self.curso_id, self.motivo, self.autorizado_por = curso_id, motivo, autorizado_por
        self.fecha = datetime.now()
        self.casos = [CasoResolucion(i) for i in inscripciones_ids]

    @classmethod
    def registrar(cls, curso_id: str, motivo: str, autorizado_por: str, inscripciones_ids: list):
        if not motivo or not autorizado_por:
            raise ErrorDeDominio("La cancelación requiere motivo y quién la autoriza")
        c = cls(curso_id, motivo, autorizado_por, inscripciones_ids)
        c._emitir(ev.CursoCancelado(curso_id, motivo, autorizado_por))
        return c

    def _caso(self, inscripcion_id: str) -> CasoResolucion:
        for caso in self.casos:
            if caso.inscripcion_id == inscripcion_id:
                return caso
        raise ErrorDeDominio("No existe caso de resolución para esa inscripción")

    def solicitar_reembolso(self, inscripcion_id: str) -> None:
        caso = self._caso(inscripcion_id)
        if caso.estado != EstadoCaso.PENDIENTE:
            raise ErrorDeDominio("El caso ya fue resuelto")
        caso.estado = EstadoCaso.REEMBOLSO_SOLICITADO
        self._emitir(ev.ReembolsoSolicitado(inscripcion_id))

    def reinscribir(self, inscripcion_id: str, curso_destino_id: str) -> None:
        caso = self._caso(inscripcion_id)
        if caso.estado != EstadoCaso.PENDIENTE:
            raise ErrorDeDominio("El caso ya fue resuelto")
        caso.estado = EstadoCaso.REINSCRITO
        self._emitir(ev.EstudianteReinscritoEnOtroCurso(inscripcion_id, curso_destino_id))


# ======================= Personas (identidad) =======================
class Estudiante(AggregateRoot):
    def __init__(self, id: str, nombre: str):
        super().__init__()
        self.id, self.nombre = id, nombre


class ClienteEmpresarial(AggregateRoot):
    def __init__(self, id: str, nombre: str):
        super().__init__()
        self.id, self.nombre = id, nombre


class Instructor(AggregateRoot):
    def __init__(self, id: str, nombre: str):
        super().__init__()
        self.id, self.nombre = id, nombre


# ======================= Aggregate Bitacora (ADR-007) =======================
@dataclass(frozen=True)
class RegistroBitacora:
    """Inmutable: quién, qué, cuándo, valor anterior, valor nuevo y quién autorizó (RNF-03)."""
    quien: str
    que: str
    anterior: object
    nuevo: object
    autorizo: Optional[str]
    cuando: datetime = field(default_factory=datetime.now)


class Bitacora(AggregateRoot):
    def __init__(self):
        super().__init__()
        self.id = "bitacora"
        self._registros: list[RegistroBitacora] = []

    def registrar(self, quien: str, que: str, anterior=None, nuevo=None, autorizo=None) -> None:
        self._registros.append(RegistroBitacora(quien, que, anterior, nuevo, autorizo))

    @property
    def registros(self) -> tuple:
        return tuple(self._registros)
