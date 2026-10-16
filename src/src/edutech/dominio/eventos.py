"""Domain Events (ADR-006). Nombrados en pasado; coinciden con el Mapa de Dominio."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EventoDominio:
    """Base de todos los eventos."""


@dataclass(frozen=True)
class InscripcionRealizada(EventoDominio):
    inscripcion_id: str
    estudiante_id: str
    curso_id: str
    grupo_id: str


@dataclass(frozen=True)
class CupoMaximoAlcanzado(EventoDominio):
    curso_id: str
    grupo_id: str


@dataclass(frozen=True)
class InscripcionCerradaSinCupoMinimo(EventoDominio):
    curso_id: str
    inscritos: int


@dataclass(frozen=True)
class PagoRegistrado(EventoDominio):
    inscripcion_id: str
    monto: float
    fecha: date


@dataclass(frozen=True)
class PlazoDePagoVencido(EventoDominio):
    inscripcion_id: str


@dataclass(frozen=True)
class AsistenciaRegistrada(EventoDominio):
    inscripcion_id: str
    presente: bool


@dataclass(frozen=True)
class AsistenciaCorregida(EventoDominio):
    inscripcion_id: str
    sesion: int
    motivo: str


@dataclass(frozen=True)
class CalificacionRegistrada(EventoDominio):
    inscripcion_id: str
    evaluacion_id: str
    nota: float


@dataclass(frozen=True)
class CalificacionModificada(EventoDominio):
    inscripcion_id: str
    evaluacion_id: str
    valor_anterior: float
    valor_nuevo: float
    motivo: str
    autorizado_por: str


@dataclass(frozen=True)
class EstudianteMarcadoApto(EventoDominio):
    inscripcion_id: str


@dataclass(frozen=True)
class EstudianteMarcadoNoCertificado(EventoDominio):
    inscripcion_id: str
    motivo: str


@dataclass(frozen=True)
class CertificadoEmitido(EventoDominio):
    inscripcion_id: str
    certificado_id: str


@dataclass(frozen=True)
class SolicitudCambioGrupoRegistrada(EventoDominio):
    inscripcion_id: str
    grupo_destino: str


@dataclass(frozen=True)
class CambioGrupoAutorizado(EventoDominio):
    inscripcion_id: str
    grupo_destino: str
    autorizado_por: str


@dataclass(frozen=True)
class CambioGrupoRechazado(EventoDominio):
    inscripcion_id: str
    rechazado_por: str


@dataclass(frozen=True)
class CursoCancelado(EventoDominio):
    curso_id: str
    motivo: str
    autorizado_por: str


@dataclass(frozen=True)
class ReembolsoSolicitado(EventoDominio):
    inscripcion_id: str


@dataclass(frozen=True)
class EstudianteReinscritoEnOtroCurso(EventoDominio):
    inscripcion_id: str
    curso_destino_id: str


@dataclass(frozen=True)
class InstructorSustituido(EventoDominio):
    curso_id: str
    instructor_anterior: str
    instructor_nuevo: str


@dataclass(frozen=True)
class ReinscripcionRealizada(EventoDominio):
    inscripcion_nueva_id: str
    inscripcion_anterior_id: str
