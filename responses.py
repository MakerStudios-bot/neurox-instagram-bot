"""Respuestas fijas SOLO para saludos simples. Todo lo demás usa IA."""

FIXED_RESPONSES = {
    # Saludos simples - solo presentarse
    "hola": "¡Hola! Soy el bot de Neurox. ¿Tienes negocio en Instagram?",
    "buenos días": "¡Buenos días! Soy Neurox. Si tienes negocio, te ayudo a vender más.",
    "buenas tardes": "¡Buenas tardes! Soy el bot de Neurox.",
    "buenas noches": "¡Buenas noches! Neurox aquí.",
    "holis": "¡Hola! Soy Neurox.",
    "hey": "¡Hey! Neurox aquí.",
    "qué tal": "¡Bien! ¿Qué necesitas?",

    # Preguntas simples sobre qué es el bot
    "qué es": "🤖 Soy un bot IA que ayuda a negocios en Instagram a vender más. Respondo mensajes 24/7 y cierro ventas automáticamente.",
    "que es": "🤖 Soy un bot IA que ayuda a negocios en Instagram a vender más. Respondo mensajes 24/7 y cierro ventas automáticamente.",
    "quién eres": "🤖 Soy el bot de Neurox. Ayudo a negocios a vender más en Instagram.",
    "quien eres": "🤖 Soy el bot de Neurox. Ayudo a negocios a vender más en Instagram.",
    "cómo funciona": "🤖 Instalamos el bot en tu Instagram, le enseñamos sobre tu negocio, y responde mensajes 24/7 vendiendo como tú.",
    "como funciona": "🤖 Instalamos el bot en tu Instagram, le enseñamos sobre tu negocio, y responde mensajes 24/7 vendiendo como tú.",

    # Despedidas
    "bye": "Espera 👋 Antes de irte, cuéntame qué negocio tienes.",
    "adiós": "Oye 👋 No te vayas sin conversar.",
    "chao": "Un segundo ⏳ ¿De verdad no quieres saber cómo vender más?",
}


def get_fixed_response(message: str) -> str or None:
    """
    Busca una respuesta fija para el mensaje.
    Solo para saludos simples. Todo lo demás usa IA.
    """
    import re
    message_lower = message.lower().strip()

    # Búsqueda exacta primero
    if message_lower in FIXED_RESPONSES:
        return FIXED_RESPONSES[message_lower]

    # Búsqueda de palabras completas para saludos y preguntas básicas
    # Solo palabras de 4+ caracteres
    for keyword, response in FIXED_RESPONSES.items():
        if len(keyword) >= 4:
            if re.search(r'\b' + re.escape(keyword) + r'\b', message_lower):
                return response

    # Si no encuentra nada, deja que la IA responda (contexto completo)
    return None
