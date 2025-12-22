# routes/api_insumos.py
from flask import Blueprint, request, jsonify
from models import db, Insumo, AlertaStock

insumos_bp = Blueprint('insumos_bp', __name__, url_prefix='/api/v1/insumos')


@insumos_bp.route('/buscar', methods=['GET'])
def buscar_insumos():
    q = request.args.get('q', '').strip()

    if not q:
        return jsonify([])

    insumos = Insumo.query.filter(
        Insumo.nombre.ilike(f"%{q}%")
    ).order_by(Insumo.nombre).limit(10).all()

    return jsonify([
        {
            "id_insumo": i.id_insumo,
            "nombre": i.nombre
        } for i in insumos
    ])




@insumos_bp.route('/', methods=['GET'])
def listar_insumos():
    insumos = Insumo.query.all()
    return jsonify([i.to_dict() for i in insumos])

@insumos_bp.route('/<int:id_insumo>', methods=['GET'])
def obtener_insumo(id_insumo):
    insumo = Insumo.query.get_or_404(id_insumo)
    return jsonify(insumo.to_dict())








@insumos_bp.route('/', methods=['POST'])
def crear_insumo():
    data = request.json
    nuevo = Insumo(
        codigo=data['codigo'],
        nombre=data['nombre'],
        cantidad=data.get('cantidad', 0),
        unidad_medida=data['unidad_medida'],
        stock_minimo=data.get('stock_minimo', 0)
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify(nuevo.to_dict()), 201

@insumos_bp.route('/<int:id_insumo>', methods=['PUT'])
def actualizar_insumo(id_insumo):
    insumo = Insumo.query.get_or_404(id_insumo)
    data = request.json
    for campo in ['codigo','nombre','cantidad','unidad_medida','stock_minimo']:
        if campo in data:
            setattr(insumo, campo, data[campo])
    db.session.commit()
    # comprobar alerta
    if float(insumo.cantidad) < float(insumo.stock_minimo):
        alerta = AlertaStock(
            id_insumo=insumo.id_insumo,
            cantidad_actual=insumo.cantidad,
            stock_minimo=insumo.stock_minimo
        )
        db.session.add(alerta)
        db.session.commit()
    return jsonify(insumo.to_dict())



@insumos_bp.route('/alertas', methods=['GET'])
def listar_alertas():
    alertas = AlertaStock.query.filter_by(estado='Pendiente').all()
    return jsonify([a.to_dict() for a in alertas])
