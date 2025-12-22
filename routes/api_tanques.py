# routes/api_tanques.py
from flask import Blueprint, request, jsonify
from models import db, TanqueFabricado, TanqueInsumo, Insumo
from decimal import Decimal
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
import io

tanques_bp = Blueprint('tanques_bp', __name__, url_prefix='/api/v1/tanques')

@tanques_bp.route('/', methods=['GET'])
def listar_tanques():
    tanques = TanqueFabricado.query.order_by(TanqueFabricado.fecha.desc()).all()
    return jsonify([t.to_dict() for t in tanques])

@tanques_bp.route('/', methods=['POST'])
def crear_tanque():
    data = request.json

    fecha_str = data.get('fecha')
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.utcnow().date()

    tanque = TanqueFabricado(
        modelo=data['modelo'],
        fecha=fecha,
        cliente=data.get('cliente')
    )

    db.session.add(tanque)
    db.session.flush() # para tener tanque.id_tanque

    costo_total = Decimal('0')
    for item in data.get('insumos', []):
        id_insumo = item['id_insumo']
        cantidad_usada = Decimal(str(item['cantidad_usada']))
        costo_unitario = Decimal(str(item['costo_unitario']))

        insumo = Insumo.query.get_or_404(id_insumo)

        ti = TanqueInsumo(
            id_tanque = tanque.id_tanque,
            id_insumo = insumo.id_insumo,
            cantidad_usada = cantidad_usada,
            costo_unitario = costo_unitario
        )
        db.session.add(ti)
        costo_total += cantidad_usada * costo_unitario
        # NOTA: según requisitos iniciales NO descontamos stock automáticamente al fabricar un tanque
        # si en el futuro querés descontar, descomentar la siguiente línea:
        # insumo.cantidad = Decimal(insumo.cantidad) - cantidad_usada

    tanque.costo_total = costo_total
    db.session.commit()
    return jsonify(tanque.to_dict()), 201

@tanques_bp.route('/<int:id_tanque>', methods=['GET'])
def obtener_tanque(id_tanque):
    tanque = TanqueFabricado.query.get_or_404(id_tanque)
    return jsonify(tanque.to_dict())

@tanques_bp.route('/<int:id_tanque>/insumos', methods=['GET'])
def insumos_tanque(id_tanque):
    tanque = TanqueFabricado.query.get_or_404(id_tanque)
    return jsonify([ti.to_dict() for ti in tanque.tanque_insumo])


@tanques_bp.route('/clientes', methods=['GET'])
def buscar_clientes():
    q = request.args.get('q', '').strip()

    if not q:
        return jsonify([])

    clientes = (
        db.session.query(TanqueFabricado.cliente)
        .filter(TanqueFabricado.cliente.ilike(f"%{q}%"))
        .distinct()
        .limit(10)
        .all()
    )

    return jsonify([c[0] for c in clientes if c[0]])



@tanques_bp.route('/<int:id_tanque>/finalizar', methods=['PUT'])
def finalizar_tanque(id_tanque):
    tanque = TanqueFabricado.query.get_or_404(id_tanque)
    
    if tanque.finalizado:
        return jsonify({'error': 'Este tanque ya fue finalizado'}), 400

    insumos = TanqueInsumo.query.filter_by(id_tanque=id_tanque).all()
    if not insumos:
        return jsonify({'error': 'El tanque no tiene insumos registrados'}), 400

    # Calcular costo total
    costo_total = sum(i.cantidad_usada * i.costo_unitario for i in insumos)
    tanque.costo_total = costo_total
  #  tanque.finalizado = True  # bloquear futuras modificaciones
    db.session.commit()

    # Generar PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Tanque_{tanque.id_tanque}_Finalizado")
    pdf.drawString(50, 750, f"Tanque ID: {tanque.id_tanque}")
    pdf.drawString(50, 735, f"Modelo: {tanque.modelo}")
    pdf.drawString(50, 720, f"Cliente: {tanque.cliente or '-'}")
    pdf.drawString(50, 705, f"Fecha: {tanque.fecha}")
    pdf.drawString(50, 690, f"Costo Total: ${float(costo_total):.2f}")

    y = 660
    pdf.drawString(50, y, "Insumos utilizados:")
    y -= 15
    pdf.drawString(60, y, "ID Insumo | Cantidad | Costo Unitario | Subtotal")
    y -= 15
    for i in insumos:
        subtotal = float(i.cantidad_usada) * float(i.costo_unitario)
        pdf.drawString(60, y, f"{i.id_insumo} | {i.cantidad_usada} | ${float(i.costo_unitario):.2f} | ${subtotal:.2f}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"Tanque_{tanque.id_tanque}.pdf", mimetype='application/pdf')

