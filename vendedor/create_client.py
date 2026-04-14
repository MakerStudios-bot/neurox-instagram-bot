#!/usr/bin/env python3
"""Script para crear automáticamente un cliente en la BD"""

import os
import sys
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from database import SessionLocal, init_db
from database.models import Client

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
BUSINESS_NAME = "Neurox"
CAL_LINK = "https://calendly.com/tu-link"

if not ACCESS_TOKEN:
    print("❌ ACCESS_TOKEN no configurado en .env")
    sys.exit(1)

print("🔍 Obteniendo page_id desde Meta...")

# Obtener el page_id (instagram_business_account_id)
try:
    response = requests.get(
        f"https://graph.instagram.com/me/instagram_business_account",
        params={"access_token": ACCESS_TOKEN}
    )
    data = response.json()

    if "error" in data:
        print(f"❌ Error de Meta: {data['error'].get('message', 'unknown')}")
        sys.exit(1)

    page_id = data.get("instagram_business_account", {}).get("id")
    if not page_id:
        print("❌ No se pudo obtener el page_id de Meta")
        print(f"Respuesta: {data}")
        sys.exit(1)

    print(f"✓ page_id obtenido: {page_id}")
except Exception as e:
    print(f"❌ Error obteniendo page_id: {e}")
    sys.exit(1)

# Inicializar BD
print("📁 Inicializando base de datos...")
init_db()

# Crear cliente
db = SessionLocal()
try:
    # Verificar si ya existe
    existing = db.query(Client).filter(Client.page_id == page_id).first()
    if existing:
        print(f"⚠️  Cliente ya existe con page_id {page_id}")
        print(f"   ID: {existing.id}")
        print(f"   Nombre: {existing.business_name}")
        db.close()
        sys.exit(0)

    # Crear nuevo cliente
    client = Client(
        page_id=page_id,
        access_token=ACCESS_TOKEN,
        business_name=BUSINESS_NAME,
        system_prompt=f"Eres vendedor de {BUSINESS_NAME}. Responde SIEMPRE en español, máximo 3 oraciones, sin listas con viñetas.",
        cal_link=CAL_LINK
    )
    db.add(client)
    db.commit()

    print(f"✅ Cliente creado exitosamente!")
    print(f"   ID: {client.id}")
    print(f"   Page ID: {client.page_id}")
    print(f"   Nombre: {client.business_name}")
    print(f"\n📱 Ahora el webhook puede recibir mensajes de Instagram")

    db.close()
except Exception as e:
    db.rollback()
    print(f"❌ Error creando cliente: {e}")
    sys.exit(1)
