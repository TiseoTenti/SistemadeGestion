import os
from flask import Flask, render_template,redirect, url_for, request, flash
from flask_login import LoginManager, login_required, current_user 
from models import db, User, Insumo, TanqueInsumo, TanqueFabricado
from routes import register_blueprints  # Se registra api_user y demás blueprints


from datetime import datetime
from decimal import Decimal
# ------------------------------------------------------------
# FACTORY PATTERN: función que crea y configura la app
# ------------------------------------------------------------
def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'clave_secreta_segura'
    import os

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
         'DATABASE_URL',
         'postgresql+psycopg2://inventario_user:Daniela33@db:5432/inventario_db'
)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)

    # Login Manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'api_user.login'  # apunta a blueprint

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar blueprints
    register_blueprints(app)

    # Crear DB y admin si no existe
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='administrador')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("🟢 Admin creado: usuario='admin', pass='admin123'")

    # ------------------- RUTAS PROTEGIDAS -------------------
    @app.route('/')
    @login_required
    def index():
        # Consulta los insumos con bajo stock
        low_stock = Insumo.query.filter(Insumo.cantidad <= Insumo.stock_minimo).all()
        return render_template('index.html', low_stock=low_stock)

    @app.route('/insumos')
    @login_required
    def pagina_insumos():
        return render_template('insumos.html')

    @app.route('/proveedores')
    @login_required
    def pagina_proveedores():
        return render_template('proveedores.html')

    @app.route('/compras')
    @login_required
    def pagina_compras():
        is_admin = getattr(current_user, 'role', 'user') == 'administrador'
        return render_template('compras.html', current_user_is_admin=is_admin)

    @app.route('/tanques')
    @login_required
    def pagina_tanques():
        return render_template('tanques.html')

    @app.route('/alertas')
    @login_required
    def pagina_alertas():
        return render_template('alertas.html')

    @app.route('/reportes')
    @login_required
    def pagina_reportes():
        return render_template('reportes.html')

    @app.route('/insumos_salida', methods=['GET', 'POST'])
    @login_required
    def registrar_salida_insumo():
        is_admin = getattr(current_user, 'role', 'user') == 'administrador'
        return render_template('insumos_salida.html', current_user_is_admin=is_admin)

    return app




# ------------------------------------------------------------
# EJECUCIÓN
# ------------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
