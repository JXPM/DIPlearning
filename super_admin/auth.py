# auth.py

from flask import render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

# Chemin vers ta base de données SQLite
DB_PATH = 'kahoot_local.db'

# Connexion à la base de données
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet l'accès aux colonnes par nom
    return conn

# Décorateur pour protéger les routes nécessitant une authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for('route_login'))  # Le nom de ta route login dans app.py
        return f(*args, **kwargs)
    return decorated_function

# Vue pour la page de connexion
def login_view():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Nom d'utilisateur et mot de passe requis.", "warning")
            return render_template('login.html')

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash("Connexion réussie.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
            return render_template('login.html')

    # GET request
    return render_template('login.html')

# Vue pour la déconnexion
def logout_view():
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('route_login'))
