"""Entry point del sistema Vendedor IA — Flask + APScheduler"""

import atexit
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db
from webhooks.instagram import webhook
from dashboard.routes import dashboard
from scheduler.follow_up import run_follow_up_job
from config import PORT, FOLLOW_UP_JOB_INTERVAL
import os
import sys

# Agregar el directorio vendedor al path para imports locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# ==================
# Inicialización BD
# ==================
print("Inicializando base de datos...")
init_db()
print("✓ Base de datos lista")

# ==================
# Registrar blueprints
# ==================
app.register_blueprint(webhook)
app.register_blueprint(dashboard)


# ==================
# Endpoint de health check
# ==================
@app.route("/health", methods=["GET"])
def health():
    return {"status": "Vendedor IA running"}, 200


# ==================
# APScheduler - Follow-up automático
# ==================
scheduler = BackgroundScheduler(timezone="UTC")

# Job de follow-up cada N horas
scheduler.add_job(
    func=run_follow_up_job,
    trigger="interval",
    hours=FOLLOW_UP_JOB_INTERVAL,
    id="follow_up_job",
    name="Follow-up automático para leads sin respuesta"
)

print(f"Iniciando scheduler con job cada {FOLLOW_UP_JOB_INTERVAL}h...")
scheduler.start()
print("✓ Scheduler iniciado")


def shutdown_scheduler():
    """Apagar el scheduler al terminar la app"""
    if scheduler.running:
        print("\nApagando scheduler...")
        scheduler.shutdown()


atexit.register(shutdown_scheduler)


# ==================
# Main
# ==================
if __name__ == "__main__":
    print(f"\n🚀 Vendedor IA iniciando en puerto {PORT}...\n")
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
