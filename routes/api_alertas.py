# routes/api_alertas.py
from flask import Blueprint, jsonify
from models import db, AlertaStock

alertas_bp = Blueprint('alertas_bp', __name__, url_prefix='/api/alertas')

# 🔹 Listar todas las alertas
@alertas_bp.route('/', methods=['GET'])
def get_alertas():
    alertas = AlertaStock.query.order_by(AlertaStock.fecha.desc()).all()
    return jsonify([a.to_dict() for a in alertas])

# 🔹 Listar alertas pendientes
@alertas_bp.route('/pendientes', methods=['GET'])
def get_alertas_pendientes():
    alertas = AlertaStock.query.filter_by(estado='Pendiente').order_by(AlertaStock.fecha.desc()).all()
    return jsonify([a.to_dict() for a in alertas])