"""Estados y catálogos (Value Objects tipo enumeración) del glosario de EduTech."""
from enum import Enum


class Modalidad(Enum):
    PRESENCIAL = "Presencial"
    EN_LINEA = "En línea"


class EstadoCurso(Enum):
    DISPONIBLE = "Disponible"
    SIN_CUPO_DISPONIBLE = "Sin cupo disponible"
    EN_CURSO = "En curso"
    CANCELADO = "Cancelado"


class EstadoInscripcion(Enum):
    INSCRITO = "Inscrito"
    EN_CURSO = "En curso"
    EVALUADO = "Evaluado"
    APROBADO = "Aprobado"
    REPROBADO = "Reprobado"
    REEMBOLSO_SOLICITADO = "Reembolso solicitado"


class EstadoPago(Enum):
    PENDIENTE = "Pendiente"
    PAGADO = "Pagado"


class EstadoCertificacion(Enum):
    APTO = "Apto para certificación"
    CERTIFICADO = "Certificado"
    NO_CERTIFICADO = "No certificado"


class EstadoSolicitud(Enum):
    PENDIENTE = "Pendiente de autorización"
    AUTORIZADA = "Autorizada"
    RECHAZADA = "Rechazada"


class EstadoCaso(Enum):
    PENDIENTE = "Pendiente"
    REEMBOLSO_SOLICITADO = "Reembolso solicitado"
    REINSCRITO = "Reinscrito"


class TipoEvaluacion(Enum):
    PARCIAL = "Parcial"
    FINAL = "Final"
    PROYECTO = "Proyecto"
    PARTICIPACION = "Participación"


class Rol(Enum):
    ESTUDIANTE = "Estudiante"
    INSTRUCTOR = "Instructor"
    CONTROL_ESCOLAR = "Control Escolar"
    ADMINISTRACION = "Administración"
