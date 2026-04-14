#!/usr/bin/env python3
"""Setup rápido del cliente con page_id conocido"""

import os
from dotenv import load_dotenv

load_dotenv()

from database import SessionLocal, init_db
from database.models import Client

# Valores
PAGE_ID = "1423070465772043"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
BUSINESS_NAME = "Neurox"
CAL_LINK = "https://calendly.com/tu-link"

print("📁 Inicializando base de datos...")
init_db()

db = SessionLocal()
try:
    # Verificar si ya existe
    existing = db.query(Client).filter(Client.page_id == PAGE_ID).first()
    if existing:
        print(f"⚠️  Cliente ya existe")
        print(f"   ID: {existing.id}")
        print(f"   Page ID: {existing.page_id}")
        db.close()
        exit(0)

    # Crear cliente
    client = Client(
        page_id=PAGE_ID,
        access_token=ACCESS_TOKEN,
        business_name=BUSINESS_NAME,
        system_prompt=f"Eres vendedor de {BUSINESS_NAME}. Responde SIEMPRE en español, máximo 3 oraciones, sin listas con viñetas. Escribe como humano en un chat.",
        cal_link=CAL_LINK
    )
    db.add(client)
    db.commit()

    print(f"✅ Cliente creado!")
    print(f"   ID: {client.id}")
    print(f"   Page ID: {client.page_id}")
    print(f"   Nombre: {client.business_name}")
    print(f"\n📱 El webhook ya puede recibir mensajes")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()
