"""Handlers de Commands (CQRS): un handler por comando; delegan en el Application Service."""
from .comandos import EmitirCertificadoCommand, RegistrarInscripcionCommand


class RegistrarInscripcionHandler:
    def __init__(self, servicio):
        self._servicio = servicio

    def handle(self, cmd: RegistrarInscripcionCommand):
        return self._servicio.registrar_inscripcion(cmd)


class EmitirCertificadoHandler:
    def __init__(self, servicio):
        self._servicio = servicio

    def handle(self, cmd: EmitirCertificadoCommand):
        return self._servicio.emitir_certificado(cmd)
