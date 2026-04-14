from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base


class Client(Base):
    """Representa un cliente/tenant — cada cuenta de Instagram de un negocio"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    page_id = Column(String, unique=True, nullable=False, index=True)  # ID de página de Instagram
    access_token = Column(String, nullable=False)  # Token de acceso Meta
    business_name = Column(String, nullable=False)  # Nombre del negocio
    system_prompt = Column(Text, nullable=False)  # Prompt base personalizado por cliente
    cal_link = Column(String, nullable=True)  # Link a Cal.com o Calendly
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación con leads
    leads = relationship("Lead", back_populates="client", cascade="all, delete-orphan")


class Lead(Base):
    """Representa un potencial cliente en el pipeline de ventas"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    instagram_user_id = Column(String, nullable=False, index=True)  # ID único del usuario en Instagram
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # Estado del lead en el funnel
    stage = Column(String, default="NUEVO")  # NUEVO, CALIFICANDO, AGENDADO, COTIZADO, FOLLOW_UP, CERRADO

    # JSON: nombre, servicio_interesado, presupuesto, objeciones, etc.
    # Se actualiza conforme Claude extrae info de la conversación
    context = Column(JSON, default={})

    # Conteo de mensajes de follow-up automáticos (máximo 2)
    follow_up_count = Column(Integer, default=0)

    # Última vez que este lead escribió algo
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    client = relationship("Client", back_populates="leads")
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Historial de mensajes de una conversación lead ↔ bot"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" o "assistant"
    content = Column(Text, nullable=False)  # Contenido del mensaje
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="messages")
