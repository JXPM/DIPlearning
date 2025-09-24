from flask import Flask, render_template, request, redirect, url_for, flash, session
from auth import login_view, logout_view, login_required, connect_db
import sqlite3

app = Flask(__name__)
app.secret_key = 'un_secret_key_tres_secret_à_modifier'

# --------------------------
# Authentification
# --------------------------

@app.route('/login', methods=['GET', 'POST'])
def route_login():
    return login_view()

@app.route('/logout')
@login_required
def route_logout():
    return logout_view()

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'), role=session.get('role'))

# --------------------------
# Gestion des utilisateurs
# --------------------------

def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    return cursor.fetchall()

def add_user(conn, username, password, role):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        conn.commit()
        return True, "Utilisateur ajouté."
    except sqlite3.IntegrityError:
        return False, "Nom d'utilisateur déjà existant."

def update_user(conn, user_id, username, password, role):
    cursor = conn.cursor()
    if password.strip() == "":
        cursor.execute(
            "UPDATE users SET username = ?, role = ? WHERE id = ?",
            (username, role, user_id)
        )
    else:
        cursor.execute(
            "UPDATE users SET username = ?, password = ?, role = ? WHERE id = ?",
            (username, password, role, user_id)
        )
    conn.commit()
    return True, "Utilisateur mis à jour."

def delete_user(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return True, "Utilisateur supprimé."

@app.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    conn = connect_db()
    users = get_all_users(conn)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', '').strip()
            if not username or not password:
                flash("Nom d'utilisateur et mot de passe requis.", "warning")
            else:
                success, msg = add_user(conn, username, password, role)
                flash(msg, "success" if success else "danger")

        elif action == 'update':
            user_id = request.form.get('user_id')
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', '').strip()
            if not username:
                flash("Le nom d'utilisateur ne peut pas être vide.", "warning")
            else:
                success, msg = update_user(conn, user_id, username, password, role)
                flash(msg, "success" if success else "danger")

        elif action == 'delete':
            user_id = request.form.get('user_id')
            success, msg = delete_user(conn, user_id)
            flash(msg, "success" if success else "danger")

        users = get_all_users(conn)

    conn.close()
    return render_template('users.html', users=users)

# --------------------------
# Gestion des questions
# --------------------------

def get_all_questions(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, question_text, option1, option2, option3, option4, correct_option, explanation
        FROM questions
    """)
    return cursor.fetchall()

def add_question(conn, question_text, option1, option2, option3, option4, correct_option, explanation):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO questions 
        (question_text, option1, option2, option3, option4, correct_option, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (question_text, option1, option2, option3, option4, correct_option, explanation))
    conn.commit()
    return True, "Question ajoutée."

def update_question(conn, q_id, question_text, option1, option2, option3, option4, correct_option, explanation):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE questions
        SET question_text = ?, option1 = ?, option2 = ?, option3 = ?, option4 = ?, correct_option = ?, explanation = ?
        WHERE id = ?
    """, (question_text, option1, option2, option3, option4, correct_option, explanation, q_id))
    conn.commit()
    return True, "Question mise à jour."

def delete_question(conn, q_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (q_id,))
    conn.commit()
    return True, "Question supprimée."

@app.route('/questions', methods=['GET', 'POST'])
@login_required
def manage_questions():
    conn = connect_db()
    questions = get_all_questions(conn)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            question_text = request.form.get('question_text', '').strip()
            option1 = request.form.get('option1', '').strip()
            option2 = request.form.get('option2', '').strip()
            option3 = request.form.get('option3', '').strip()
            option4 = request.form.get('option4', '').strip()
            correct_option = int(request.form.get('correct_option', 0))
            explanation = request.form.get('explanation', '').strip()

            if not all([question_text, option1, option2, option3, option4, explanation]) or correct_option not in [1, 2, 3, 4]:
                flash("Tous les champs doivent être remplis correctement.", "warning")
            else:
                success, msg = add_question(conn, question_text, option1, option2, option3, option4, correct_option, explanation)
                flash(msg, "success" if success else "danger")

        elif action == 'update':
            q_id = request.form.get('question_id')
            question_text = request.form.get('question_text', '').strip()
            option1 = request.form.get('option1', '').strip()
            option2 = request.form.get('option2', '').strip()
            option3 = request.form.get('option3', '').strip()
            option4 = request.form.get('option4', '').strip()
            correct_option = int(request.form.get('correct_option', 0))
            explanation = request.form.get('explanation', '').strip()

            if not all([question_text, option1, option2, option3, option4, explanation]) or correct_option not in [1, 2, 3, 4]:
                flash("Tous les champs doivent être remplis correctement.", "warning")
            else:
                success, msg = update_question(conn, q_id, question_text, option1, option2, option3, option4, correct_option, explanation)
                flash(msg, "success" if success else "danger")

        elif action == 'delete':
            q_id = request.form.get('question_id')
            success, msg = delete_question(conn, q_id)
            flash(msg, "success" if success else "danger")

        questions = get_all_questions(conn)

    conn.close()
    return render_template('questions.html', questions=questions)

# --------------------------
# Lancement de l'application
# --------------------------

if __name__ == "__main__":
    app.run(debug=True)
