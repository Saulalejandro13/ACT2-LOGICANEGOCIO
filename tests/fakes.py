"""Dobles de prueba (Repository / UnitOfWork / EventBus en memoria).
Implementan los contratos de la Etapa 5 y 6 (ADR-003). Sin SQL ni ORM.
"""


class RepoMemoria:
    def __init__(self):
        self.datos = {}

    def save(self, agregado):
        self.datos[agregado.id] = agregado

    def find_by_id(self, id_):
        return self.datos.get(id_)


class CursoRepositoryMemoria(RepoMemoria):
    def listar(self):
        return list(self.datos.values())


class EstudianteRepositoryMemoria(RepoMemoria):
    pass


class InscripcionRepositoryMemoria(RepoMemoria):
    def find_by_estudiante(self, estudiante_id):
        return [i for i in self.datos.values() if i.estudiante_id == estudiante_id]

    def find_by_curso(self, curso_id):
        return [i for i in self.datos.values() if i.curso_id == curso_id]

    def pendientes_de_pago(self):
        return [i for i in self.datos.values() if i.pago.esta_pendiente()]


class RegistroAcademicoRepositoryMemoria(RepoMemoria):
    def find_by_inscripcion(self, inscripcion_id):
        return next((r for r in self.datos.values() if r.inscripcion_id == inscripcion_id), None)


class CertificadoRepositoryMemoria(RepoMemoria):
    def find_by_inscripcion(self, inscripcion_id):
        return next((c for c in self.datos.values() if c.inscripcion_id == inscripcion_id), None)


class CancelacionRepositoryMemoria(RepoMemoria):
    def find_by_curso(self, curso_id):
        return next((c for c in self.datos.values() if c.curso_id == curso_id), None)


class FakeUnitOfWork:
    """Registra si la operacion se confirmo o se revirtio (todo o nada)."""

    def __init__(self):
        self.confirmado = False
        self.revertido = False

    def __enter__(self):
        return self

    def __exit__(self, tipo, valor, tb):
        if tipo is not None:
            self.rollback()
            return False  # propaga el error de negocio
        return False

    def commit(self):
        self.confirmado = True

    def rollback(self):
        self.revertido = True


class FakeEventBus:
    def __init__(self):
        self.publicados = []

    def publicar(self, evento):
        self.publicados.append(evento)

    def tipos(self):
        return [type(e).__name__ for e in self.publicados]
