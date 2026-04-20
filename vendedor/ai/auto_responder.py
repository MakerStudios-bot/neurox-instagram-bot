"""Respuestas automáticas sin IA — para bot_automatico_sin_ia"""
import os
import json


def get_auto_response(message_text: str) -> str:
    msg = message_text.lower().strip()
    business_name = os.getenv("BUSINESS_NAME", "Neurox")
    contacto = os.getenv("WHATSAPP_DERIVACION", "") or os.getenv("CONTACTO_DERIVACION", "")
    productos_raw = os.getenv("PRODUCTOS_PROMPT", "")
    respuestas_custom = os.getenv("RESPUESTAS_CUSTOM", "")

    # Cargar respuestas custom si existen (JSON: {"palabra_clave": "respuesta"})
    custom = {}
    if respuestas_custom:
        try:
            custom = json.loads(respuestas_custom)
        except Exception:
            pass

    # Revisar respuestas custom primero
    for keyword, respuesta in custom.items():
        if keyword.lower() in msg:
            return respuesta

    # Saludo
    if any(w in msg for w in ["hola", "buenas", "hey", "hi", "buenos dias", "buenas tardes", "buenas noches", "que tal"]):
        resp = f"¡Hola! Bienvenido a {business_name} 👋\n\n"
        if productos_raw:
            resp += f"Estos son nuestros productos:\n{productos_raw}\n\n"
        resp += "¿En qué te puedo ayudar?"
        return resp

    # Precios / productos / catálogo
    if any(w in msg for w in ["precio", "precios", "cuanto", "cuánto", "cuesta", "vale", "catalogo", "catálogo", "productos", "que venden", "qué venden", "que tienen", "qué tienen", "lista"]):
        if productos_raw:
            return f"Estos son nuestros productos y precios:\n\n{productos_raw}\n\n¿Te interesa alguno?"
        return f"¡Con gusto te ayudo con los precios! Escríbenos al {contacto} para más detalles."

    # Envío / despacho
    if any(w in msg for w in ["envio", "envío", "despacho", "delivery", "envian", "envían", "llega", "demora"]):
        return f"Hacemos envíos a todo Chile 📦\nPara más detalles sobre envío escríbenos al {contacto}"

    # Garantía / devolución
    if any(w in msg for w in ["garantia", "garantía", "devolucion", "devolución", "cambio", "reclamo"]):
        return f"Todos nuestros productos tienen garantía ✅\nPara consultas sobre garantía o devoluciones contacta al {contacto}"

    # Horario
    if any(w in msg for w in ["horario", "horarios", "atencion", "atención", "abren", "abierto", "disponible"]):
        horario = os.getenv("HORARIO_ATENCION", "Lunes a Viernes de 9:00 a 18:00")
        return f"Nuestro horario de atención es:\n{horario}\n\n¿Necesitas algo más?"

    # Ubicación / dirección
    if any(w in msg for w in ["direccion", "dirección", "donde", "dónde", "ubicacion", "ubicación", "local", "tienda"]):
        return f"Para información sobre nuestra ubicación escríbenos al {contacto}"

    # Pago / formas de pago
    if any(w in msg for w in ["pago", "pagar", "transferencia", "tarjeta", "efectivo", "webpay", "mercadopago"]):
        return f"Aceptamos transferencia bancaria, tarjeta de crédito/débito y efectivo 💳\n¿Te gustaría hacer un pedido?"

    # Comprar / pedir / quiero
    if any(w in msg for w in ["comprar", "pedir", "quiero", "reservar", "apartar", "disponible", "stock", "hay"]):
        if contacto:
            return f"¡Genial! Para hacer tu pedido escríbenos directamente al {contacto} y te atendemos al toque 🚀"
        return f"¡Genial! Cuéntame qué producto te interesa y coordinamos 🚀"

    # Gracias
    if any(w in msg for w in ["gracias", "gracia", "thank", "genial", "perfecto", "dale", "buena"]):
        return f"¡De nada! Cualquier cosa estamos aquí para ayudarte 😊"

    # Fallback
    if contacto:
        return f"¡Gracias por escribirnos a {business_name}! Para atención personalizada escríbenos al {contacto} 📱"
    return f"¡Gracias por escribirnos a {business_name}! ¿En qué te puedo ayudar? Puedes preguntar por precios, envíos o disponibilidad 😊"
