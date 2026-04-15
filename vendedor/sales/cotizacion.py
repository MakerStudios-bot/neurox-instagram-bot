"""Generación de cotizaciones automáticas usando Claude"""

from database.models import Cotizacion
from ai.claude_client import call_claude
from config import APP_URL
import json


def generar_cotizacion(lead, db):
    """
    Genera una cotización automática basada en el contexto del lead.

    Args:
        lead: Objeto Lead con context (nombre, servicio_interesado, presupuesto)
        db: Sesión SQLAlchemy

    Returns:
        str: URL completa a la cotización (/cotizacion/{token})
    """

    context = lead.context or {}
    nombre_cliente = context.get("nombre", "Cliente")
    servicio = context.get("servicio_interesado", "Servicio")
    presupuesto = context.get("presupuesto", "No especificado")

    # Precios de servicios reales
    servicios_disponibles = {
        "página web": {"Landing Page": "$150.000", "Web Completa": "$350.000"},
        "landing page": {"Landing Page": "$150.000"},
        "web": {"Landing Page": "$150.000", "Web Completa": "$350.000"},
        "bot": {"Bot Automático Instagram (Sin IA)": "$110.000", "Bot Automático Instagram (Con IA)": "$180.000", "Membresía Bot Starter": "$24.000/mes", "Membresía Bot Pro": "$55.000/mes", "Membresía Bot Full": "$105.000/mes"},
        "bot instagram": {"Bot Automático Instagram (Sin IA)": "$110.000", "Bot Automático Instagram (Con IA)": "$180.000", "Membresía Bot Starter": "$24.000/mes", "Membresía Bot Pro": "$55.000/mes", "Membresía Bot Full": "$105.000/mes"},
        "bot ia": {"Bot Automático Instagram (Con IA)": "$180.000", "Membresía Bot Starter": "$24.000/mes", "Membresía Bot Pro": "$55.000/mes", "Membresía Bot Full": "$105.000/mes"},
        "bot sin ia": {"Bot Automático Instagram (Sin IA)": "$110.000", "Membresía Bot Starter": "$24.000/mes", "Membresía Bot Pro": "$55.000/mes", "Membresía Bot Full": "$105.000/mes"},
        "video": {"Por video": "$35.000", "4 videos": "$110.000", "8 videos": "$190.000"},
        "videos": {"Por video": "$35.000", "4 videos": "$110.000", "8 videos": "$190.000"},
        "edición": {"Por video": "$35.000", "4 videos": "$110.000", "8 videos": "$190.000"},
        "vendedor ia": {"Vendedor IA Starter (+ $55.000/mes)": "$230.000", "Vendedor IA Pro (+ $105.000/mes)": "$380.000", "Vendedor IA Elite (+ $160.000/mes)": "$580.000"},
        "sistema ventas": {"Vendedor IA Starter (+ $55.000/mes)": "$230.000", "Vendedor IA Pro (+ $105.000/mes)": "$380.000", "Vendedor IA Elite (+ $160.000/mes)": "$580.000"},
        "automatización": {"Vendedor IA Starter (+ $55.000/mes)": "$230.000", "Vendedor IA Pro (+ $105.000/mes)": "$380.000", "Vendedor IA Elite (+ $160.000/mes)": "$580.000"}
    }

    # Buscar servicios relevantes
    items_default = []
    for palabra_clave, opciones in servicios_disponibles.items():
        if palabra_clave in servicio.lower():
            for nombre_servicio, precio in opciones.items():
                items_default.append({"descripcion": nombre_servicio, "precio": precio})
            break

    # Si no encontró nada específico, usar un mensaje genérico
    if not items_default:
        items_default = [
            {"descripcion": "Consultoría inicial de servicios", "precio": "Gratis"}
        ]

    # Prompt para que Claude valide y genere JSON
    prompt_cotizacion = f"""
Genera una cotización profesional en JSON para un cliente.

Cliente: {nombre_cliente}
Servicio solicitado: {servicio}
Presupuesto mencionado: {presupuesto}

SERVICIOS DISPONIBLES (usa EXACTAMENTE los nombres y precios):
- Landing Page: $150.000
- Web Completa: $350.000
- Bot Automático Instagram (Sin IA): $110.000 inicial
- Bot Automático Instagram (Con IA): $180.000 inicial
- Membresía Bot Starter: $24.000/mes (500 conversaciones)
- Membresía Bot Pro: $55.000/mes (1.500 conversaciones, IA personalizada, reportes)
- Membresía Bot Full: $105.000/mes (4.000+ conversaciones, soporte 24/7)
- Por video (edición): $35.000
- 4 videos (paquete): $110.000
- 8 videos (paquete): $190.000
- Vendedor IA Starter: $230.000 inicial + $55.000/mes (hasta 500 conversaciones/mes)
- Vendedor IA Pro: $380.000 inicial + $105.000/mes (hasta 1500 conversaciones/mes)
- Vendedor IA Elite: $580.000 inicial + $160.000/mes (ilimitado)

Devuelve un JSON válido (SIN explicaciones, SOLO el JSON):
{{
    "items": [
        {{"descripcion": "Nombre del servicio exacto", "precio": "Precio exacto"}},
        {{"descripcion": "Otro servicio si es combo", "precio": "Precio"}}
    ],
    "total": "Total en formato $X.XXX",
    "notas": "Nota breve: validez de 30 días, próximos pasos"
}}

REGLAS IMPORTANTES:
- Solo usa servicios de la lista "SERVICIOS DISPONIBLES"
- NUNCA inventes servicios
- Los precios deben ser exactos, sin cambios
- Si el cliente pidió "desarrollo web" sugiere Web Completa
- Si pidió "bot" sugiere Bot Automático Instagram
- Si pidió "videos" sugiere edición de videos
- El total debe ser la suma de todos los items
"""

    try:
        response = call_claude(
            system_prompt="Eres un asesor de ventas experto. Generas cotizaciones profesionales en JSON válido.",
            messages=[{"role": "user", "content": prompt_cotizacion}]
        )

        # Parsear JSON de la respuesta
        # Claude a veces agrega caracteres antes del JSON, así que extraemos solo el JSON
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")

        json_str = json_match.group(0)
        coti_data = json.loads(json_str)

    except Exception as e:
        print(f"Error generando cotización con Claude: {e}")
        # Fallback: usar cotización por defecto según servicio detectado
        if items_default:
            total = "$0"  # Calcular total real
            coti_data = {
                "items": items_default,
                "total": total,
                "notas": "Cotización basada en tu solicitud. Válida por 30 días. Responde al chat para confirmar."
            }
        else:
            coti_data = {
                "items": [
                    {"descripcion": "Consultoría inicial de servicios Neurox", "precio": "Gratis"}
                ],
                "total": "$0",
                "notas": "Agendar una llamada para personalizar la cotización según tus necesidades."
            }

    # Crear registro en BD
    cotizacion = Cotizacion(
        lead_id=lead.id,
        servicio=servicio,
        presupuesto_cliente=presupuesto,
        items=coti_data.get("items", []),
        total=coti_data.get("total", "A consultar"),
        notas=coti_data.get("notas", "")
    )

    db.add(cotizacion)
    db.flush()  # Para obtener el token generado

    # Retornar URL completa
    url = f"{APP_URL}/cotizacion/{cotizacion.token}"
    print(f"✓ Cotización generada: {url}")
    return url
