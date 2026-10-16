"""Implementaciones concretas de los Repository (en memoria). Cambiar a SQL/ORM solo afecta
esta capa: dominio y aplicación dependen únicamente de las abstracciones (ADR-003)."""
from ..dominio.repositorios import (
    CancelacionRepository, CertificadoRepository, CursoRepository, EstudianteRepository,
    InscripcionRepository, RegistroAcademicoRepository,
)


class _RepoMemoria:
    def __init__(self):
        self._datos = {}

    def save(self, agregado) -> None:
        self._datos[agregado.id] = agregado

    def find_by_id(self, id_):
        return self._datos.get(id_)

    def _todos(self):
        return list(self._datos.values())


class CursoRepositoryMemoria(_RepoMemoria, CursoRepository):
    def listar(self):
        return self._todos()


class EstudianteRepositoryMemoria(_RepoMemoria, EstudianteRepository):
    pass


class InscripcionRepositoryMemoria(_RepoMemoria, InscripcionRepository):
    def find_by_estudiante(self, estudiante_id):
        return [i for i in self._todos() if i.estudiante_id == estudiante_id]

    def find_by_curso(self, curso_id):
        return [i for i in self._todos() if i.curso_id == curso_id]

    def pendientes_de_pago(self):
        return [i for i in self._todos() if i.pago.esta_pendiente()]


class RegistroAcademicoRepositoryMemoria(_RepoMemoria, RegistroAcademicoRepository):
    def find_by_inscripcion(self, inscripcion_id):
        return next((r for r in self._todos() if r.inscripcion_id == inscripcion_id), None)


class CertificadoRepositoryMemoria(_RepoMemoria, CertificadoRepository):
    def find_by_inscripcion(self, inscripcion_id):
        return next((c for c in self._todos() if c.inscripcion_id == inscripcion_id), None)


class CancelacionRepositoryMemoria(_RepoMemoria, CancelacionRepository):
    def find_by_curso(self, curso_id):
        return next((c for c in self._todos() if c.curso_id == curso_id), None)
