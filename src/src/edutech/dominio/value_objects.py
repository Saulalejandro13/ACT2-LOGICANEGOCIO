"""Value Objects: se definen por sus valores, son inmutables y validan sus reglas (ADR-005)."""
from dataclasses import dataclass, replace
from datetime import date
from typing import Optional

from .comun import ErrorDeDominio


@dataclass(frozen=True)
class Dinero:
    monto: float
    moneda: str = "MXN"

    def __post_init__(self):
        if self.monto < 0:
            raise ValueError("El monto no puede ser negativo")


@dataclass(frozen=True)
class Nota:
    """Calificación de una evaluación (0-100). Mínima aprobatoria: 70."""
    valor: float
    MINIMA_APROBATORIA = 70

    def __post_init__(self):
        if not 0 <= self.valor <= 100:
            raise ValueError("La nota debe estar entre 0 y 100")

    def aprueba(self) -> bool:
        return self.valor >= self.MINIMA_APROBATORIA


@dataclass(frozen=True)
class Cupo:
    """Lugares de un grupo: mínimo 5, máximo 25 y ocupados."""
    minimo: int = 5
    maximo: int = 25
    ocupados: int = 0

    def __post_init__(self):
        if self.minimo > self.maximo or not 0 <= self.ocupados <= self.maximo:
            raise ValueError("Cupo inválido")

    @property
    def restantes(self) -> int:
        return self.maximo - self.ocupados

    @property
    def esta_lleno(self) -> bool:
        return self.ocupados >= self.maximo

    @property
    def alcanza_minimo(self) -> bool:
        return self.ocupados >= self.minimo

    def ocupar(self) -> "Cupo":
        if self.esta_lleno:
            raise ErrorDeDominio("Grupo sin cupo")
        return replace(self, ocupados=self.ocupados + 1)

    def liberar(self) -> "Cupo":
        if self.ocupados == 0:
            raise ErrorDeDominio("El grupo no tiene lugares ocupados")
        return replace(self, ocupados=self.ocupados - 1)


@dataclass(frozen=True)
class PorcentajeAsistencia:
    """Valor calculado. El mínimo requerido está POR DEFINIR (ADR-008): se recibe como parámetro."""
    asistidas: int
    total: int

    @property
    def valor(self) -> float:
        return 0.0 if self.total == 0 else self.asistidas / self.total * 100

    def cumple(self, minimo: float) -> bool:
        return self.valor >= minimo


@dataclass(frozen=True)
class CalendarioCurso:
    inicio: date
    fin: date
    sesiones: int = 0

    def __post_init__(self):
        if self.fin < self.inicio:
            raise ValueError("La fecha de fin no puede ser anterior al inicio")


@dataclass(frozen=True)
class PeriodoInscripcion:
    apertura: date
    cierre: date

    def __post_init__(self):
        if self.cierre < self.apertura:
            raise ValueError("El cierre no puede ser anterior a la apertura")

    def esta_abierto(self, hoy: date) -> bool:
        return self.apertura <= hoy <= self.cierre


@dataclass(frozen=True)
class ReglasConfigurables:
    """Reglas que EduTech aún no define (ADR-008). None = pendiente."""
    asistencia_minima: Optional[float] = None
    plazo_pago_dias: Optional[int] = None
