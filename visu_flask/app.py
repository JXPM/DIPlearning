from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = "kahoot_secret"  # Nécessaire pour les messages flash

DATABASE = "kahoot_local.db"

# Connexion à la base
def connect_db():
    return sqlite3.connect(DATABASE)

# Page d'accueil
@app.route('/')
def index():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template('index.html', tables=tables)

# Afficher contenu d'une table
@app.route('/table/<table_name>')
def show_table(table_name):
    conn = connect_db()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        data = df.to_dict(orient='records')
        columns = df.columns.tolist()
    except Exception as e:
        flash(f"Erreur lors de la lecture de la table : {e}", "danger")
        data, columns = [], []
    finally:
        conn.close()
    return render_template('table.html', table_name=table_name, data=data, columns=columns)

# Ajouter une question
@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']
        explanation = request.form['explanation']

        if all([question_text, option1, option2, option3, option4, correct_option, explanation]):
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (question_text, option1, option2, option3, option4, correct_option, explanation))
                conn.commit()
                conn.close()
                flash("Question ajoutée avec succès", "success")
                return redirect(url_for('add_question'))
            except Exception as e:
                flash(f"Erreur : {e}", "danger")
        else:
            flash("Veuillez remplir tous les champs", "warning")
    return render_template('add_question.html')

# Ajouter un utilisateur
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if username and password:
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
                conn.commit()
                conn.close()
                flash("Utilisateur ajouté avec succès", "success")
                return redirect(url_for('add_user'))
            except sqlite3.IntegrityError:
                flash("Nom d'utilisateur déjà existant", "danger")
            except Exception as e:
                flash(f"Erreur : {e}", "danger")
        else:
            flash("Tous les champs sont obligatoires", "warning")
    return render_template('add_user.html')

if __name__ == '__main__':
    app.run(debug=True)
