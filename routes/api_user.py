from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from forms import LoginForm

api_user = Blueprint('api_user', __name__, url_prefix='/user')


# -------- LOGIN --------
@api_user.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

# -------- LOGOUT --------
@api_user.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('api_user.login'))


# -------- CREAR NUEVO USUARIO --------
@api_user.route('/new', methods=['GET', 'POST'])
@login_required
def user_new():
    if current_user.role != 'administrador':
        flash('No autorizado', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not username or not password or not role:
            flash('Faltan datos', 'danger')
            return redirect(url_for('api_user.user_new'))

        # 🔍 Verificar si el usuario ya existe
        usuario_existente = User.query.filter_by(username=username).first()
        if usuario_existente:
            flash('El nombre de usuario ya existe', 'warning')
            return redirect(url_for('api_user.user_new'))

        # ✅ Crear usuario
        u = User(username=username, role=role)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        flash('✅Usuario creado correctamente!', 'success')
        return redirect(url_for('api_user.user_new'))

    users = User.query.all()
    return render_template('user.html', users=users)


