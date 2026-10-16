"""Contratos de Repository en términos del dominio (ADR-003). Sin SQL ni ORM.
Uno por aggregate root, para no depender de un repositorio genérico gigante (SOLID-I).
"""
from abc import ABC, abstractmethod
from typing import List, Optional


class CursoRepository(ABC):
    @abstractmethod
    def find_by_id(self, curso_id: str): ...

    @abstractmethod
    def save(self, curso) -> None: ...

    @abstractmethod
    def listar(self) -> List: ...


class EstudianteRepository(ABC):
    @abstractmethod
    def find_by_id(self, estudiante_id: str): ...

    @abstractmethod
    def save(self, estudiante) -> None: ...


class InscripcionRepository(ABC):
    @abstractmethod
    def find_by_id(self, inscripcion_id: str): ...

    @abstractmethod
    def find_by_estudiante(self, estudiante_id: str) -> List: ...

    @abstractmethod
    def find_by_curso(self, curso_id: str) -> List: ...

    @abstractmethod
    def pendientes_de_pago(self) -> List: ...

    @abstractmethod
    def save(self, inscripcion) -> None: ...


class RegistroAcademicoRepository(ABC):
    @abstractmethod
    def find_by_inscripcion(self, inscripcion_id: str) -> Optional[object]: ...

    @abstractmethod
    def save(self, registro) -> None: ...


class CertificadoRepository(ABC):
    @abstractmethod
    def find_by_inscripcion(self, inscripcion_id: str) -> Optional[object]: ...

    @abstractmethod
    def save(self, certificado) -> None: ...


class CancelacionRepository(ABC):
    @abstractmethod
    def find_by_curso(self, curso_id: str) -> Optional[object]: ...

    @abstractmethod
    def save(self, cancelacion) -> None: ...
