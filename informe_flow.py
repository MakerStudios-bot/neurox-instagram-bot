"""
Máquina de estados para venta de informes vía Instagram DM
"""
import json
from pathlib import Path
import requests

SESSIONS_FILE = Path(__file__).parent / "informe_sessions.json"
INFORMES_API_URL = "https://web-production-e421.up.railway.app"

# Tipos de informes disponibles
TIPOS_INFORMES = {
    "1": {"id": "due_diligence", "label": "Due Diligence de Empresa", "precio": 29990},
    "2": {"id": "mercado", "label": "Análisis de Mercado", "precio": 19990},
    "3": {"id": "persona", "label": "Perfil de Persona", "precio": 9990},
    "4": {"id": "competencia", "label": "Análisis de Competencia", "precio": 24990},
}

def load_sessions():
    """Carga sesiones de archivo"""
    if SESSIONS_FILE.exists():
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    """Guarda sesiones en archivo"""
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

def detect_informe_intent(message_text):
    """Detecta si el usuario quiere un informe"""
    keywords = ["informe", "due diligence", "due", "diligencia", "reporte", "análisis", "investigar"]
    text_lower = message_text.lower()
    return any(keyword in text_lower for keyword in keywords)

def process_informe_message(sender_id, text):
    """Procesa un mensaje dentro del flujo de informe"""
    sessions = load_sessions()
    sender_id_str = str(sender_id)

    # Si no existe sesión, crear nueva
    if sender_id_str not in sessions:
        sessions[sender_id_str] = {
            "estado": "esperando_tipo",
            "tipo": None,
            "objetivo": None,
            "nombre": None,
            "email": None
        }
        save_sessions(sessions)
        return """¿Qué tipo de informe necesitas?

1️⃣ Due Diligence de Empresa ($29.990)
2️⃣ Análisis de Mercado ($19.990)
3️⃣ Perfil de Persona ($9.990)
4️⃣ Análisis de Competencia ($24.990)

Responde con el número (1, 2, 3 o 4)"""

    session = sessions[sender_id_str]
    estado = session["estado"]
    text_clean = text.strip()

    # Paso 1: Esperando tipo de informe
    if estado == "esperando_tipo":
        if text_clean in TIPOS_INFORMES:
            tipo_info = TIPOS_INFORMES[text_clean]
            session["tipo"] = tipo_info["id"]
            session["estado"] = "esperando_objetivo"
            save_sessions(sessions)
            return f"""✅ Seleccionaste: {tipo_info['label']}

¿Qué empresa, persona o tema quieres investigar?"""
        else:
            return "❌ Opción inválida. Por favor responde con 1, 2, 3 o 4"

    # Paso 2: Esperando objetivo (empresa/persona)
    elif estado == "esperando_objetivo":
        session["objetivo"] = text_clean
        session["estado"] = "esperando_nombre"
        save_sessions(sessions)
        return "¿Cuál es tu nombre?"

    # Paso 3: Esperando nombre
    elif estado == "esperando_nombre":
        session["nombre"] = text_clean
        session["estado"] = "esperando_email"
        save_sessions(sessions)
        return "¿Tu email para recibir el informe? (te lo enviaremos en PDF)"

    # Paso 4: Esperando email
    elif estado == "esperando_email":
        session["email"] = text_clean
        session["estado"] = "esperando_pago"
        save_sessions(sessions)

        # Crear pedido en Informes IA
        try:
            tipo_id = session["tipo"]
            tipo_label = TIPOS_INFORMES[next(k for k, v in TIPOS_INFORMES.items() if v["id"] == tipo_id)]["label"]

            link = create_pedido_and_get_link(
                tipo=tipo_id,
                objetivo=session["objetivo"],
                email=session["email"],
                nombre=session["nombre"],
                instagram_sender_id=sender_id_str
            )

            if link:
                return f"""✅ ¡Perfecto! Tu informe de {tipo_label} para {session['objetivo']} está listo para pagar.

💳 Aquí está tu link de pago:
{link}

Una vez que pagues, te enviaremos el informe automáticamente por email y por aquí en el chat. 📊"""
            else:
                return "❌ Error al crear el pedido. Intenta más tarde."
        except Exception as e:
            print(f"Error creando pedido: {e}")
            return f"❌ Error: {str(e)}"

    else:
        return "❌ Algo salió mal. Escribe 'informe' para empezar de nuevo."

def create_pedido_and_get_link(tipo, objetivo, email, nombre, instagram_sender_id):
    """Crea un pedido en Informes IA API y retorna el link de pago"""
    try:
        payload = {
            "tipo": tipo,
            "objetivo": objetivo,
            "email": email,
            "nombre": nombre,
            "datos_extra": f"instagram_sender_id:{instagram_sender_id}"
        }

        response = requests.post(
            f"{INFORMES_API_URL}/api/pedidos",
            params=payload,
            timeout=10
        )

        if response.status_code == 200:
            pedido = response.json().get("pedido", {})
            # Por ahora, retornamos instrucciones para generar el link manualmente
            # En el futuro podemos automatizar esto con la API de Flow
            return f"https://www.flow.cl/uri/nYsCkwR36"  # Link de prueba
        else:
            print(f"Error en API: {response.text}")
            return None
    except Exception as e:
        print(f"Error en create_pedido_and_get_link: {e}")
        return None

def reset_session(sender_id):
    """Reinicia la sesión de un usuario"""
    sessions = load_sessions()
    sender_id_str = str(sender_id)
    if sender_id_str in sessions:
        del sessions[sender_id_str]
        save_sessions(sessions)
