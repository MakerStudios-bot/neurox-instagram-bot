# Vendedor IA — Pipeline de Ventas 100% Automático por Instagram DMs

Sistema de pipeline de ventas completamente automatizado que funciona por Instagram DMs. Usa Claude IA (Haiku) para respuestas inteligentes, state machine para etapas de leads, y sigue automáticos para leads sin respuesta.

## Características

- ✅ **State Machine**: NUEVO → CALIFICANDO → AGENDADO → COTIZADO → FOLLOW_UP → CERRADO
- ✅ **IA Adaptativa**: System prompt diferente por etapa (personalizable por cliente)
- ✅ **Multi-tenant**: Múltiples clientes con sus propios settings, prompts y leads aislados
- ✅ **Follow-up Automático**: Job horario que detecta leads sin respuesta y envía seguimiento (máx 2)
- ✅ **Dashboard Admin**: Lista de leads + historial + cierre manual (con Basic Auth)
- ✅ **Base de Datos**: SQLite con SQLAlchemy ORM (migrable a Postgres)
- ✅ **Webhook Instagram**: Recibe DMs de Meta Graph API, orquesta todo, envía respuestas

## Tech Stack

- Python 3.9 + Flask
- SQLAlchemy ORM + SQLite
- Anthropic Claude Haiku 4.5 (económico)
- APScheduler (jobs automáticos)
- Meta Graph API v18
- Railway (deployment)

## Local Setup

```bash
cd vendedor

# Crear .env
cp .env.example .env
# Editar .env con tus keys

# Instalar dependencias
pip install -r requirements.txt

# Inicializar BD
python database/seed.py

# Correr
PORT=5000 python app.py
```

Luego:
- Webhook: `POST http://localhost:5000/webhook`
- Health: `GET http://localhost:5000/health`
- Dashboard: `http://localhost:5000/admin/leads` (admin/changeme)

## Deploy en Railway

1. Conectar repo a Railway
2. Crear nueva service
3. Configurar variables de entorno:
   ```
   VERIFY_TOKEN=tu_verify_token
   APP_SECRET=tu_app_secret
   ANTHROPIC_API_KEY=sk-ant-...
   ADMIN_USER=admin
   ADMIN_PASS=tu_contraseña_fuerte
   PORT=5000
   ```
4. Build command: `cd vendedor && pip install -r requirements.txt`
5. Start command: `cd vendedor && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
6. Deploy

## Conectar a Instagram (Meta)

1. Ir a Meta for Developers
2. Crear app (o usar existente)
3. Configurar webhook:
   - Callback URL: `https://tu-app.railway.app/webhook`
   - Verify Token: el de tu .env (VERIFY_TOKEN)
4. Suscribirse a eventos `messages` de Instagram
5. Obtener:
   - ACCESS_TOKEN (token de página)
   - INSTAGRAM_BUSINESS_ACCOUNT_ID (ID de la página)
   - APP_SECRET
6. Guardar en `.env` y redeploy

## Modelos de Datos

### Client (tenant)
- `page_id`: ID de página Instagram (identificador único del cliente)
- `access_token`: Token Meta para enviar DMs
- `business_name`: Nombre del negocio
- `system_prompt`: Prompt base personalizado
- `cal_link`: Link a Cal.com o Calendly

### Lead
- `instagram_user_id`: ID del usuario en Instagram
- `client_id`: Cliente propietario del lead
- `stage`: Una de 6 etapas (NUEVO, CALIFICANDO, AGENDADO, COTIZADO, FOLLOW_UP, CERRADO)
- `context`: JSON con datos extraídos (nombre, servicio, presupuesto, etc.)
- `follow_up_count`: Número de mensajes de seguimiento enviados
- `last_message_at`: Cuándo respondió por última vez

### Message
- `lead_id`: Lead propietario
- `role`: "user" o "assistant"
- `content`: Contenido del mensaje

## Cómo Funciona

1. **Webhook recibe DM** → valida que sea del cliente → busca/crea Lead
2. **Get AI Response** → carga historial de DB → crea prompt dinámico → llama Claude
3. **Parse Signal** → Claude incluye `[SIGNAL: AGENDAR]` al final → sistema lo extrae
4. **State Machine** → evalúa si debe cambiar etapa basado en signal
5. **Send DM** → envía respuesta limpia al usuario via Meta API
6. **Persiste todo** → guarda mensajes y estado en DB

## Sistema de Signals

Cada respuesta de Claude termina con:
```
[SIGNAL: CALIFICAR|AGENDAR|COTIZAR|CERRAR]
```

Esto permite transiciones automáticas SIN llamadas LLM extras. El webhook parsea, aplica la transición, limpia el tag, y envía solo el mensaje al usuario.

## Follow-up Automático

APScheduler corre cada hora:
1. Busca leads en CALIFICANDO/COTIZADO que llevan >24h sin responder
2. Si `follow_up_count < 2`:
   - Cambia a FOLLOW_UP
   - Genera mensaje con prompt especial
   - Envía DM
   - Incrementa contador
3. Si `follow_up_count >= 2` → marca como CERRADO automáticamente

## Dashboard Admin

Acceso en `/admin`:
- `/admin/leads` — tabla con todos los leads
- `/admin/lead/<id>` — conversación completa + botón cerrar
- `/admin/lead/<id>/close` — cierra lead (won/lost)

Protected con Basic Auth. Credenciales en `.env`.

## Variables de Entorno

```env
# Meta/Instagram
VERIFY_TOKEN=token_para_verificar_webhook
APP_SECRET=secret_de_tu_app_meta

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=sqlite:///vendedor.db

# Admin
ADMIN_USER=admin
ADMIN_PASS=tu_contraseña

# Server
PORT=5000
DEBUG=False
```

## Próximas Mejoras

- [ ] Exportar leads a CSV/Google Sheets
- [ ] Webhooks hacia sistemas CRM (Pipedrive, etc.)
- [ ] Análisis de conversión y ROI por lead
- [ ] A/B testing de prompts
- [ ] Integración con Cal.com API (auto-enviar confirmación)
- [ ] Soporte para múltiples canales (WhatsApp, Telegram)
- [ ] Custom domains para Cal.com por cliente

---

Hecho con ❤️ por Claude
