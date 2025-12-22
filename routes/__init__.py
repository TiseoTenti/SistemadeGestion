# routes/__init__.py
def register_blueprints(app):
    from routes.api_insumos import insumos_bp
    from routes.api_proveedores import proveedores_bp
    from routes.api_compras import compras_bp
    from routes.api_tanques import tanques_bp
    from routes.api_alertas import alertas_bp
    from routes.api_reportes import reportes_bp
    from routes.api_user import api_user
    from routes.api_insumos_salida import insumos_salida_bp



    app.register_blueprint(insumos_bp)
    app.register_blueprint(proveedores_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(tanques_bp)
    app.register_blueprint(alertas_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(api_user)
    app.register_blueprint(insumos_salida_bp)

   
