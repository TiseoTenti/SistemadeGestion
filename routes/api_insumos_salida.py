# routes/api_insumos_salida.py
from flask import Blueprint, request, jsonify
from models import db, Insumo, TanqueFabricado, TanqueInsumo, ProveedorInsumo, AlertaStock
from datetime import datetime
from decimal import Decimal, InvalidOperation

insumos_salida_bp = Blueprint('insumos_salida_bp', __name__, url_prefix='/api/v1/insumos_salida')


# --------------------------------------------
# POST /api/v1/insumos_salida/
# Registrar salida de insumo para un tanque
# --------------------------------------------
@insumos_salida_bp.route('/', methods=['POST'])
def registrar_salida():
    data = request.get_json()
    
    id_insumo = data.get('id_insumo')
    id_tanque = data.get('id_tanque')
    cantidad_usada = float(data.get('cantidad_usada', 0))
    operario = data.get('operario')

    if not operario:
        return jsonify({"error": "Debe indicar el operario"}), 400


    # Validaciones básicas
    if not id_insumo or not id_tanque or cantidad_usada <= 0:
        return jsonify({"error": "Datos incompletos o inválidos"}), 400

    insumo = Insumo.query.get(id_insumo)
    tanque = TanqueFabricado.query.get(id_tanque)

    if not insumo or not tanque:
        return jsonify({"error": "Insumo o tanque no encontrado"}), 404

    # Verificar stock suficiente
    if float(insumo.cantidad) < cantidad_usada:
        return jsonify({"error": "Stock insuficiente"}), 400

    # Buscar costo unitario actual del insumo
    proveedor_insumo = ProveedorInsumo.query.filter_by(id_insumo=id_insumo).order_by(ProveedorInsumo.id_proveedor_insumo.desc()).first()
    costo_unitario = float(proveedor_insumo.precio_actual) if proveedor_insumo else 0.0

    # Descontar stock
    insumo.cantidad = float(insumo.cantidad) - cantidad_usada

    # Registrar en TanqueInsumo
    registro = TanqueInsumo(
        id_tanque=id_tanque,
        id_insumo=id_insumo,
        cantidad_usada=cantidad_usada,
        costo_unitario=costo_unitario,
        operario=operario,
        fecha_registro=datetime.utcnow()  
    )
    db.session.add(registro)

    # Recalcular costo total del tanque
    tanque.costo_total = float(tanque.costo_total) + (cantidad_usada * costo_unitario)

    # Comprobar alerta de stock
    if float(insumo.cantidad) < float(insumo.stock_minimo):
        alerta = AlertaStock(
            id_insumo=insumo.id_insumo,
            cantidad_actual=insumo.cantidad,
            stock_minimo=insumo.stock_minimo,
            estado='Pendiente'
        )
        db.session.add(alerta)

    db.session.commit()

    return jsonify({
        "mensaje": "Salida registrada correctamente",
        "tanque": tanque.to_dict(),
        "insumo": insumo.to_dict(),
        "cantidad_usada": cantidad_usada,
        "costo_unitario": costo_unitario,
        "nuevo_stock": float(insumo.cantidad)
    }), 201

#Delete de insumos_salida

@insumos_salida_bp.route('/<int:id_tanque_insumo>', methods=['DELETE'])
def eliminar_salida(id_tanque_insumo):
    registro = TanqueInsumo.query.get_or_404(id_tanque_insumo)

    insumo = Insumo.query.get_or_404(registro.id_insumo)
    tanque = TanqueFabricado.query.get_or_404(registro.id_tanque)

    cantidad = float(registro.cantidad_usada)
    costo_unitario = float(registro.costo_unitario or 0)

    # 1. Devolver stock al insumo
    insumo.cantidad = float(insumo.cantidad) + cantidad

    # 2. Revertir costo del tanque
    tanque.costo_total = float(tanque.costo_total) - (cantidad * costo_unitario)

    if tanque.costo_total < 0:
        tanque.costo_total = 0

    # 3. Eliminar registro de salida
    db.session.delete(registro)

    # 4. Limpiar alertas si ya no corresponde
    alertas = AlertaStock.query.filter_by(id_insumo=insumo.id_insumo, estado='Pendiente').all()
    for alerta in alertas:
        if float(insumo.cantidad) >= float(alerta.stock_minimo):
            alerta.estado = 'Resuelta'

    db.session.commit()

    return jsonify({
        "mensaje": "Salida eliminada y stock revertido correctamente",
        "nuevo_stock": float(insumo.cantidad),
        "costo_tanque": float(tanque.costo_total)
    }), 200


# --------------------------------------------
# GET /api/v1/insumos_salida/
# Listar todas las salidas registradas
# --------------------------------------------
@insumos_salida_bp.route('/', methods=['GET'])
def listar_salidas():
    registros = TanqueInsumo.query.order_by(TanqueInsumo.id_tanque_insumo.desc()).all()
    resultado = []

    for r in registros:
        tanque = TanqueFabricado.query.get(r.id_tanque)
        insumo = Insumo.query.get(r.id_insumo)

        resultado.append({
            "id_tanque_insumo": r.id_tanque_insumo,
            "id_tanque": r.id_tanque,
            "tanque_nombre": tanque.modelo if tanque else "N/A",
            "id_insumo": r.id_insumo,
            "insumo_nombre": insumo.nombre if insumo else "N/A",
            "cantidad_usada": float(r.cantidad_usada),
            "costo_unitario": float(r.costo_unitario),
            "operario": r.operario,
            "fecha_registro": r.fecha_registro.isoformat() if r.fecha_registro else None
        })

    return jsonify(resultado), 200


