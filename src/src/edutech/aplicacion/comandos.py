"""Commands (CQRS): intenciones que MODIFICAN el estado."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RegistrarInscripcionCommand:
    estudiante_id: str
    curso_id: str
    grupo_id: str


@dataclass(frozen=True)
class EmitirCertificadoCommand:
    inscripcion_id: str


@dataclass(frozen=True)
class ValidarRequisitosCommand:
    inscripcion_id: str


@dataclass(frozen=True)
class CancelarCursoCommand:
    curso_id: str
    motivo: str
    autorizado_por: str
