"""Rutas del dashboard admin"""

from flask import Blueprint, render_template, jsonify, request
from database import SessionLocal
from database.models import Client, Lead, Message
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
