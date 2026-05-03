# agent/tools.py — Herramientas del agente
# Generado por AgentKit para Restaurant La Gaviota

import os
import yaml
import logging
from datetime import datetime

logger = logging.getLogger("agentkit")


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_horario() -> dict:
    """Retorna el horario de atención y si el restaurante está abierto ahora."""
    info = cargar_info_negocio()
    ahora = datetime.now()
    dia_semana = ahora.weekday()  # 0=lunes, 6=domingo
    hora_actual = ahora.hour + ahora.minute / 60

    # Viernes=4, Sábado=5 → 11am a 11:59pm
    if dia_semana in [4, 5]:
        esta_abierto = 11.0 <= hora_actual < 24.0
    else:
        # Domingo a Jueves → 11am a 10pm
        esta_abierto = 11.0 <= hora_actual < 22.0

    return {
        "horario": info.get("negocio", {}).get("horario", "Domingo a Jueves 11am-10pm | Viernes y Sábado 11am-11:59pm"),
        "esta_abierto": esta_abierto,
        "hora_actual": ahora.strftime("%H:%M"),
    }


def buscar_en_knowledge(consulta: str) -> str:
    """Busca información relevante en los archivos de /knowledge."""
    resultados = []
    knowledge_dir = "knowledge"

    if not os.path.exists(knowledge_dir):
        return "No hay archivos de conocimiento disponibles."

    for archivo in os.listdir(knowledge_dir):
        ruta = os.path.join(knowledge_dir, archivo)
        if archivo.startswith(".") or not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{archivo}]: {contenido[:500]}")
        except (UnicodeDecodeError, IOError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."


# ── Reservaciones ────────────────────────────────────────────────────────────

reservaciones_en_memoria: dict[str, dict] = {}


def registrar_reservacion(telefono: str, nombre: str, fecha: str, hora: str, personas: int) -> str:
    """Registra una reservación en memoria (en producción, usar base de datos)."""
    reservacion_id = f"RES-{telefono[-4:]}-{datetime.now().strftime('%m%d%H%M')}"
    reservaciones_en_memoria[reservacion_id] = {
        "telefono": telefono,
        "nombre": nombre,
        "fecha": fecha,
        "hora": hora,
        "personas": personas,
        "creada_en": datetime.now().isoformat(),
    }
    logger.info(f"Reservación registrada: {reservacion_id}")
    return reservacion_id


def consultar_reservacion(telefono: str) -> list[dict]:
    """Busca reservaciones activas para un número de teléfono."""
    return [
        {"id": rid, **datos}
        for rid, datos in reservaciones_en_memoria.items()
        if datos["telefono"] == telefono
    ]


# ── Pedidos / Delivery ───────────────────────────────────────────────────────

pedidos_en_memoria: dict[str, dict] = {}


def registrar_pedido(telefono: str, items: list[str], tipo: str, direccion: str = "", nombre: str = "") -> str:
    """
    Registra un pedido.

    Args:
        telefono: Número del cliente
        items: Lista de platos pedidos
        tipo: 'delivery' o 'recojo'
        direccion: Dirección de entrega (solo para delivery)
        nombre: Nombre del cliente
    """
    pedido_id = f"PED-{telefono[-4:]}-{datetime.now().strftime('%m%d%H%M%S')}"
    pedidos_en_memoria[pedido_id] = {
        "telefono": telefono,
        "nombre": nombre,
        "items": items,
        "tipo": tipo,
        "direccion": direccion,
        "estado": "recibido",
        "creado_en": datetime.now().isoformat(),
    }
    logger.info(f"Pedido registrado: {pedido_id}")
    return pedido_id


def consultar_pedido(pedido_id: str) -> dict | None:
    """Consulta el estado de un pedido por su ID."""
    return pedidos_en_memoria.get(pedido_id)


def actualizar_estado_pedido(pedido_id: str, nuevo_estado: str) -> bool:
    """
    Actualiza el estado de un pedido.
    Estados válidos: recibido, preparando, en_camino, entregado, problema
    """
    if pedido_id in pedidos_en_memoria:
        pedidos_en_memoria[pedido_id]["estado"] = nuevo_estado
        pedidos_en_memoria[pedido_id]["actualizado_en"] = datetime.now().isoformat()
        logger.info(f"Pedido {pedido_id} actualizado a: {nuevo_estado}")
        return True
    return False


def registrar_problema_delivery(telefono: str, pedido_id: str, descripcion: str) -> str:
    """Registra un problema con un pedido de delivery para escalarlo al equipo."""
    ticket_id = f"PROB-{telefono[-4:]}-{datetime.now().strftime('%m%d%H%M%S')}"
    logger.warning(f"Problema delivery {ticket_id}: Pedido {pedido_id} — {descripcion}")
    # En producción: enviar alerta al equipo (email, Slack, etc.)
    return ticket_id


# ── Leads / Ventas ───────────────────────────────────────────────────────────

leads_en_memoria: dict[str, dict] = {}


def registrar_lead(telefono: str, nombre: str, interes: str) -> str:
    """Registra un lead (cliente potencial) para seguimiento."""
    lead_id = f"LEAD-{telefono[-4:]}-{datetime.now().strftime('%m%d%H%M')}"
    leads_en_memoria[lead_id] = {
        "telefono": telefono,
        "nombre": nombre,
        "interes": interes,
        "creado_en": datetime.now().isoformat(),
        "estado": "nuevo",
    }
    logger.info(f"Lead registrado: {lead_id}")
    return lead_id


def escalar_a_equipo(telefono: str, contexto: str, tipo: str = "consulta") -> bool:
    """
    Registra una solicitud para que el equipo del restaurante contacte al cliente.
    tipo: 'consulta', 'reclamo', 'lead_caliente', 'problema_delivery'
    """
    logger.info(f"ESCALAMIENTO [{tipo}] — {telefono}: {contexto}")
    # En producción: notificar al equipo via email, Slack, SMS, etc.
    return True
