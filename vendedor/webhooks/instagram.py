"""Webhook de Instagram — punto de entrada del sistema"""

import hmac
import hashlib
import json
from flask import Blueprint, request, Response
from database import SessionLocal
from database.models import Client, Lead, Message
from ai.handler import get_ai_response
from ai.auto_responder import get_auto_response
from sales.messenger import send_dm
from sales.state_machine import extract_signal, should_transition, apply_transition
from config import VERIFY_TOKEN, APP_SECRET, CAL_LINK, BOT_MODE, ASSISTANT_NAME
from datetime import datetime
import os

webhook = Blueprint("webhook", __name__)


def verify_hmac_signature(req):
    """Verifica que el request viene de Meta (válida firma HMAC)"""
    if not APP_SECRET:
        print("⚠️  APP_SECRET no configurado, omitiendo validación HMAC")
        return True

    signature = req.headers.get("X-Hub-Signature-256", "")
    body = req.data

    if not signature:
        print("❌ No se encontró firma HMAC")
        return False

    expected_signature = "sha256=" + hmac.new(
        APP_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(signature, expected_signature)
    if not is_valid:
        print(f"❌ Firma HMAC inválida")
    return is_valid


@webhook.route("/webhook", methods=["GET"])
def webhook_verify():
    """Verifica el webhook con Meta (handshake inicial)"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"🔍 Webhook verification request:")
    print(f"   mode={mode}, token={token}, challenge={challenge}")
    print(f"   Expected VERIFY_TOKEN: {VERIFY_TOKEN}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado con Meta")
        return challenge, 200
    else:
        print(f"❌ Webhook verification fallido. Token mismatch: '{token}' != '{VERIFY_TOKEN}'")
        return "Forbidden", 403


@webhook.route("/webhook", methods=["POST"])
def webhook_handle():
    """Recibe DMs de Instagram y orquesta el pipeline completo"""
    try:
        # 1. Validar firma de Meta (desactivado temporalmente)
        # if not verify_hmac_signature(request):
        #     print("❌ Firma HMAC inválida, rechazando")
        #     return "Forbidden", 403

        data = request.get_json()

        # 2. Validar que sea el objeto correcto
        if data.get("object") != "instagram":
            return "OK", 200

        # 3. Extraer datos del mensaje
        entry = data.get("entry", [{}])[0]
        messaging = entry.get("messaging", [])

        if not messaging:
            return "OK", 200

        for msg in messaging:
            db = None  # Inicializar a None para evitar UnboundLocalError en finally
            try:
                sender_id = msg.get("sender", {}).get("id")
                message_text = msg.get("message", {}).get("text")

                # Ignore si falta info (reacciones, stickers, media sin texto, etc.)
                if not sender_id or not message_text:
                    continue

                # Extraer page_id del recipient (la cuenta que recibe el DM)
                page_id = msg.get("recipient", {}).get("id")

                print(f"\n📨 DM recibido: {sender_id} → {page_id}")
                print(f"   Texto: {message_text[:50]}...")

                # 4. Buscar el cliente por page_id (o crear si no existe)
                db = SessionLocal()
                client = db.query(Client).filter(Client.page_id == page_id).first()

                if not client:
                    print(f"⚠️  Cliente no encontrado, creando automáticamente...")
                    from config import ACCESS_TOKEN as DEFAULT_ACCESS_TOKEN

                    # Modo Restaurante Napoleon
                    if BOT_MODE == "napoleon":
                        biz_name = "Restaurante Napoleon"
                        biz_prompt = f"""Eres {ASSISTANT_NAME}, el anfitrión amable y formal del Restaurante Napoleon, un espacio gastronómico de excelencia.

Tu objetivo es:
1. Recibir clientes con cortesía y profesionalismo
2. Presentar nuestros platos y especialidades
3. Resolver preguntas sobre reservas y disponibilidad
4. Facilitar la reserva de mesas

NUESTROS PLATOS DESTACADOS:
🍽️ ENTRADA
- Tabla de quesos y embutidos: $18.000
- Camarones al ajillo: $16.000

🍝 PLATOS PRINCIPALES
- Filete a la pimienta: $32.000
- Pechuga de pollo rellena: $26.000
- Salmón a la mantequilla: $34.000
- Pasta Napoleón (especialidad): $24.000

🍷 BEBIDAS
- Vino tinto chileno: $15.000
- Vino blanco: $14.000
- Agua mineral/gaseosa: $3.000

HORARIOS: Lunes-Viernes 12:00-23:00 | Sábados 12:00-00:00 | Domingos 12:00-22:00

INSTRUCCIONES: Responde en español, máximo 3 oraciones. Sé amable, formal y profesional. Nunca menciones que eres IA. Sugiere platos según lo que el cliente busca."""

                    # Modo Bodylab para demostración
                    elif BOT_MODE == "bodylab_demo":
                        biz_name = "Bodylab Cosmetica"
                        biz_prompt = f"""Eres {ASSISTANT_NAME}, un asistente amable y profesional de Bodylab Cosmetica, un centro de estética integral especializado en masajes, depilación y manicure.

Tu objetivo es:
1. Recibir clientes con calidez y profesionalismo
2. Entender qué servicio les interesa
3. Proporcionar información sobre precios y disponibilidad
4. Agendar citas en los horarios disponibles

SERVICIOS:
💆 MASAJES - Relajante ($25k), Descontracturante ($30k), Facial ($20k)
🪶 DEPILACIÓN - Brasileña ($35k), Piernas ($40k)
💅 MANICURE - Manicure ($15k), Pedicure ($18k)

HORARIOS: Lunes-Viernes 09:00-18:00 | Sábado 09:00-16:00 | Domingo Cerrado

Responde SIEMPRE en español, máximo 3 oraciones, sin listas. NUNCA menciones que eres IA. Sé amable y profesional."""
                    else:
                        # Modo Neurox normal
                        biz_name = os.getenv("BUSINESS_NAME", "Neurox")
                        biz_prompt = os.getenv("SYSTEM_PROMPT", f"Eres vendedor de {biz_name}. Responde SIEMPRE en español, máximo 3 oraciones, sin listas con viñetas.")

                    client = Client(
                        page_id=page_id,
                        access_token=DEFAULT_ACCESS_TOKEN or "",
                        business_name=biz_name,
                        system_prompt=biz_prompt,
                        cal_link=os.getenv("CAL_LINK", CAL_LINK)
                    )
                    db.add(client)
                    db.flush()
                    print(f"✓ Cliente creado automáticamente: {client.id}")

                # Sobrescribir prompt si BOT_MODE lo requiere (incluso para clientes existentes)
                if BOT_MODE == "napoleon":
                    napoleon_prompt = f"""Eres {ASSISTANT_NAME}, el anfitrión amable y formal del Restaurante Napoleon, un espacio gastronómico de excelencia.

Tu objetivo es:
1. Recibir clientes con cortesía y profesionalismo
2. Presentar nuestros platos y especialidades
3. Resolver preguntas sobre reservas y disponibilidad
4. Facilitar la reserva de mesas

NUESTROS PLATOS DESTACADOS:
🍽️ ENTRADA
- Tabla de quesos y embutidos: $18.000
- Camarones al ajillo: $16.000

🍝 PLATOS PRINCIPALES
- Filete a la pimienta: $32.000
- Pechuga de pollo rellena: $26.000
- Salmón a la mantequilla: $34.000
- Pasta Napoleón (especialidad): $24.000

🍷 BEBIDAS
- Vino tinto chileno: $15.000
- Vino blanco: $14.000
- Agua mineral/gaseosa: $3.000

HORARIOS: Lunes-Viernes 12:00-23:00 | Sábados 12:00-00:00 | Domingos 12:00-22:00

INSTRUCCIONES: Responde en español, máximo 3 oraciones. Sé amable, formal y profesional. Nunca menciones que eres IA. Sugiere platos según lo que el cliente busca."""
                    client.system_prompt = napoleon_prompt
                    client.business_name = "Restaurante Napoleon"
                    db.flush()  # Guardar cambios del cliente en la BD

                # 5. Buscar o crear el lead
                lead = db.query(Lead).filter(
                    Lead.instagram_user_id == sender_id,
                    Lead.client_id == client.id
                ).first()

                if not lead:
                    # Crear nuevo lead
                    lead = Lead(
                        instagram_user_id=sender_id,
                        client_id=client.id,
                        stage="NUEVO"
                    )
                    db.add(lead)
                    db.flush()
                    print(f"✓ Nuevo lead creado: {lead.id}")
                else:
                    print(f"✓ Lead existente: {lead.id} (etapa: {lead.stage})")

                # 6. Si el lead está CERRADO, ignorar
                if lead.stage == "CERRADO":
                    print(f"  Lead está CERRADO, ignorando mensaje")
                    db.close()
                    continue

                # 7. Actualizar last_message_at
                lead.last_message_at = datetime.utcnow()

                # 8. Obtener respuesta (IA o automática según tipo de servicio)
                tipo_servicio = os.getenv("TIPO_SERVICIO", "")
                signal = None

                if tipo_servicio == "bot_automatico_sin_ia":
                    print(f"  Respuesta automática (sin IA)...")
                    response_text = get_auto_response(message_text)
                else:
                    print(f"  Llamando IA...")
                    ai_result = get_ai_response(lead, message_text, db)
                    response_text = ai_result["response"]
                    signal = ai_result["signal"]

                print(f"  Signal extraído: {signal}")

                # 9. Evaluar transición de etapa
                if signal:
                    should_trans, new_stage = should_transition(lead, signal)
                    if should_trans:
                        apply_transition(lead, new_stage, db)

                # 10. Enviar DM al usuario
                print(f"  Enviando DM...")
                send_dm(
                    page_id=client.page_id,
                    access_token=client.access_token,
                    user_id=sender_id,
                    message_text=response_text
                )

                # 11. Guardar cambios
                db.commit()
                print(f"✓ Pipeline completado para lead {lead.id}")

            except Exception as e:
                print(f"❌ Error procesando mensaje: {e}")
                if db is not None:
                    db.rollback()
                continue
            finally:
                if db is not None:
                    db.close()

        return "OK", 200

    except Exception as e:
        print(f"❌ Error en webhook_handle: {e}")
        return "OK", 200
