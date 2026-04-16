#!/bin/bash
cd /Users/macbookpro/instagram_bot_new/vendedor

echo "=== Commiteando fixes de cotizaciones ==="
git add webhooks/instagram.py ai/handler.py sales/cotizacion.py

git commit -m "Fix: 3 bugs criticos en cotizaciones

- webhooks/instagram.py: inicializar db=None para evitar UnboundLocalError
  cuando Instagram manda mensajes sin texto (reacciones, stickers, etc.)
- ai/handler.py: evitar que servicios especificos (bot_con_ia) sean
  sobreescritos por genericos (bot); mas keywords para deteccion
- sales/cotizacion.py: mostrar nombres legibles en cotizacion
  en vez de keys internas (bot_con_ia -> Bot Automatico Instagram Con IA)"

echo "=== Pusheando a GitHub ==="
git push origin main

echo ""
echo "=== LISTO - Railway va a deployar automaticamente ==="
