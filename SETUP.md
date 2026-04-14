# 🚀 Guía de Configuración — Vendedor IA

## Paso 1: Obtener credenciales de Meta (5 minutos)

1. Ve a https://developers.facebook.com/
2. **Crear nueva app** (si no tienes una):
   - Tipo: "Business"
   - Nombre: "Neurox" (o el que prefieras)

3. **Agregar producto "Messenger"**:
   - En tu app → Agregar producto
   - Busca "Messenger"
   - Click en "Configurar"

4. **Obtener credenciales**:
   - Ve a **Messenger** → **Settings**
   - Copia el **Access Token** (token de tu página de Instagram)
   - Ve a **Settings** → **Basic** 
   - Copia el **App Secret**

5. **Obtener INSTAGRAM_BUSINESS_ACCOUNT_ID** (si lo necesitas):
   ```bash
   curl "https://graph.instagram.com/me/instagram_business_account?access_token=TU_ACCESS_TOKEN"
   ```
   Devuelve algo como: `{"instagram_business_account": {"id": "17841480693267452"}}`

**Guarda estos 3 valores:**
- `VERIFY_TOKEN` (lo creas tú: cualquier string aleatorio, ej: "mi_token_secreto_123")
- `APP_SECRET` (de Meta)
- `ANTHROPIC_API_KEY` (de https://console.anthropic.com/)

---

## Paso 2: Deploy a Railway (1 click)

1. **Ve a README.md** en este repo
2. **Haz click en el botón "Deploy on Railway"** (azul grande)
3. **Autoriza con tu cuenta de Railway** (crear si no tienes)
4. **Completa las variables de entorno**:
   - `VERIFY_TOKEN` → el que creaste
   - `APP_SECRET` → de Meta
   - `ANTHROPIC_API_KEY` → de Anthropic
   - `ADMIN_USER` → dejar como "admin"
   - `ADMIN_PASS` → crear una contraseña fuerte
   - `PORT` → dejar como 5000

5. **Deploy**: Railway automáticamente construye y despliega

**Copiar la URL pública** (algo como `https://neurox-production-abc123.railway.app`)

---

## Paso 3: Conectar Webhook en Meta (3 minutos)

1. Ve a **Meta for Developers** → tu app → **Messenger** → **Settings**
2. **Webhook URL**: `https://tu-railway-url/webhook`
3. **Verify Token**: el que copiaste en Paso 1
4. **Eventos a suscribirse**:
   - ✅ `messages`
   - ✅ `message_postbacks`
   - ✅ `messaging_postback`
5. **Guardar**

6. **Suscribir página**:
   - En **Webhooks** → elige tu página de Instagram
   - Confirmar suscripción

---

## Paso 4: Crear Cliente en Base de Datos (1 minuto)

Ya está automático. La primera vez que recibas un mensaje en Instagram:
1. El sistema detecta tu `page_id`
2. Crea automáticamente un **Client** en la BD
3. Inicia el pipeline de ventas

**O crear manualmente via Railway Shell**:
```bash
# En Railway, abre "Shell" de tu deployment
cd vendedor
python
from database import SessionLocal
from database.models import Client
db = SessionLocal()
client = Client(
    page_id="17841480693267452",  # Tu Instagram Business Account ID
    access_token="EAAB...",  # Access Token de Meta
    business_name="Mi Negocio",
    system_prompt="Eres vendedor de servicios...",
    cal_link="https://calendly.com/tu-link"
)
db.add(client)
db.commit()
print("Cliente creado ✓")
```

---

## Paso 5: Probar

1. **Envía un DM** a tu cuenta de Instagram desde otra cuenta
2. **Abre el dashboard**: `https://tu-railway-url/admin/leads`
   - Usuario: `admin`
   - Contraseña: la que creaste
3. Verás el lead aparecer automáticamente

---

## URLs finales después de Deploy:

- **Webhook**: `https://tu-railway-url/webhook`
- **Health check**: `https://tu-railway-url/health`
- **Dashboard admin**: `https://tu-railway-url/admin/leads`

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Webhook no se verifica | Asegúrate que VERIFY_TOKEN sea exacto en Meta y Railway |
| No se reciben mensajes | Verifica logs en Railway, suscribe página al webhook |
| IA no responde | Valida ANTHROPIC_API_KEY en Railway |
| Error 500 en dashboard | Abre Shell en Railway y ejecuta `python database/seed.py` |

---

¡Eso es todo! Tu Vendedor IA está corriendo. 🎉
