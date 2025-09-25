# app.py
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'diplearning_secret_key_2025'
app.config['DATABASE'] = '/home/pi/diplearning_local.db'

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user_type = request.form['user_type']  # 'eleve' ou 'prof'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_type == 'eleve':
            # MODIFICATION : Accepte n'importe quel nom d'utilisateur pour les élèves
            # Vérifie d'abord si l'élève existe déjà
            cursor.execute("SELECT username, role FROM users WHERE username=? AND role='eleve'", 
                          (username,))
            user = cursor.fetchone()
            
            if not user:
                # Si l'élève n'existe pas, on le crée automatiquement
                try:
                    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, NULL, ?)",
                                  (username, 'eleve'))
                    conn.commit()
                    # Maintenant on récupère l'utilisateur créé
                    cursor.execute("SELECT username, role FROM users WHERE username=? AND role='eleve'", 
                                  (username,))
                    user = cursor.fetchone()
                except sqlite3.IntegrityError:
                    # En cas de conflit (très rare), on réessaye la sélection
                    cursor.execute("SELECT username, role FROM users WHERE username=? AND role='eleve'", 
                                  (username,))
                    user = cursor.fetchone()
        else:
            # Connexion prof : nom + mot de passe (reste strict)
            password = request.form['password']
            cursor.execute("SELECT username, role FROM users WHERE username=? AND password=? AND role IN ('prof', 'super_admin', 'super_user')", 
                          (username, password))
            user = cursor.fetchone()
        
        conn.close()
        
        if user:
            session['user'] = {'username': user[0], 'role': user[1]}
            return redirect(url_for('dashboard'))
        else:
            error_msg = "Identifiants incorrects pour professeur"
            return render_template('login.html', error=error_msg)
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user=session['user'])

@app.route('/quiz')
def quiz():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Seuls les profs peuvent voir toutes les questions
    if session['user']['role'] == 'eleve':
        return redirect(url_for('play_quiz'))
    
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions').fetchall()
    conn.close()
    
    return render_template('quiz.html', questions=questions)

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Seuls les profs peuvent ajouter des questions
    if session['user']['role'] == 'eleve':
        return "Accès réservé aux enseignants", 403
    
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form['question_text'],
                request.form['option1'],
                request.form['option2'],
                request.form['option3'],
                request.form['option4'],
                int(request.form['correct_option']),
                request.form['explanation']
            ))
            conn.commit()
            return render_template('add_question.html', success="Question ajoutée !")
        except Exception as e:
            return render_template('add_question.html', error=str(e))
        finally:
            conn.close()
    
    return render_template('add_question.html')

@app.route('/play_quiz')
def play_quiz():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    questions = conn.execute('SELECT id, question_text, option1, option2, option3, option4 FROM questions LIMIT 10').fetchall()
    conn.close()
    
    return render_template('play_quiz.html', questions=questions)

@app.route('/admin')
def admin():
    if 'user' not in session or session['user']['role'] != 'super_admin':
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, role FROM users ORDER BY role, username').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users, session=session)

@app.route('/add_prof', methods=['POST'])
def add_prof():
    """Ajouter un nouveau professeur"""
    if 'user' not in session or session['user']['role'] != 'super_admin':
        return jsonify({'error': 'Accès refusé'}), 403
    
    username = request.form['username']
    password = request.form['password']
    
    if not username or not password:
        return jsonify({'error': 'Nom et mot de passe requis'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, password, 'prof'))
        conn.commit()
        return jsonify({'success': f'Professeur {username} ajouté avec succès'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Ce nom d\'utilisateur existe déjà'}), 400
    finally:
        conn.close()

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Supprimer un utilisateur"""
    if 'user' not in session or session['user']['role'] != 'super_admin':
        return jsonify({'error': 'Accès refusé'}), 403
    
    # Empêcher l'auto-suppression
    current_user = session['user']['username']
    conn = get_db_connection()
    
    user_to_delete = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if user_to_delete and user_to_delete[0] == current_user:
        conn.close()
        return jsonify({'error': 'Vous ne pouvez pas vous supprimer vous-même'}), 400
    
    try:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': 'Utilisateur supprimé avec succès'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/add_eleve', methods=['POST'])
def add_eleve():
    """Ajouter un nouvel élève"""
    if 'user' not in session or session['user']['role'] != 'super_admin':
        return jsonify({'error': 'Accès refusé'}), 403
    
    username = request.form['username']
    
    if not username:
        return jsonify({'error': 'Nom d\'élève requis'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, NULL, ?)",
                    (username, 'eleve'))
        conn.commit()
        return jsonify({'success': f'Élève {username} ajouté avec succès'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Ce nom d\'élève existe déjà'}), 400
    finally:
        conn.close()

@app.route('/wikipedia')
def wikipedia():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect('http://192.168.4.1:8080')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']):
        print("Base de données non trouvée. Exécutez init_db.py")
        exit(1)
    
    print("Flask démarré sur http://192.168.4.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)