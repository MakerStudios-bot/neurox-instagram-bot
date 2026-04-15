"""Generación de cotizaciones automáticas con servicios Neurox"""

from database.models import Cotizacion
from config import APP_URL


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

    # DEBUG: mostrar el contexto completo
    print(f"\n=== GENERAR COTIZACIÓN ===")
    print(f"Lead ID: {lead.id}")
    print(f"Contexto completo: {context}")
    print(f"Servicio detectado: '{servicio}'")
    print(f"Nombre: '{nombre_cliente}'")
    print(f"Presupuesto: '{presupuesto}'")
    print(f"=========================\n")

    # Precios de servicios reales
    servicios_disponibles = {
        # Web - específico
        "web_completa": [
            {"descripcion": "Web Completa", "precio": "$350.000"}
        ],
        "landing_page": [
            {"descripcion": "Landing Page", "precio": "$150.000"}
        ],

        # Web - genérico (cuando no especifica cuál)
        "página web": [
            {"descripcion": "Landing Page", "precio": "$150.000"},
            {"descripcion": "Web Completa", "precio": "$350.000"}
        ],
        "landing page": [
            {"descripcion": "Landing Page", "precio": "$150.000"}
        ],
        "web": [
            {"descripcion": "Landing Page", "precio": "$150.000"},
            {"descripcion": "Web Completa", "precio": "$350.000"}
        ],
        # Bot - específico
        "bot_con_ia": [
            {"descripcion": "Bot Automático Instagram (Con IA)", "precio": "$180.000"},
            {"descripcion": "Membresía Bot Starter", "precio": "$24.000/mes"},
            {"descripcion": "Membresía Bot Pro", "precio": "$55.000/mes"},
            {"descripcion": "Membresía Bot Full", "precio": "$105.000/mes"}
        ],
        "bot_sin_ia": [
            {"descripcion": "Bot Automático Instagram (Sin IA)", "precio": "$110.000"},
            {"descripcion": "Membresía Bot Starter", "precio": "$24.000/mes"},
            {"descripcion": "Membresía Bot Pro", "precio": "$55.000/mes"},
            {"descripcion": "Membresía Bot Full", "precio": "$105.000/mes"}
        ],

        # Bot - genérico (cuando no especifica con/sin IA)
        "bot": [
            {"descripcion": "Bot Automático Instagram (Sin IA)", "precio": "$110.000"},
            {"descripcion": "Bot Automático Instagram (Con IA)", "precio": "$180.000"},
            {"descripcion": "Membresía Bot Starter", "precio": "$24.000/mes"},
            {"descripcion": "Membresía Bot Pro", "precio": "$55.000/mes"},
            {"descripcion": "Membresía Bot Full", "precio": "$105.000/mes"}
        ],
        "bot instagram": [
            {"descripcion": "Bot Automático Instagram (Sin IA)", "precio": "$110.000"},
            {"descripcion": "Bot Automático Instagram (Con IA)", "precio": "$180.000"},
            {"descripcion": "Membresía Bot Starter", "precio": "$24.000/mes"},
            {"descripcion": "Membresía Bot Pro", "precio": "$55.000/mes"},
            {"descripcion": "Membresía Bot Full", "precio": "$105.000/mes"}
        ],
        "bot ia": [
            {"descripcion": "Bot Automático Instagram (Con IA)", "precio": "$180.000"},
            {"descripcion": "Membresía Bot Starter", "precio": "$24.000/mes"},
            {"descripcion": "Membresía Bot Pro", "precio": "$55.000/mes"},
            {"descripcion": "Membresía Bot Full", "precio": "$105.000/mes"}
        ],
        "bot sin ia": [
            {"descripcion": "Bot Automático Instagram (Sin IA)", "precio": "$110.000"},
            {"descripcion": "Membresía Bot Starter", "precio": "$24.000/mes"},
            {"descripcion": "Membresía Bot Pro", "precio": "$55.000/mes"},
            {"descripcion": "Membresía Bot Full", "precio": "$105.000/mes"}
        ],
        "video": [
            {"descripcion": "Por video", "precio": "$35.000"},
            {"descripcion": "4 videos", "precio": "$110.000"},
            {"descripcion": "8 videos", "precio": "$190.000"}
        ],
        "videos": [
            {"descripcion": "Por video", "precio": "$35.000"},
            {"descripcion": "4 videos", "precio": "$110.000"},
            {"descripcion": "8 videos", "precio": "$190.000"}
        ],
        "edición": [
            {"descripcion": "Por video", "precio": "$35.000"},
            {"descripcion": "4 videos", "precio": "$110.000"},
            {"descripcion": "8 videos", "precio": "$190.000"}
        ],
        # Vendedor IA
        "vendedor_ia": [
            {"descripcion": "Vendedor IA Starter", "precio": "$230.000 + $55.000/mes"},
            {"descripcion": "Vendedor IA Pro", "precio": "$380.000 + $105.000/mes"},
            {"descripcion": "Vendedor IA Elite", "precio": "$580.000 + $160.000/mes"}
        ],
        "vendedor ia": [
            {"descripcion": "Vendedor IA Starter", "precio": "$230.000 + $55.000/mes"},
            {"descripcion": "Vendedor IA Pro", "precio": "$380.000 + $105.000/mes"},
            {"descripcion": "Vendedor IA Elite", "precio": "$580.000 + $160.000/mes"}
        ],
        "sistema ventas": [
            {"descripcion": "Vendedor IA Starter", "precio": "$230.000 + $55.000/mes"},
            {"descripcion": "Vendedor IA Pro", "precio": "$380.000 + $105.000/mes"},
            {"descripcion": "Vendedor IA Elite", "precio": "$580.000 + $160.000/mes"}
        ],
        "automatización": [
            {"descripcion": "Vendedor IA Starter", "precio": "$230.000 + $55.000/mes"},
            {"descripcion": "Vendedor IA Pro", "precio": "$380.000 + $105.000/mes"},
            {"descripcion": "Vendedor IA Elite", "precio": "$580.000 + $160.000/mes"}
        ]
    }

    # Buscar servicios relevantes por palabra clave
    items_default = []
    servicio_lower = servicio.lower()
    for palabra_clave, opciones in servicios_disponibles.items():
        if palabra_clave in servicio_lower:
            items_default = opciones.copy()
            break

    # Si no encontró nada específico, ofrecer una selección de todos los servicios
    if not items_default:
        print(f"⚠️  No se encontró coincidencia para '{servicio}', mostrando opciones generales")
        items_default = [
            {"descripcion": "Páginas Web - Landing Page", "precio": "$150.000"},
            {"descripcion": "Bot Automático Instagram (Con IA)", "precio": "$180.000"},
            {"descripcion": "Edición de Videos", "precio": "$35.000 por video"}
        ]

    # Calcular total (solo para items sin "/mes")
    def calcular_total(items):
        total_num = 0
        for item in items:
            precio = item.get("precio", "0")
            # Extraer número del precio (solo si no es /mes)
            if "/mes" not in precio:
                try:
                    # Remover $ y puntos de formato
                    num = precio.replace("$", "").replace(".", "").split("+")[0].strip()
                    total_num += int(num)
                except:
                    pass

        if total_num > 0:
            return f"${total_num:,}".replace(",", ".")
        return "A consultar"

    coti_data = {
        "items": items_default,
        "total": calcular_total(items_default),
        "notas": "Cotización válida por 30 días. Responde al chat para confirmar o hacer preguntas."
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
    print(f"✓ Cotización generada para '{nombre_cliente}' - Servicio: {servicio}")
    print(f"  Items: {len(coti_data.get('items', []))} | Total: {coti_data.get('total', 'A consultar')}")
    print(f"  URL: {url}")
    return url
