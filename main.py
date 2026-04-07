import os
import json
import hmac
import hashlib
import requests
from flask import Flask, request
from ai_handler import get_ai_response
from responses import get_fixed_response

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "your_verify_token")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
APP_SECRET = os.getenv("APP_SECRET", "")


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return handle_verification(request)
    elif request.method == "POST":
        return handle_message(request)


def verify_hmac_signature(req):
    """Verifica la firma HMAC de Meta para mayor seguridad"""
    if not APP_SECRET:
        print("⚠️ APP_SECRET no configurado - omitiendo validación HMAC")
        return True

    signature = req.headers.get("X-Hub-Signature-256", "")
    body = req.data  # Usar request.data para obtener bytes RAW

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
        print(f"❌ Firma HMAC inválida. Expected: {expected_signature}, Got: {signature}")
    return is_valid


def handle_verification(req):
    """Verifica el webhook con Meta"""
    mode = req.args.get("hub.mode")
    token = req.args.get("hub.verify_token")
    challenge = req.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado")
        return challenge, 200
    else:
        return "Forbidden", 403


def handle_message(req):
    """Procesa mensajes entrantes de Instagram"""
    try:
        # Verificar firma HMAC
        if not verify_hmac_signature(req):
            print("❌ Firma HMAC inválida - rechazando solicitud")
            return "Forbidden", 403

        data = req.get_json()

        # Verificar que sea el tipo de evento correcto
        if data.get("object") != "instagram":
            return "OK", 200

        # Extraer el mensaje
        entry = data.get("entry", [{}])[0]
        messaging = entry.get("messaging", [])

        for msg in messaging:
            sender_id = msg.get("sender", {}).get("id")
            message_text = msg.get("message", {}).get("text")

            if sender_id and message_text:
                # Buscar respuesta fija primero
                response_text = get_fixed_response(message_text)

                # Si no hay respuesta fija, usar IA con historial
                if response_text is None:
                    response_text = get_ai_response(sender_id, message_text)

                # Enviar respuesta
                send_message(sender_id, response_text)

        return "OK", 200
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return "OK", 200


def send_message(recipient_id, message_text):
    """Envía un mensaje via Instagram DM"""
    url = f"https://graph.instagram.com/v19.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/messages"

    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    params = {"access_token": ACCESS_TOKEN}

    response = requests.post(url, json=payload, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error enviando mensaje: {response.text}")
    else:
        print(f"Mensaje enviado a {recipient_id}")


@app.route("/", methods=["GET"])
def health():
    """Health check endpoint"""
    return {"status": "Bot running"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
