# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

# ---------- Insumos ----------
class Insumo(db.Model):
    __tablename__ = 'insumos'
    id_insumo = db.Column(db.Integer, primary_key=True)
    #sacar el campo codigo
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Numeric(10,2), default=0)
    unidad_medida = db.Column(db.String(20), nullable=False)
    stock_minimo = db.Column(db.Numeric(10,2), default=0)

    compras = db.relationship('Compra', backref='insumo', lazy=True)
    proveedor_insumo = db.relationship('ProveedorInsumo', backref='insumo', lazy=True)
    tanque_insumo = db.relationship('TanqueInsumo', backref='insumo', lazy=True)
    alertas = db.relationship('AlertaStock', backref='insumo', lazy=True)

    def to_dict(self):
        return {
            'id_insumo': self.id_insumo,
            # Sacar codigo el campo codigo
            'codigo': self.codigo,
            'nombre': self.nombre,
            'cantidad': float(self.cantidad),
            'unidad_medida': self.unidad_medida,
            'stock_minimo': float(self.stock_minimo)
        }

# ---------- Proveedores ----------
class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False) 
    razon_social = db.Column(db.String(100))
    #puede existir cuit pot duplicado
    cuit = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(150))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))

    compras = db.relationship('Compra', backref='proveedor', lazy=True)
    proveedor_insumo = db.relationship('ProveedorInsumo', backref='proveedor', lazy=True)

    def to_dict(self):
        return {
            'id_proveedor': self.id_proveedor,
            'nombre': self.nombre, 
            'razon_social': self.razon_social,
            'cuit': self.cuit,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email
        }

    def insumos_detalle(self):
        return [
            {
                'id_proveedor_insumo': pi.id_proveedor_insumo,
                'id_insumo': pi.id_insumo,
                'nombre_insumo': pi.insumo.nombre,
                'precio_actual': float(pi.precio_actual)
            } for pi in self.proveedor_insumo
        ]


# ---------- Proveedor_Insumo (N:M) ----------
class ProveedorInsumo(db.Model):
    __tablename__ = 'proveedor_insumo'
    id_proveedor_insumo = db.Column(db.Integer, primary_key=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'), nullable=False)
    id_insumo = db.Column(db.Integer, db.ForeignKey('insumos.id_insumo'), nullable=False)
    precio_actual = db.Column(db.Numeric(10,2), nullable=False)

    historial_precios = db.relationship('HistorialPrecio', backref='proveedor_insumo', lazy=True)

# ---------- Historial_Precios ----------
class HistorialPrecio(db.Model):
    __tablename__ = 'historial_precios'
    id_historial = db.Column(db.Integer, primary_key=True)
    id_proveedor_insumo = db.Column(db.Integer, db.ForeignKey('proveedor_insumo.id_proveedor_insumo'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    precio = db.Column(db.Numeric(10,2), nullable=False)
    #revisado = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id_historial': self.id_historial,
            'id_proveedor_insumo': self.id_proveedor_insumo,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'precio': float(self.precio),
           #'revisado': self.revisado,
        }

# ---------- Compras ----------
class Compra(db.Model):
    __tablename__ = 'compras'
    id_compra = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'), nullable=False)
    id_insumo = db.Column(db.Integer, db.ForeignKey('insumos.id_insumo'), nullable=False)
    cantidad = db.Column(db.Numeric(10,2), nullable=False)
    precio_unitario = db.Column(db.Numeric(10,2), nullable=False)
    total = db.Column(db.Numeric(12,2), nullable=False)
    # agregar columna revisado
    #revisado = db.Column(db.Boolean, default=False)  # <-- Nueva columna

    def to_dict(self):
        return {
            'id_compra': self.id_compra,
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'id_proveedor': self.id_proveedor,
            'proveedor': self.proveedor.razon_social if self.proveedor else None,
            'id_insumo': self.id_insumo,
            'insumo': self.insumo.nombre if self.insumo else None,
            'cantidad': float(self.cantidad),
            'precio_unitario': float(self.precio_unitario),
            'total': float(self.total),
            #'revisado': self.revisado  # <-- Se agrega para el front
        }

# ---------- Tanques_Fabricados ----------
class TanqueFabricado(db.Model):
    __tablename__ = 'tanques_fabricados'
    id_tanque = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    cliente = db.Column(db.String(100))
    costo_total = db.Column(db.Numeric(12,2), default=0)
   # finalizado = db.Column(db.Boolean, default=False)  # <- nuevo campo

    tanque_insumo = db.relationship('TanqueInsumo', backref='tanque', lazy=True)

    def to_dict(self):
        return {
            'id_tanque': self.id_tanque,
            'modelo': self.modelo,
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'cliente': self.cliente,
            'costo_total': float(self.costo_total),
          #  'finalizado': self.finalizado,
            'insumos_utilizados': [
                {
                    'id_tanque_insumo': ti.id_tanque_insumo,
                    'id_insumo': ti.id_insumo,
                    'nombre_insumo': ti.insumo.nombre,
                    'cantidad_usada': float(ti.cantidad_usada),
                    'costo_unitario': float(ti.costo_unitario)
                } for ti in self.tanque_insumo
            ]
        }

# ---------- Tanque_Insumo (N:M) ----------
class TanqueInsumo(db.Model):
    __tablename__ = 'tanque_insumo'
    id_tanque_insumo = db.Column(db.Integer, primary_key=True)
    id_tanque = db.Column(db.Integer, db.ForeignKey('tanques_fabricados.id_tanque'), nullable=False)
    id_insumo = db.Column(db.Integer, db.ForeignKey('insumos.id_insumo'), nullable=False)
    cantidad_usada = db.Column(db.Numeric(10,2), nullable=False)
    costo_unitario = db.Column(db.Numeric(10,2), nullable=False)
#   operario = db.Column(db.String(100))  # 👈 NUEVO
#   fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)  
    

    def to_dict(self):
        return {
            'id_tanque_insumo': self.id_tanque_insumo,
            'id_tanque': self.id_tanque,
            'id_insumo': self.id_insumo,
            'cantidad_usada': float(self.cantidad_usada),
            'costo_unitario': float(self.costo_unitario),
         #  'operario': self.operario,
         
         #   'editable': not self.tanque.finalizado  # <- indicamos si se puede modificar
        }

# ---------- Alertas_Stock ----------
class AlertaStock(db.Model):
    __tablename__ = 'alertas_stock'
    id_alerta = db.Column(db.Integer, primary_key=True)
    id_insumo = db.Column(db.Integer, db.ForeignKey('insumos.id_insumo'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    cantidad_actual = db.Column(db.Numeric(10,2), nullable=False)
    stock_minimo = db.Column(db.Numeric(10,2), nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')

    def to_dict(self):
        return {
            'id_alerta': self.id_alerta,
            'id_insumo': self.id_insumo,
            'insumo': self.insumo.nombre if self.insumo else None,
            'fecha': self.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'cantidad_actual': float(self.cantidad_actual),
            'stock_minimo': float(self.stock_minimo),
            'estado': self.estado
        }


# ---------- Users ----------
#class User(UserMixin, db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    username = db.Column(db.String(80), unique=True, nullable=False)
#    password = db.Column(db.String(200), nullable=False)
#    role = db.Column(db.String(20), nullable=False)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'role': self.role}

