# routes/api_reportes.py
from flask import Blueprint, jsonify
from models import db, Insumo, Compra, TanqueFabricado, AlertaStock

reportes_bp = Blueprint('reportes_bp', __name__, url_prefix='/api/reportes')

# 🔹 Resumen general del sistema
@reportes_bp.route('/resumen', methods=['GET'])
def resumen():
    total_insumos = Insumo.query.count()
    total_alertas_pendientes = AlertaStock.query.filter_by(estado='Pendiente').count()
    total_compras = db.session.query(db.func.sum(Compra.total)).scalar() or 0
    total_tanques = TanqueFabricado.query.count()
    costo_total_tanques = db.session.query(db.func.sum(TanqueFabricado.costo_total)).scalar() or 0

    return jsonify({
        'insumos_registrados': total_insumos,
        'alertas_pendientes': total_alertas_pendientes,
        'valor_total_compras': float(total_compras),
        'tanques_fabricados': total_tanques,
        'costo_total_tanques': float(costo_total_tanques)
    })

# 🔹 Reporte de insumos por debajo del stock mínimo
@reportes_bp.route('/bajo_stock', methods=['GET'])
def insumos_bajo_stock():
    from models import Insumo
    insumos = Insumo.query.filter(Insumo.cantidad < Insumo.stock_minimo).all()
    return jsonify([i.to_dict() for i in insumos])
