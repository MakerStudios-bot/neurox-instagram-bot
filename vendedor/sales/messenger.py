"""Envío de mensajes vía Meta Graph API"""

import requests
from typing import Optional


def send_dm(page_id: str, access_token: str, user_id: str, message_text: str) -> bool:
    """
    Envía un DM a un usuario de Instagram vía Meta Graph API.

    Args:
        page_id: ID de la página de negocios Instagram
        access_token: token de acceso Meta
        user_id: ID del usuario destinatario en Instagram
        message_text: contenido del mensaje

    Returns:
        True si se envió correctamente, False si falló
    """

    url = f"https://graph.instagram.com/v18.0/{page_id}/messages"

    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message_text}
    }
    params = {"access_token": access_token}

    try:
        response = requests.post(url, json=payload, headers=headers, params=params)

        if response.status_code == 200:
            print(f"✓ DM enviado a {user_id}")
            return True
        else:
            print(f"❌ Error enviando DM a {user_id}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Excepción enviando DM: {e}")
        return False
