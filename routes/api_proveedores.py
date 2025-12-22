# routes/api_proveedores.py
from flask import Blueprint, request, jsonify
from models import db, Proveedor, ProveedorInsumo

proveedores_bp = Blueprint('proveedores_bp', __name__, url_prefix='/api/v1/proveedores')

@proveedores_bp.route('/', methods=['GET'])
def listar_proveedores():
    provs = Proveedor.query.all()
    return jsonify([p.to_dict() for p in provs])



@proveedores_bp.route('/', methods=['POST'])
def crear_proveedor():
    data = request.json
    p = Proveedor(
        nombre=data['nombre'],
        razon_social=data['razon_social'],
        cuit=data['cuit'],
        direccion=data.get('direccion'),
        telefono=data.get('telefono'),
        email=data.get('email')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@proveedores_bp.route('/buscar', methods=['GET'])
def buscar_proveedores():
    q = request.args.get('q', '').strip()

    if not q:
        return jsonify([])

    proveedores = Proveedor.query.filter(
        Proveedor.nombre.ilike(f"%{q}%")
    ).order_by(Proveedor.nombre).limit(10).all()

    return jsonify([
        {
            "id_proveedor": p.id_proveedor,
            "nombre": p.nombre
        } for p in proveedores
    ])




@proveedores_bp.route('/<int:id_proveedor>/insumos', methods=['GET'])
def insumos_por_proveedor(id_proveedor):
    proveedor = Proveedor.query.get_or_404(id_proveedor)
    return jsonify(proveedor.insumos_detalle())

@proveedores_bp.route('/<int:id_proveedor>/insumos', methods=['POST'])
def asociar_insumo_proveedor(id_proveedor):
    data = request.json
    # espera: { "id_insumo": int, "precio_actual": 123.45 }
    pi = ProveedorInsumo(
        id_proveedor=id_proveedor,
        id_insumo=data['id_insumo'],
        precio_actual=data['precio_actual']
    )
    db.session.add(pi)
    db.session.commit()
    return jsonify({'message': 'Asociación creada', 'id': pi.id_proveedor_insumo}), 201
