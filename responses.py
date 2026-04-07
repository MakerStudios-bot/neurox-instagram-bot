"""Respuestas fijas predefinidas para palabras clave comunes"""

FIXED_RESPONSES = {
    # Saludos
    "hola": "¡Hola! 👋 ¿En qué puedo ayudarte?",
    "buenos días": "¡Buenos días! ¿Qué necesitas?",
    "buenas tardes": "¡Buenas tardes! ¿Cómo estás?",
    "buenas noches": "¡Buenas noches! ¿En qué te puedo asistir?",
    "hi": "Hi! 👋 How can I help you?",
    "hii": "Hi there! What can I do for you? 😊",

    # Horarios/Disponibilidad
    "horario": "📅 Estamos disponibles de lunes a viernes, 9am - 6pm. ¿Qué necesitas?",
    "horarios": "📅 Estamos disponibles de lunes a viernes, 9am - 6pm. ¿Qué necesitas?",
    "abierto": "✅ Sí, estamos abiertos. ¿Cómo te ayudamos?",
    "abierta": "✅ Sí, estamos abiertos. ¿Cómo te ayudamos?",

    # Precios/Productos
    "precio": "💰 ¿Cuál es el producto o servicio que te interesa? Te paso los detalles.",
    "precios": "💰 ¿Cuál es el producto o servicio que te interesa? Te paso los detalles.",
    "costo": "💰 ¿Qué servicio te interesa? Cuéntame y te doy el precio.",
    "cuánto": "💰 ¿Cuál producto/servicio? Dime y te paso el precio.",

    # Contacto/Información
    "contacto": "📞 Puedes contactarnos por este DM o escribir a info@example.com",
    "contactar": "📞 Estamos aquí en DMs. ¿Qué necesitas?",
    "dirección": "📍 Puedes encontrarnos en nuestro perfil. ¿Necesitas algo más?",
    "ubicación": "📍 Puedes encontrarnos en nuestro perfil. ¿Necesitas algo más?",

    # Agradecimiento
    "gracias": "¡De nada! 😊 ¿Algo más en lo que pueda ayudarte?",
    "thanks": "You're welcome! 😊 Anything else?",
    "muchas gracias": "¡De nada! 😊 ¿Necesitas algo más?",

    # Despedida
    "bye": "¡Hasta pronto! 👋",
    "adiós": "¡Hasta pronto! 👋",
    "chao": "¡Hasta luego! 👋",
}


def get_fixed_response(message: str) -> str or None:
    """
    Busca una respuesta fija para el mensaje.
    Retorna la respuesta si encuentra una coincidencia, None si no.
    """
    message_lower = message.lower().strip()

    # Búsqueda exacta primero
    if message_lower in FIXED_RESPONSES:
        return FIXED_RESPONSES[message_lower]

    # Búsqueda parcial (si el mensaje contiene la palabra clave)
    for keyword, response in FIXED_RESPONSES.items():
        if keyword in message_lower:
            return response

    return None
