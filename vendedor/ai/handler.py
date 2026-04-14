"""Orquestador principal de IA — maneja el flujo de conversación"""

from database.models import Lead, Message
from database import SessionLocal
from .claude_client import call_claude
from .prompts import system_prompt_for_stage
from config import MAX_HISTORY


def get_ai_response(lead: Lead, user_message: str, db) -> str:
    """
    Obtiene respuesta de IA para un lead.

    Flujo:
    1. Carga el historial de mensajes de la DB (últimos MAX_HISTORY)
    2. Construye el system prompt según la etapa y contexto
    3. Llama a Claude
    4. Guarda el mensaje de la IA en la DB
    5. Devuelve la respuesta (sin el [SIGNAL: ...] que quedó para parsear después)

    Args:
        lead: objeto Lead
        user_message: string del mensaje del usuario
        db: sesión SQLAlchemy

    Returns:
        string con la respuesta de IA (limpia, sin [SIGNAL: ...])
    """

    # 1. Guardar el mensaje del usuario en la DB
    user_msg_record = Message(
        lead_id=lead.id,
        role="user",
        content=user_message
    )
    db.add(user_msg_record)
    db.flush()  # Flush pero no commit, espera a que se agregue la respuesta

    # 2. Cargar historial (últimos MAX_HISTORY mensajes)
    messages = db.query(Message).filter(
        Message.lead_id == lead.id
    ).order_by(Message.created_at).all()

    # Tomar solo los últimos MAX_HISTORY
    messages = messages[-MAX_HISTORY:]

    # 3. Convertir a formato Anthropic SDK
    conversation = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    # 4. Construir system prompt según etapa
    system_prompt = system_prompt_for_stage(lead.stage, lead.client, lead)

    # 5. Llamar a Claude
    try:
        ai_response_full = call_claude(system_prompt, conversation)
    except Exception as e:
        print(f"Error en get_ai_response: {e}")
        ai_response_full = "Disculpa, tuve un error procesando tu mensaje. Intenta de nuevo."

    # 6. Guardar la respuesta de IA en la DB
    assistant_msg_record = Message(
        lead_id=lead.id,
        role="assistant",
        content=ai_response_full
    )
    db.add(assistant_msg_record)
    db.flush()

    # 7. Extraer [SIGNAL: ...] de la respuesta si existe
    # Buscar la última línea que empiece con [SIGNAL:
    signal = None
    lines = ai_response_full.split("\n")
    for line in reversed(lines):
        line_stripped = line.strip()
        if line_stripped.startswith("[SIGNAL:"):
            signal = line_stripped
            break

    # 8. Limpiar la respuesta (remover [SIGNAL: ...] si existe)
    ai_response_clean = ai_response_full
    if signal:
        ai_response_clean = ai_response_full.replace(signal, "").strip()

    # 9. Devolver la respuesta limpia (el signal se extrae en el webhook)
    # Agregamos el signal de vuelta para que el webhook pueda parsearlo
    # pero lo hacemos de forma que pueda extraerlo
    return {
        "response": ai_response_clean,
        "signal": signal
    }
