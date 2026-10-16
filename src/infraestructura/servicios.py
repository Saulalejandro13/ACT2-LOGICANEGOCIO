"""Servicios técnicos: Unit of Work y Event Bus síncronos en memoria."""
from collections import defaultdict

from ..aplicacion.abstracciones import EventBus, UnitOfWork


class UnitOfWorkMemoria(UnitOfWork):
    def __init__(self):
        self.confirmado = False
        self.revertido = False

    def __enter__(self):
        self.confirmado = self.revertido = False
        return self

    def __exit__(self, tipo, valor, tb):
        if tipo is not None:
            self.rollback()
        return False  # propaga el error de negocio

    def commit(self) -> None:
        self.confirmado = True

    def rollback(self) -> None:
        self.revertido = True


class EventBusSincrono(EventBus):
    def __init__(self):
        self._suscriptores = defaultdict(list)
        self.historial = []

    def suscribir(self, tipo_evento, manejador) -> None:
        self._suscriptores[tipo_evento].append(manejador)

    def publicar(self, evento) -> None:
        self.historial.append(evento)
        for manejador in self._suscriptores[type(evento)]:
            manejador(evento)
