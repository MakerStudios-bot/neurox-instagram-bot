import os
from anthropic import Anthropic

client = Anthropic()

SYSTEM_PROMPT = """Eres un asistente de atención al cliente amable y profesional para una cuenta de Instagram.
Responde brevemente (máximo 2-3 líneas), de manera natural y conversacional.
Sé útil y cortés. Si no sabes algo, ofrece ayuda o sugiere contactar con soporte."""

# Almacenar historial de conversaciones (máximo 20 mensajes previos)
conversation_history = {}
MAX_HISTORY = 20
MAX_TOKENS = 500


def get_ai_response(user_id: str, user_message: str) -> str:
    """Obtiene respuesta de Claude API para el mensaje del usuario con historial"""
    try:
        # Inicializar historial del usuario si no existe
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        # Agregar mensaje del usuario al historial
        conversation_history[user_id].append({
            "role": "user",
            "content": user_message
        })

        # Mantener solo los últimos 20 mensajes
        if len(conversation_history[user_id]) > MAX_HISTORY:
            conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]

        # Llamar a Claude con el historial
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )

        response_text = message.content[0].text

        # Agregar respuesta de Claude al historial
        conversation_history[user_id].append({
            "role": "assistant",
            "content": response_text
        })

        return response_text
    except Exception as e:
        print(f"Error llamando a Claude API: {e}")
        return "Disculpa, tuve un error procesando tu mensaje. Intenta de nuevo."
