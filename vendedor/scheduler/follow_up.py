"""Job automático de follow-up para leads sin respuesta"""

from datetime import datetime, timedelta
from database.models import Lead, Client, Message
from database import SessionLocal
from ai.handler import get_ai_response
from sales.messenger import send_dm
from sales.state_machine import apply_transition
from config import FOLLOW_UP_HOURS, MAX_FOLLOW_UPS


def run_follow_up_job():
    """
    Job que se ejecuta cada hora vía APScheduler.
    Busca leads que no han respondido en > FOLLOW_UP_HOURS
    y les envía un mensaje de seguimiento automático.
    """
    db = SessionLocal()

    try:
        print("\n⏰ Ejecutando follow-up job...")

        # Cutoff: hace N horas
        cutoff = datetime.utcnow() - timedelta(hours=FOLLOW_UP_HOURS)

        # Buscar leads que cumplen criterios
        leads_to_follow_up = db.query(Lead).filter(
            Lead.stage.in_(["CALIFICANDO", "COTIZADO"]),
            Lead.last_message_at < cutoff,
            Lead.follow_up_count < MAX_FOLLOW_UPS
        ).all()

        if not leads_to_follow_up:
            print("  No hay leads para follow-up")
            return

        print(f"  Encontrados {len(leads_to_follow_up)} leads sin respuesta")

        for lead in leads_to_follow_up:
            print(f"\n  Follow-up para lead {lead.id} ({lead.instagram_user_id}):")
            print(f"    Etapa actual: {lead.stage}")
            print(f"    Follow-ups previos: {lead.follow_up_count}")

            try:
                # Cambiar a FOLLOW_UP si no está ya
                if lead.stage != "FOLLOW_UP":
                    lead.stage = "FOLLOW_UP"
                    print(f"    → Transición a FOLLOW_UP")

                # Incrementar contador
                lead.follow_up_count += 1
                lead.last_message_at = datetime.utcnow()
                db.flush()

                # Generar mensaje de follow-up con IA
                follow_up_response = get_ai_response(
                    lead,
                    "[Sistema] Es hora de un seguimiento automático.",
                    db
                )

                # Extraer la respuesta limpia
                response_text = follow_up_response["response"]

                # Enviar DM
                success = send_dm(
                    page_id=lead.client.page_id,
                    access_token=lead.client.access_token,
                    user_id=lead.instagram_user_id,
                    message_text=response_text
                )

                if success:
                    print(f"    ✓ Follow-up #{lead.follow_up_count} enviado")

                    # Si alcanzó MAX_FOLLOW_UPS, marcar como cerrado
                    if lead.follow_up_count >= MAX_FOLLOW_UPS:
                        lead.stage = "CERRADO"
                        print(f"    ✓ Lead marcado como CERRADO (máx follow-ups alcanzados)")

                    db.commit()
                else:
                    print(f"    ❌ Error enviando follow-up")
                    db.rollback()

            except Exception as e:
                print(f"    ❌ Excepción en follow-up: {e}")
                db.rollback()

        print("\n✓ Follow-up job completado")

    except Exception as e:
        print(f"❌ Error en follow-up job: {e}")
    finally:
        db.close()
