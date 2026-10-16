"""Piezas comunes del dominio: error de negocio, ids y base de Aggregate Root."""
import uuid


class ErrorDeDominio(Exception):
    """Rechazo de una regla de negocio, expresado en lenguaje ubicuo
    (p. ej. 'Grupo sin cupo', 'Estudiante no apto para certificación')."""


def nuevo_id() -> str:
    return uuid.uuid4().hex[:8]


class AggregateRoot:
    """Raíz de aggregate: acumula los Domain Events que ocurren en su interior."""

    def __init__(self):
        self.eventos = []

    def _emitir(self, evento):
        self.eventos.append(evento)

    def extraer_eventos(self):
        """Devuelve y limpia los eventos pendientes (los publica la Service Layer)."""
        pendientes, self.eventos = self.eventos, []
        return pendientes
