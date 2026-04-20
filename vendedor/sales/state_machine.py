"""State machine del lead — transiciones entre etapas"""

from database.models import Lead
import re


def extract_signal(ai_response: str) -> str:
    """
    Extrae el [SIGNAL: ...] de la respuesta de Claude.

    Args:
        ai_response: respuesta completa de Claude

    Returns:
        string "CALIFICAR", "AGENDAR", "CERRAR" o None
    """
    # Buscar [SIGNAL: X] en la respuesta
    match = re.search(r'\[SIGNAL:\s*(\w+)\s*\]', ai_response)
    if match:
        return match.group(1).upper()
    return None


def should_transition(lead: Lead, signal: str) -> tuple[bool, str]:
    """
    Determina si el lead debe pasar a otra etapa basado en:
    - Etapa actual
    - Signal de Claude

    Args:
        lead: objeto Lead
        signal: string "CALIFICAR", "AGENDAR", "CERRAR" o None

    Returns:
        (debería_transicionar: bool, nueva_etapa: str)
    """

    current_stage = lead.stage

    # Transiciones por etapa
    transitions = {
        "NUEVO": {
            "CALIFICAR": "CALIFICANDO",  # Siempre → CALIFICANDO en primer mensaje
            "AGENDAR": "AGENDADO",
        },
        "CALIFICANDO": {
            "AGENDAR": "AGENDADO",
            "CERRAR": "CERRADO",
        },
        "AGENDADO": {
            "CERRAR": "CERRADO",
        },
        "FOLLOW_UP": {
            "AGENDAR": "AGENDADO",
            "CERRAR": "CERRADO",
        },
    }

    # Si la etapa actual no tiene transiciones definidas, no hacer nada
    if current_stage not in transitions:
        return False, current_stage

    # Si el signal es None o no está en las transiciones, mantener la etapa
    if signal is None or signal not in transitions[current_stage]:
        return False, current_stage

    # Aplicar transición
    nueva_etapa = transitions[current_stage][signal]
    return True, nueva_etapa


def apply_transition(lead: Lead, nueva_etapa: str, db) -> None:
    """
    Aplica la transición de etapa al lead en la DB.

    Args:
        lead: objeto Lead
        nueva_etapa: string con la nueva etapa
        db: sesión SQLAlchemy
    """
    if lead.stage != nueva_etapa:
        old_stage = lead.stage
        lead.stage = nueva_etapa
        print(f"  Transición: {old_stage} → {nueva_etapa}")
        db.flush()
