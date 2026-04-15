"""Rutas del dashboard admin y cotizaciones públicas"""

from flask import Blueprint, render_template, jsonify, request
from database import SessionLocal
from database.models import Client, Lead, Message, Cotizacion
from .auth import require_basic_auth
from datetime import datetime

dashboard = Blueprint("dashboard", __name__, url_prefix="/admin")
public_bp = Blueprint("public", __name__)


@dashboard.route("/", methods=["GET"])
@require_basic_auth
def admin_index():
    """Redirige a la lista de leads"""
    return """
    <html>
        <head><title>Vendedor IA</title></head>
        <body>
            <h1>Vendedor IA - Admin Dashboard</h1>
            <p><a href="/admin/leads">Ver Leads</a></p>
        </body>
    </html>
    """


@dashboard.route("/leads", methods=["GET"])
@require_basic_auth
def list_leads():
    """Lista todos los leads con badges de etapa"""
    db = SessionLocal()

    try:
        # Filtro opcional por cliente
        client_id = request.args.get("client_id", type=int)

        query = db.query(Lead)
        if client_id:
            query = query.filter(Lead.client_id == client_id)

        leads = query.order_by(Lead.created_at.desc()).all()

        # Colores por etapa
        stage_colors = {
            "NUEVO": "#6c757d",
            "CALIFICANDO": "#0d6efd",
            "AGENDADO": "#ffc107",
            "COTIZADO": "#198754",
            "FOLLOW_UP": "#fd7e14",
            "CERRADO": "#dc3545",
        }

        html = """
        <html>
        <head>
            <title>Leads - Vendedor IA</title>
            <style>
                body { font-family: Arial; margin: 20px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
                th { background: #f5f5f5; }
                .badge { padding: 5px 10px; border-radius: 3px; color: white; }
                a { color: #0d6efd; text-decoration: none; }
            </style>
        </head>
        <body>
            <h1>Leads</h1>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Usuario</th>
                    <th>Cliente</th>
                    <th>Etapa</th>
                    <th>Follow-ups</th>
                    <th>Última actividad</th>
                    <th>Acciones</th>
                </tr>
        """

        for lead in leads:
            color = stage_colors.get(lead.stage, "#999")
            last_msg = lead.last_message_at.strftime("%Y-%m-%d %H:%M") if lead.last_message_at else "N/A"

            html += f"""
                <tr>
                    <td>{lead.id}</td>
                    <td>{lead.instagram_user_id}</td>
                    <td>{lead.client.business_name}</td>
                    <td><span class="badge" style="background: {color}">{lead.stage}</span></td>
                    <td>{lead.follow_up_count}</td>
                    <td>{last_msg}</td>
                    <td><a href="/admin/lead/{lead.id}">Ver</a></td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        return html

    finally:
        db.close()


@dashboard.route("/lead/<int:lead_id>", methods=["GET"])
@require_basic_auth
def view_lead(lead_id):
    """Muestra el historial completo de un lead"""
    db = SessionLocal()

    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()

        if not lead:
            return "Lead no encontrado", 404

        html = f"""
        <html>
        <head>
            <title>Lead {lead_id} - Vendedor IA</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                .info {{ background: #f5f5f5; padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
                .message {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
                .user {{ background: #e3f2fd; }}
                .assistant {{ background: #f3e5f5; }}
                button {{ padding: 10px 20px; cursor: pointer; }}
                a {{ color: #0d6efd; text-decoration: none; margin-right: 10px; }}
            </style>
        </head>
        <body>
            <a href="/admin/leads">← Volver a leads</a>
            <h1>Lead #{lead_id}</h1>
            <div class="info">
                <p><strong>Usuario Instagram:</strong> {lead.instagram_user_id}</p>
                <p><strong>Cliente:</strong> {lead.client.business_name}</p>
                <p><strong>Etapa actual:</strong> {lead.stage}</p>
                <p><strong>Follow-ups:</strong> {lead.follow_up_count}</p>
                <p><strong>Creado:</strong> {lead.created_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p><strong>Contexto:</strong> <pre>{lead.context}</pre></p>
            </div>

            <h2>Conversación</h2>
        """

        messages = db.query(Message).filter(Message.lead_id == lead_id).order_by(Message.created_at).all()

        for msg in messages:
            css_class = "user" if msg.role == "user" else "assistant"
            role_label = "Usuario" if msg.role == "user" else "Bot"
            time_str = msg.created_at.strftime("%H:%M:%S")

            html += f"""
                <div class="message {css_class}">
                    <strong>{role_label}</strong> [{time_str}]<br>
                    {msg.content}
                </div>
            """

        html += """
            <hr>
            <form method="POST" action="/admin/lead-close" style="margin-top: 20px;">
                <input type="hidden" name="lead_id" value='""" + str(lead_id) + """'>
                <label>
                    <input type="radio" name="result" value="won"> Ganado
                    <input type="radio" name="result" value="lost"> Perdido
                </label>
                <button type="submit">Cerrar Lead</button>
            </form>
        </body>
        </html>
        """

        return html

    finally:
        db.close()


@dashboard.route("/lead-close", methods=["POST"])
@require_basic_auth
def close_lead():
    """Cierra un lead (marca como CERRADO)"""
    db = SessionLocal()

    try:
        lead_id = request.form.get("lead_id", type=int)
        result = request.form.get("result")  # "won" o "lost"

        if not lead_id or result not in ["won", "lost"]:
            return "Datos inválidos", 400

        lead = db.query(Lead).filter(Lead.id == lead_id).first()

        if not lead:
            return "Lead no encontrado", 404

        lead.stage = "CERRADO"
        lead.context = lead.context or {}
        lead.context["closed_as"] = result
        lead.context["closed_at"] = datetime.utcnow().isoformat()

        db.commit()

        return f"""
        <html>
        <body>
            <h1>Lead {lead_id} cerrado como {result}</h1>
            <a href="/admin/leads">Volver a leads</a>
        </body>
        </html>
        """

    finally:
        db.close()


# ==================
# Rutas Públicas (sin autenticación)
# ==================

@public_bp.route("/cotizacion/<token>", methods=["GET"])
def view_cotizacion(token):
    """Muestra una cotización pública por token"""
    db = SessionLocal()

    try:
        cotizacion = db.query(Cotizacion).filter(Cotizacion.token == token).first()

        if not cotizacion:
            return "Cotización no encontrada", 404

        lead = cotizacion.lead
        client = lead.client
        nombre_cliente = lead.context.get("nombre", "Cliente") if lead.context else "Cliente"

        # Generar tabla de items
        items_html = ""
        total_price = cotizacion.total or "A consultar"

        for item in cotizacion.items:
            desc = item.get("descripcion", "Servicio")
            price = item.get("precio", "$0.00")
            items_html += f"""
            <tr>
                <td>{desc}</td>
                <td style="text-align: right;">{price}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cotización - {client.business_name}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #0d6efd;
                    padding-bottom: 20px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    color: #0d6efd;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 5px 0;
                    color: #666;
                    font-size: 14px;
                }}
                .client-info {{
                    background: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .client-info p {{
                    margin: 5px 0;
                    font-size: 14px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #0d6efd;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #eee;
                }}
                .total-row {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #0d6efd;
                    text-align: right;
                    padding-top: 20px;
                    border-top: 2px solid #0d6efd;
                }}
                .notas {{
                    background: #fff3cd;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                    font-size: 13px;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{client.business_name}</h1>
                    <p>Cotización Profesional</p>
                </div>

                <div class="client-info">
                    <p><strong>Para:</strong> {nombre_cliente}</p>
                    <p><strong>Servicio:</strong> {cotizacion.servicio}</p>
                    <p><strong>Fecha:</strong> {cotizacion.created_at.strftime("%d/%m/%Y")}</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Descripción</th>
                            <th style="text-align: right;">Precio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>

                <div class="total-row">
                    TOTAL: {total_price}
                </div>

                {"<div class='notas'>" + cotizacion.notas + "</div>" if cotizacion.notas else ""}

                <div class="footer">
                    <p>Responde al chat de Instagram para confirmar o hacer preguntas sobre esta cotización.</p>
                    <p style="color: #999; margin-top: 10px;">Generado automáticamente por {client.business_name}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    finally:
        db.close()
