"""Puertos que la Service Layer necesita y que implementa la infraestructura (SOLID-D)."""
from abc import ABC, abstractmethod


class UnitOfWork(ABC):
    """Agrupa los cambios de un caso de uso: se confirman todos o ninguno."""

    @abstractmethod
    def __enter__(self): ...

    @abstractmethod
    def __exit__(self, tipo, valor, tb): ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


class EventBus(ABC):
    @abstractmethod
    def publicar(self, evento) -> None: ...