#    registros = TanqueInsumo.query.all()
#    resultado = []
#
#    for r in registros:
#      insumo = Insumo.query.get(r.id_insumo)
#      tanque = TanqueFabricado.query.get(r.id_tanque)
#      resultado.append({
#        "id_tanque_insumo": r.id_tanque_insumo,
#        "id_tanque": r.id_tanque,
#        "nombre_tanque": tanque.modelo if tanque else f"Tanque #{r.id_tanque}",
#        "id_insumo": r.id_insumo,
#        "nombre_insumo": insumo.nombre if insumo else f"Insumo #{r.id_insumo}",
#        "cantidad_usada": float(r.cantidad_usada),
#        "costo_unitario": float(r.costo_unitario or 0),
#        #"fecha_registro": r.fecha_registro.isoformat() if r.fecha_registro else None
#    })
#    return jsonify(resultado), 200


# --------------------------------------------
# GET /api/v1/insumos_salida/<id_tanque_insumo>
# Obtener una salida específica
# --------------------------------------------
@insumos_salida_bp.route('/<int:id_tanque_insumo>', methods=['GET'])
def obtener_salida(id_tanque_insumo):
    registro = TanqueInsumo.query.get_or_404(id_tanque_insumo)
    return jsonify(registro.to_dict()), 200


#UPDATE SALIDA
@insumos_salida_bp.route('/<int:id_tanque_insumo>', methods=['PUT'])
def actualizar_salida(id_tanque_insumo):
    registro = TanqueInsumo.query.get_or_404(id_tanque_insumo)
    data = request.get_json() or {}

    # --- Validar y convertir cantidad ---
    try:
        nueva_cantidad = Decimal(str(data.get('cantidad_usada', registro.cantidad_usada or 0)))
    except (InvalidOperation, TypeError, ValueError):
        return jsonify({"error": "Cantidad inválida"}), 400
    if nueva_cantidad <= 0:
        return jsonify({"error": "Cantidad inválida"}), 400

    # --- Validar id_insumo ---
    try:
        nuevo_id_insumo = int(data.get('id_insumo', registro.id_insumo))
    except (ValueError, TypeError):
        return jsonify({"error": "ID de insumo inválido"}), 400

    nuevo_operario = data.get('operario', registro.operario)

    # --- Obtener tanque e insumos ---
    tanque = TanqueFabricado.query.get_or_404(registro.id_tanque)
    insumo_antiguo = Insumo.query.get_or_404(registro.id_insumo)
    insumo_nuevo = Insumo.query.get_or_404(nuevo_id_insumo)

    # --- Revertir stock y costo del insumo original ---
    insumo_antiguo.cantidad = float(insumo_antiguo.cantidad or 0) + float(registro.cantidad_usada or 0)
    tanque.costo_total = float(tanque.costo_total or 0) - float(registro.cantidad_usada or 0) * float(registro.costo_unitario or 0)
    if tanque.costo_total < 0:
        tanque.costo_total = 0

    # --- Verificar stock suficiente del nuevo insumo ---
    if float(insumo_nuevo.cantidad or 0) < float(nueva_cantidad):
        return jsonify({"error": f"Stock insuficiente del insumo {insumo_nuevo.nombre}"}), 400

    # --- Obtener costo unitario ---
    proveedor_insumo = ProveedorInsumo.query.filter_by(id_insumo=nuevo_id_insumo)\
        .order_by(ProveedorInsumo.id_proveedor_insumo.desc()).first()
    costo_unitario = float(proveedor_insumo.precio_actual or 0) if proveedor_insumo else 0.0

    # --- Actualizar stock y registro ---
    insumo_nuevo.cantidad = float(insumo_nuevo.cantidad or 0) - float(nueva_cantidad)
    registro.id_insumo = nuevo_id_insumo
    registro.cantidad_usada = float(nueva_cantidad)
    registro.costo_unitario = costo_unitario
    registro.operario = nuevo_operario

    # --- Ajustar costo total del tanque ---
    tanque.costo_total += float(nueva_cantidad) * costo_unitario

    # --- Actualizar alertas de stock ---
    for ins in [insumo_antiguo, insumo_nuevo]:
        alertas = AlertaStock.query.filter_by(id_insumo=ins.id_insumo, estado='Pendiente').all()
        for alerta in alertas:
            if float(ins.cantidad or 0) >= float(alerta.stock_minimo or 0):
                alerta.estado = 'Resuelta'

    db.session.commit()

    return jsonify({
        "mensaje": "Salida actualizada correctamente",
        "nuevo_stock_antiguo": float(insumo_antiguo.cantidad),
        "nuevo_stock_nuevo": float(insumo_nuevo.cantidad),
        "costo_tanque": float(tanque.costo_total),
        "cantidad_usada": float(nueva_cantidad),
        "operario": registro.operario,
        "id_insumo": registro.id_insumo
    }), 200



# --------------------------------------------
# GET /api/v1/insumos_salida/tanque/<int:id_tanque>
# Listar salidas por tanque específico
# --------------------------------------------
@insumos_salida_bp.route('/tanque/<int:id_tanque>', methods=['GET'])
def listar_por_tanque(id_tanque):
    registros = TanqueInsumo.query.filter_by(id_tanque=id_tanque).all()
    if not registros:
        return jsonify({"mensaje": "No hay insumos asociados a este tanque"}), 404
    return jsonify([r.to_dict() for r in registros]), 200
