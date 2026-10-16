"""Pruebas de arquitectura (ADR-001..003, SOLID-D). Funcionan tal cual: solo analizan imports.
  dominio     -> NO importa aplicacion ni infraestructura, ni SQL/ORM
  aplicacion  -> NO importa infraestructura (depende de abstracciones)
Ajustar PAQUETE si el paquete no se llama `edutech`.
"""
import ast
from pathlib import Path

import pytest

PAQUETE = "edutech"
RAIZ = Path(__file__).resolve().parent.parent / "src" / PAQUETE

REGLAS = {
    "dominio": {"aplicacion", "infraestructura"},
    "aplicacion": {"infraestructura"},
}
LIBRERIAS_DE_PERSISTENCIA = {"sqlite3", "sqlalchemy", "psycopg2", "pymysql", "django", "peewee"}


def _imports(archivo: Path):
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for a in nodo.names:
                yield a.name
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            yield nodo.module


@pytest.mark.parametrize("capa,prohibidas", REGLAS.items())
def test_capa_no_depende_de_capas_prohibidas(capa, prohibidas):
    violaciones = [
        f"{a.name} importa {m}"
        for a in (RAIZ / capa).rglob("*.py")
        for m in _imports(a)
        if prohibidas & set(m.split("."))
    ]
    assert not violaciones, "\n".join(violaciones)


@pytest.mark.parametrize("capa", ["dominio", "aplicacion"])
def test_nucleo_no_depende_de_sql_ni_orm(capa):
    violaciones = [
        f"{a.name} importa {m}"
        for a in (RAIZ / capa).rglob("*.py")
        for m in _imports(a)
        if m.split(".")[0] in LIBRERIAS_DE_PERSISTENCIA
    ]
    assert not violaciones, "\n".join(violaciones)


EVENTOS_DOCUMENTADOS = {  # Mapa de Dominio / ADR-006: lenguaje ubicuo, nombres en pasado
    "InscripcionRealizada", "CupoMaximoAlcanzado", "InscripcionCerradaSinCupoMinimo",
    "PagoRegistrado", "PlazoDePagoVencido", "AsistenciaRegistrada", "AsistenciaCorregida",
    "CalificacionRegistrada", "CalificacionModificada", "EstudianteMarcadoApto",
    "EstudianteMarcadoNoCertificado", "CertificadoEmitido", "SolicitudCambioGrupoRegistrada",
    "CambioGrupoAutorizado", "CambioGrupoRechazado", "CursoCancelado", "ReembolsoSolicitado",
    "EstudianteReinscritoEnOtroCurso", "InstructorSustituido", "ReinscripcionRealizada",
}


def _eventos_en_codigo():
    eventos = RAIZ / "dominio" / "eventos.py"
    return {n.name for n in ast.walk(ast.parse(eventos.read_text(encoding="utf-8")))
            if isinstance(n, ast.ClassDef) and n.name != "EventoDominio"}


def test_eventos_del_codigo_coinciden_con_el_lenguaje_ubicuo():
    """No hay eventos inventados: cada clase de eventos.py esta en el Mapa de Dominio."""
    sobrantes = _eventos_en_codigo() - EVENTOS_DOCUMENTADOS
    assert not sobrantes, f"Eventos que no estan en el Mapa de Dominio: {sobrantes}"


def test_todos_los_eventos_documentados_existen_en_el_codigo():
    faltantes = EVENTOS_DOCUMENTADOS - _eventos_en_codigo()
    assert not faltantes, f"Eventos documentados sin implementar: {faltantes}"
