# Neurox — Bot de Instagram + Vendedor IA

Bot automático que responde DMs de Instagram usando Claude IA, con sistema de pipeline de ventas completamente automatizado.

## 🚀 Deploy Vendedor IA a Railway (1 Click)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new?templateUrl=https://github.com/MakerStudios-bot/neurox-instagram-bot)

**Pasos:**
1. Haz click en el botón ☝️
2. Autoriza en Railway
3. Completa las variables de entorno (VERIFY_TOKEN, APP_SECRET, ANTHROPIC_API_KEY, etc.)
4. ¡Listo! Deploy automático ✅

**Luego:** Conecta a Meta for Developers (ver sección "Configurar Webhook en Meta" abajo)

---

## 📋 Dos Sistemas en Este Repo

### 1. **Bot Simple** (main.py)
- Respuestas fijas predefinidas
- IA para conversaciones
- Histórico en memoria
- ✅ Rápido de deployar

### 2. **Vendedor IA** (vendedor/) - ⭐ RECOMENDADO
- **State machine** automático: NUEVO → CALIFICANDO → AGENDADO → COTIZADO → FOLLOW_UP → CERRADO
- **IA adaptativa** con prompts dinámicos por etapa
- **Multi-tenant**: Múltiples clientes aislados
- **Follow-up automático**: Job cada 24h
- **Dashboard admin**: Ver leads + historial + cierre manual
- **Base de datos**: Persistencia completa en SQLite
- ✅ Sistema de ventas profesional end-to-end

**Recomendamos usar Vendedor IA** (en carpeta `vendedor/`). [Ver documentación completa](./vendedor/README.md)

---

## 📖 Documentación

## Características

✅ **Respuestas fijas** para preguntas comunes (horarios, precios, contacto, saludos)  
✅ **IA inteligente** con Claude Haiku 4.5 (rápido y económico)  
✅ **Historial de conversaciones** (mantiene contexto de hasta 20 mensajes previos)  
✅ **Validación HMAC** de seguridad con Meta  
✅ **Webhook** integrado con Meta Graph API  
✅ **Fácil deployment** en Railway  

## Estructura

```
├── main.py           # Servidor Flask + lógica de webhook
├── ai_handler.py     # Integración Claude API
├── responses.py      # Respuestas fijas predefinidas
├── requirements.txt  # Dependencias Python
├── Dockerfile        # Config para Railway
├── railway.toml      # Config de deploy
└── .env.example      # Ejemplo de variables de entorno
```

## Configuración

### 1. Crear app en Meta for Developers

1. Ve a https://developers.facebook.com/
2. Crea una nueva app de tipo "Business"
3. Agrega el producto **"Messenger"** (que incluye Instagram)
4. En "App Roles" → "Test Users", conecta tu cuenta de Instagram personal
5. Ve a "Messenger" → "Settings" y copia el **Access Token**
6. Guarda el **App ID**

### 2. Obtener credenciales

- **VERIFY_TOKEN**: Puedes crear uno tú mismo (ej: "my_random_token_123")
- **ACCESS_TOKEN**: Obtenido de Meta for Developers (token de larga duración para la página)
- **INSTAGRAM_BUSINESS_ACCOUNT_ID**: ID de tu cuenta de negocio (NO es el Page ID)
  - Puedes obtenerlo ejecutando:
  ```bash
  curl "https://graph.instagram.com/me/instagram_business_account?access_token=YOUR_TOKEN"
  ```
  - Será un número como: `17841480693267452`
- **APP_SECRET**: Secret de tu app en Meta (necesario para validación HMAC)
- **ANTHROPIC_API_KEY**: Clave de Anthropic (https://console.anthropic.com/)

### 3. Configurar variables en Railway

Copia `.env.example` a `.env` y llena los valores:

```bash
cp .env.example .env
```

En Railway, agrega estas variables en el panel de "Variables":
- `VERIFY_TOKEN`
- `ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- `ANTHROPIC_API_KEY`

### 4. Configurar Webhook en Meta

1. Obtén la URL pública de tu app en Railway (ej: `https://my-bot.railway.app`)
2. Ve a Meta for Developers → tu app → Messenger → Settings
3. En "Webhook URL", agrega: `https://your-railway-url/webhook`
4. En "Verify Token", pega el valor de `VERIFY_TOKEN`
5. Selecciona los eventos: `messages`, `message_postbacks`, `messaging_postback`
6. Guarda

### 5. Suscribir página a webhook

En Meta for Developers, ve a Messenger → Settings → Webhooks y suscribe tu página de Instagram.

## Flujo del bot

```
DM a Instagram
    ↓
Meta envía POST a /webhook
    ↓
¿Palabra clave en responses.py?
    ├─ Sí → Respuesta fija (instantáneo)
    └─ No → Llamar Claude API → Respuesta IA
    ↓
Enviar respuesta al usuario
```

## Uso local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env
cp .env.example .env
# Editar .env con tus valores

# Ejecutar
python main.py
```

El bot escuchará en `http://localhost:5000`

## Personalización

### Agregar respuestas fijas

Edita `responses.py` y agrega más palabras clave:

```python
FIXED_RESPONSES = {
    "mi palabra": "Mi respuesta aquí",
    "otra palabra": "Otra respuesta",
}
```

### Cambiar el prompt de IA

Edita el `SYSTEM_PROMPT` en `ai_handler.py` para personalizar el comportamiento de Claude.

## Deployment en Railway

1. Conecta tu repo de GitHub (o sube manualmente)
2. Railway detectará automáticamente el `Dockerfile`
3. Agrega las variables de entorno
4. Despliega
5. Obtén la URL pública y configura el webhook en Meta

## Troubleshooting

**El webhook no se verifica:**
- Verifica que `VERIFY_TOKEN` coincida en Meta y en tu `.env`
- Asegúrate de que la URL sea accesible públicamente

**No se reciben mensajes:**
- Verifica los logs en Railway
- Asegúrate de que la página está suscrita al webhook
- Prueba enviando un DM a la cuenta

**Errores de API de Claude:**
- Verifica que `ANTHROPIC_API_KEY` sea válido
- Revisa que tengas crédito en tu cuenta de Anthropic

## Especificaciones Técnicas

- **Modelo IA**: Claude Haiku 4.5 (optimizado para costos y velocidad)
- **Max tokens por respuesta**: 500
- **Historial de conversación**: Últimos 20 mensajes (mantiene contexto entre respuestas)
- **Validación de seguridad**: HMAC SHA-256 con Meta

## Notas Importantes

### HMAC Validation
- La validación HMAC está habilitada por defecto
- Si tienes problemas, puedes comentar temporalmente la línea en `main.py`:
  ```python
  # if not verify_hmac_signature(req):
  #     return "Forbidden", 403
  ```
- Pero se recomienda dejarla activada para producción

### Diferencia entre Page ID e Instagram Business Account ID
- **Page ID**: ID de tu página de Facebook
- **INSTAGRAM_BUSINESS_ACCOUNT_ID**: ID de tu cuenta de negocio de Instagram (diferente)
- Asegúrate de usar el correcto, sino el bot no podrá enviar mensajes

### Historial de Conversaciones
- El bot mantiene el contexto de los últimos 20 mensajes por usuario
- Esto permite conversaciones más naturales y contextuales
- El historial se almacena en memoria (se reinicia cuando se redeploy)

---

¡Listo! Tu bot está configurado y listo para funcionar. 🚀
