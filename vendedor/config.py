"""Configuración centralizada del sistema"""

import os
from dotenv import load_dotenv

load_dotenv()

# Meta Instagram API
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "test_verify_token")
APP_SECRET = os.getenv("APP_SECRET", "test_secret")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
APP_URL = os.getenv("APP_URL", "https://neurox-instagram-bot-production.up.railway.app")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # Modelo económico
MAX_TOKENS = 500
MAX_HISTORY = 20  # Últimos 20 mensajes en historial

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///vendedor.db")

# Dashboard Admin
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "changeme")

# Calendly
CAL_LINK = os.getenv("CAL_LINK", "https://calendly.com/neurox-contacto/new-meeting")

# Scheduler
FOLLOW_UP_HOURS = 24  # Esperar 24h antes de enviar follow-up
MAX_FOLLOW_UPS = 2  # Máximo 2 mensajes de seguimiento por lead
FOLLOW_UP_JOB_INTERVAL = 1  # Cada hora

# Server
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False") == "True"
