# language: es
# Escenarios de aceptacion ligados a los casos de uso seleccionados (CU-02, CU-03, CU-05).
# Cada escenario se puede automatizar con pytest-bdd o ejecutarse manualmente y capturar evidencia.

Característica: Inscripción individual (CU-02, US-02)

  Escenario: 1.1 Inscripción exitosa con cupo disponible
    Dado un curso "Python" con el grupo "G1" que tiene lugares disponibles
    Y un estudiante registrado
    Cuando el estudiante se inscribe al grupo "G1"
    Entonces se crea la inscripción en estado "Inscrito"
    Y se genera un pago en estado "Pendiente"
    Y se ocupa un lugar del grupo

  Escenario: 1.2 Inscripción rechazada por grupo sin cupo
    Dado un grupo "G1" con 25 inscritos
    Cuando un estudiante intenta inscribirse al grupo "G1"
    Entonces el sistema rechaza la operación con el mensaje "Grupo sin cupo"
    Y no se crea ninguna inscripción ni pago

Característica: Control de cupo (CU-03, US-04)

  Escenario: 2.1 El curso queda sin cupo disponible al llegar a 25
    Dado un grupo con 24 inscritos
    Cuando se registra la inscripción número 25
    Entonces el curso pasa a "Sin cupo disponible"
    Y se emite el evento "CupoMaximoAlcanzado"

Característica: Validación y emisión de certificado (CU-05, US-10, US-11)

  Escenario: 3.1 Estudiante apto recibe certificado
    Dado un estudiante con calificación 85, asistencia suficiente, curso concluido y pago regularizado
    Cuando Control Escolar valida los requisitos
    Entonces el estudiante queda "Apto para certificación"
    Cuando Control Escolar emite el certificado
    Entonces el estado pasa a "Certificado" y se emite "CertificadoEmitido"

  Esquema del escenario: 3.2 Estudiante no certificado por incumplir un requisito
    Dado un estudiante que incumple "<requisito>"
    Cuando Control Escolar valida los requisitos
    Entonces queda "No certificado" con motivo "<motivo>"
    Y no se puede emitir el certificado

    Ejemplos:
      | requisito              | motivo                    |
      | calificación mínima 70 | Calificación insuficiente |
      | asistencia mínima      | Asistencia insuficiente   |
      | curso concluido        | Curso no concluido        |
      | pago regularizado      | Pago pendiente            |
