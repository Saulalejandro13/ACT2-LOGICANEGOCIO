"""Queries (CQRS): solo lectura, sin Unit of Work ni cambios de estado (ADR-009)."""
from dataclasses import dataclass
from typing import Optional

from ..dominio.enumeraciones import EstadoCurso
from .dtos import CursoDisponibleDTO, PagoPendienteDTO


@dataclass(frozen=True)
class ConsultarCatalogoQuery:
    modalidad: Optional[str] = None


@dataclass(frozen=True)
class ConsultarPagosPendientesQuery:
    curso_id: Optional[str] = None


class ConsultarCatalogoHandler:
    def __init__(self, cursos):
        self._cursos = cursos

    def handle(self, query: ConsultarCatalogoQuery):
        resultado = []
        for c in self._cursos.listar():
            if query.modalidad and c.modalidad.value != query.modalidad:
                continue
            resultado.append(CursoDisponibleDTO(
                curso_id=c.id, nombre=c.nombre, modalidad=c.modalidad.value, estado=c.estado.value,
                disponible=c.estado == EstadoCurso.DISPONIBLE))
        return resultado


class ConsultarPagosPendientesHandler:
    def __init__(self, inscripciones):
        self._inscripciones = inscripciones

    def handle(self, query: ConsultarPagosPendientesQuery):
        return [
            PagoPendienteDTO(i.id, i.estudiante_id, i.curso_id, i.pago.monto.monto, i.pago.estado.value)
            for i in self._inscripciones.pendientes_de_pago()
            if not query.curso_id or i.curso_id == query.curso_id
        ]
