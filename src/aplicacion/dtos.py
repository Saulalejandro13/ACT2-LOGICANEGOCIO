"""Modelos de LECTURA / respuesta. No exponen los aggregates (CQRS)."""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CursoDisponibleDTO:
    curso_id: str
    nombre: str
    modalidad: str
    estado: str
    disponible: bool


@dataclass(frozen=True)
class PagoPendienteDTO:
    inscripcion_id: str
    estudiante_id: str
    curso_id: str
    monto: float
    estado: str


@dataclass(frozen=True)
class InscripcionDTO:
    id: str
    estudiante_id: str
    curso_id: str
    grupo_id: str
    estado: str
    estado_pago: str


@dataclass(frozen=True)
class CertificadoDTO:
    inscripcion_id: str
    estado: object  # EstadoCertificacion
    motivo: str = ""


@dataclass(frozen=True)
class CancelacionDTO:
    curso_id: str
    casos: List[str] = field(default_factory=list)  # ids de inscripción con caso de resolución
