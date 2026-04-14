"""Script para inicializar la base de datos con datos de prueba"""

from . import engine, SessionLocal, init_db
from .models import Client


def seed_database():
    """Crea las tablas y agrega un cliente de prueba"""
    print("Creando tablas...")
    init_db()
    print("✓ Tablas creadas")

    db = SessionLocal()

    # Verificar si ya existe el cliente de prueba
    client = db.query(Client).filter(Client.page_id == "test_page_123").first()

    if not client:
        print("Agregando cliente de prueba...")
        test_client = Client(
            page_id="test_page_123",
            access_token="test_token_123",
            business_name="Neurox Test",
            system_prompt="""Eres Neurox, una agencia de soluciones digitales.
Ofrecemos Bot IA ($230k), Web ($180k) y Videos ($35k).
Responde SIEMPRE en español, máximo 3 oraciones.
Al final escribe: [SIGNAL: CALIFICAR|AGENDAR|COTIZAR|CERRAR]""",
            cal_link="https://cal.com/test"
        )
        db.add(test_client)
        db.commit()
        print("✓ Cliente de prueba agregado")
        print(f"  page_id: {test_client.page_id}")
        print(f"  access_token: {test_client.access_token}")
    else:
        print("✓ Cliente de prueba ya existe")

    db.close()
    print("\nBase de datos inicializada correctamente ✅")


if __name__ == "__main__":
    seed_database()
