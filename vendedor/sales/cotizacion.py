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

    # Prompt para que Claude genere items de cotización en JSON
    prompt_cotizacion = f"""
Genera una cotización profesional en JSON para un cliente.

Cliente: {nombre_cliente}
Servicio: {servicio}
Presupuesto mencionado: {presupuesto}

Devuelve un JSON válido con esta estructura (SIN explicaciones, SOLO el JSON):
{{
    "items": [
        {{"descripcion": "Descripción del servicio 1", "precio": "precio en formato $X.XX"}},
        {{"descripcion": "Descripción del servicio 2", "precio": "precio en formato $X.XX"}}
    ],
    "total": "Total en formato $X.XX",
    "notas": "Nota breve sobre validez de cotización o próximos pasos"
}}

Crea entre 2-4 items que sean relevantes para el servicio y presupuesto mencionado.
Los precios deben ser razonables pero premium (no descuentos, precio normal de mercado).
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
        # Fallback: cotización genérica
        coti_data = {
            "items": [
                {"descripcion": f"{servicio} - Consultoría", "precio": "$500.00"},
                {"descripcion": f"{servicio} - Implementación", "precio": "$1,500.00"}
            ],
            "total": "$2,000.00",
            "notas": "Cotización preliminar. Sujeta a confirmación tras revisión detallada."
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
