"""Webhook de Instagram — punto de entrada del sistema"""

import hmac
import hashlib
import json
from flask import Blueprint, request, Response
from database import SessionLocal
from database.models import Client, Lead, Message
from ai.handler import get_ai_response
from sales.messenger import send_dm
from sales.state_machine import extract_signal, should_transition, apply_transition
from sales.cotizacion import generar_cotizacion
from config import VERIFY_TOKEN, APP_SECRET
from datetime import datetime

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
                    # Crear cliente automáticamente
                    from config import ACCESS_TOKEN as DEFAULT_ACCESS_TOKEN
                    client = Client(
                        page_id=page_id,
                        access_token=DEFAULT_ACCESS_TOKEN or "",
                        business_name="Neurox",
                        system_prompt="Eres vendedor. Responde SIEMPRE en español, máximo 3 oraciones, sin listas con viñetas.",
                        cal_link="https://calendly.com"
                    )
                    db.add(client)
                    db.flush()
                    print(f"✓ Cliente creado automáticamente: {client.id}")

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

                # 8. Obtener respuesta de IA
                print(f"  Llamando IA...")
                ai_result = get_ai_response(lead, message_text, db)
                response_text = ai_result["response"]
                signal = ai_result["signal"]

                print(f"  Signal extraído: {signal}")

                # 9. Evaluar transición de etapa
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

                # 11. Si signal es COTIZAR, generar cotización y enviar link
                if signal == "COTIZAR":
                    print(f"  Signal COTIZAR detectado, generando cotización...")
                    try:
                        coti_url = generar_cotizacion(lead, db)
                        # Enviar segundo DM con el link
                        coti_message = f"Aquí está tu cotización personalizada:\n{coti_url}"
                        send_dm(
                            page_id=client.page_id,
                            access_token=client.access_token,
                            user_id=sender_id,
                            message_text=coti_message
                        )
                        print(f"  ✓ Cotización enviada: {coti_url}")
                    except Exception as e:
                        print(f"  ❌ Error generando cotización: {e}")

                # 12. Guardar cambios
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
