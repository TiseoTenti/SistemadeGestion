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
    # tanque.finalizado = True
    db.session.commit()

    # Generar PDF profesional con bordes
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdf.setTitle(f"Tanque_{tanque.id_tanque}_Finalizado")

    # Título
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, height - 50, f"Informe de Tanque Fabricado ID {tanque.id_tanque}")

    # Información general
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, f"Cliente: {tanque.cliente}")
    pdf.drawString(50, height - 95, f"Modelo: {tanque.modelo}")
    pdf.drawString(50, height - 110, f"Fecha: {tanque.fecha.strftime('%Y-%m-%d')}")
    pdf.drawString(50, height - 125, f"Costo Total: ${float(costo_total):.2f}")

    # Tabla profesional
    y_start = height - 150
    row_height = 20
    x_positions = [50, 100, 160, 320, 400, 480]  # columnas: fecha, cantidad, insumo, precio unitario, total, proveedor
    headers = ["Fecha", "Cantidad", "Insumo", "Precio Unitario", "Precio Total", "Proveedor"]

    def dibujar_fila(y, valores, bold=False):
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        for i, val in enumerate(valores):
            pdf.drawString(x_positions[i] + 2, y + 5, str(val))
        # Línea horizontal para bordes
        pdf.line(x_positions[0], y, x_positions[-1] + 80, y)

    # Encabezado
    y = y_start
    dibujar_fila(y, headers, bold=True)
    y -= row_height

    for ti in tanque.tanque_insumo:
        if y < 50:  # salto de página
            pdf.showPage()
            y = height - 50
            dibujar_fila(y, headers, bold=True)
            y -= row_height
        fecha = tanque.fecha.strftime('%Y-%m-%d')
        cantidad = f"{float(ti.cantidad_usada):.2f}"
        insumo = ti.insumo.nombre
        precio_unitario = f"${float(ti.costo_unitario):.2f}"
        precio_total = f"${float(ti.cantidad_usada * ti.costo_unitario):.2f}"
        proveedor_nombre = ti.insumo.proveedor_insumo[0].proveedor.razon_social if ti.insumo.proveedor_insumo else '-'
        dibujar_fila(y, [fecha, cantidad, insumo, precio_unitario, precio_total, proveedor_nombre])
        y -= row_height

    # Borde final de la tabla
    pdf.line(x_positions[0], y + row_height, x_positions[-1] + 80, y + row_height)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    # Guardar internamente
    with open(f"Tanque_{tanque.id_tanque}_Finalizado.pdf", "wb") as f:
        f.write(buffer.read())

    return jsonify({'message': 'PDF profesional generado internamente', 'costo_total': float(costo_total)})
