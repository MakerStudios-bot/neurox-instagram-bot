"""Orquestador principal de IA — maneja el flujo de conversación"""

import re
from sqlalchemy.orm.attributes import flag_modified
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
    signal = None
    match = re.search(r'\[SIGNAL:\s*(\w+)\s*\]', ai_response_full)
    if match:
        signal = match.group(1).upper()  # Extraer solo la palabra clave

    # 8. Limpiar la respuesta (remover TODO [SIGNAL: ...] incluyendo los corchetes)
    ai_response_clean = re.sub(r'\[SIGNAL:\s*\w+\s*\]', '', ai_response_full).strip()

    # 9. Extraer y actualizar contexto del lead (nombre, servicio, presupuesto)
    _extract_and_update_context(lead, user_message, ai_response_clean, db)

    # 10. Devolver la respuesta limpia (sin el tag [SIGNAL: ...])
    return {
        "response": ai_response_clean,
        "signal": signal
    }


def _extract_and_update_context(lead: Lead, user_message: str, ai_response: str, db) -> None:
    """
    Extrae información del contexto del lead (nombre, servicio, presupuesto)
    de la conversación y la actualiza en lead.context.

    Args:
        lead: objeto Lead
        user_message: mensaje del usuario
        ai_response: respuesta de la IA
        db: sesión SQLAlchemy
    """
    if not lead.context:
        lead.context = {}

    print(f"\n[CONTEXT] Usuario dice: '{user_message[:100]}'")
    print(f"[CONTEXT] Contexto antes: {lead.context}")

    full_text = (user_message + " " + ai_response).lower()

    # Palabras clave para detectar servicios (más específico primero)
    servicios_keywords = [
        # Web - buscar versiones específicas primero
        (["web completa", "sitio web completo", "página completa", "web profesional completa"], "web_completa"),
        (["landing page", "landing"], "landing_page"),
        (["página web", "pagina web", "sitio web", "desarrollo web", "web"], "web"),

        # Bot con IA - keywords ampliados
        (["bot con ia", "bot ia", "chatbot ia", "bot inteligente",
          "bot con inteligencia", "bot de inteligencia artificial",
          "bot inteligencia artificial", "chatbot inteligente",
          "bot automatico con ia", "bot con inteligencia artificial"], "bot_con_ia"),

        # Bot sin IA
        (["bot sin ia", "bot basico", "bot sin inteligencia", "bot simple"], "bot_sin_ia"),

        # Bot genérico
        (["bot instagram", "bot automatico", "automatización instagram",
          "chatbot", "bot"], "bot"),

        # Video
        (["edición de videos", "editar videos", "edición video",
          "edicion de videos", "editar video", "videos", "video"], "video"),

        # Vendedor IA
        (["vendedor ia", "vendedor inteligente", "sistema de ventas",
          "automatización ventas", "automatizacion ventas",
          "vendedor automatizado", "sistema ventas"], "vendedor_ia"),
    ]

    # Jerarquía de especificidad — no sobreescribir un servicio específico con uno genérico
    SERVICE_SPECIFICITY = {
        "web_completa": 3, "landing_page": 3,
        "bot_con_ia": 3, "bot_sin_ia": 3, "vendedor_ia": 3,
        "web": 2, "bot": 2, "video": 2,
    }

    # Detectar servicio en el mensaje del usuario
    for palabras, servicio in servicios_keywords:
        if any(palabra in user_message.lower() for palabra in palabras):
            current = lead.context.get("servicio_interesado", "")
            # Solo actualizar si es igual o más específico que el actual
            current_level = SERVICE_SPECIFICITY.get(current, 0)
            new_level = SERVICE_SPECIFICITY.get(servicio, 0)
            if new_level >= current_level:
                lead.context = {**lead.context, "servicio_interesado": servicio}
                print(f"  ✓ Servicio detectado: {servicio} (nivel {new_level} >= {current_level})")
            else:
                print(f"  ⚠ Servicio '{servicio}' ignorado (nivel {new_level} < {current_level} '{current}')")
            break

    # Detectar nombre (buscar patrones comunes: "me llamo X", "soy X", "nombre X", "Juan", etc.)
    # Por ahora usamos una heurística simple
    if "nombre" not in lead.context or not lead.context.get("nombre"):
        # Buscar "me llamo...", "mi nombre es...", "soy..."
        patterns = [
            r"me\s+llamo\s+(\w+)",
            r"mi\s+nombre\s+es\s+(\w+)",
            r"soy\s+(\w+)",
            r"nombre:\s*(\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                nombre = match.group(1).capitalize()
                lead.context = {**lead.context, "nombre": nombre}
                print(f"  ✓ Nombre detectado: {nombre}")
                break

    # Detectar presupuesto (buscar números con $ o patrones como "tengo X", "presupuesto")
    if "presupuesto" not in lead.context or not lead.context.get("presupuesto"):
        # Buscar patrones como "$150.000", "150 mil", etc.
        patterns = [
            r"\$?\d+[.,]\d{3}(?:\.\d{3})?",  # $150.000 o 150,000
            r"(\d+)\s*(mil|millones)",  # 150 mil
        ]
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                presupuesto = match.group(0)
                lead.context = {**lead.context, "presupuesto": presupuesto}
                print(f"  ✓ Presupuesto detectado: {presupuesto}")
                break

    # Marcar que el contexto cambió para que SQLAlchemy lo guarde
    print(f"[CONTEXT] Contexto después: {lead.context}")
    flag_modified(lead, "context")
    db.flush()
    print(f"[CONTEXT] Flush completado\n")
