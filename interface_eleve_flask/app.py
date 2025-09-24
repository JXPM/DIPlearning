from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import datetime

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète'
DB_PATH = "kahoot_local.db"

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet accès aux colonnes par nom
    return conn

def get_question_ids():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM questions")
    rows = cursor.fetchall()
    conn.close()
    return [row['id'] for row in rows]

def get_question_by_id(question_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question_text, option1, option2, option3, option4, correct_option, explanation "
        "FROM questions WHERE id=?",
        (question_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=? AND password=? AND role='eleve'", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def save_result(user_id, score, total):
    conn = connect_db()
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute(
        "INSERT INTO results (user_id, score, total, date) VALUES (?, ?, ?, ?)",
        (user_id, score, total, now)
    )
    conn.commit()
    conn.close()

def get_results(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT score, total, date FROM results WHERE user_id=? ORDER BY date DESC", (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_id = login_user(username, password)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            session['question_index'] = 0
            session['score'] = 0
            session['answers'] = []
            session['quiz_finished'] = False
            session.pop('shuffled_question_ids', None)  # Réinitialiser la liste des questions
            return redirect(url_for("quiz"))
        else:
            return render_template("login.html", error="Connexion échouée.")
    return render_template("login.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if 'user_id' not in session:
        return redirect(url_for("login"))

    if 'shuffled_question_ids' not in session:
        question_ids = get_question_ids()
        random.seed(session['user_id'])
        session['shuffled_question_ids'] = random.sample(question_ids, len(question_ids))
    
    q_index = session.get('question_index', 0)
    total_questions = len(session['shuffled_question_ids'])

    if session.get('quiz_finished', False):
        return redirect(url_for("summary"))

    current_question_id = session['shuffled_question_ids'][q_index]
    current_q = get_question_by_id(current_question_id)

    if request.method == "POST":
        selected = request.form.get("selected")
        if selected is None:
            return render_template("quiz.html", question=current_q, index=q_index + 1, total=total_questions, error="Veuillez sélectionner une réponse.")

        selected = int(selected)

        session.setdefault('answers', []).append((current_question_id, selected))
        correct_option = current_q['correct_option']

        if selected == correct_option:
            session['score'] = session.get('score', 0) + 1

        session['question_index'] = q_index + 1

        if session['question_index'] >= total_questions:
            session['quiz_finished'] = True
            save_result(session['user_id'], session.get('score', 0), total_questions)
            return redirect(url_for("summary"))

        return redirect(url_for("quiz"))

    return render_template("quiz.html", question=current_q, index=q_index + 1, total=total_questions)

@app.route("/summary")
def summary():
    if 'user_id' not in session or not session.get('quiz_finished', False):
        return redirect(url_for("login"))

    results = get_results(session['user_id'])

    detailed_answers = []
    all_question_ids = session.get('shuffled_question_ids', [])
    answers = session.get('answers', [])

    for i, (q_id, selected) in enumerate(answers):
        q = get_question_by_id(q_id)
        if q:
            correct = q['correct_option']
            explanation = q['explanation']
            options = [q['option1'], q['option2'], q['option3'], q['option4']]
            detailed_answers.append({
                'question': q['question_text'],
                'selected': options[selected - 1],
                'correct': options[correct - 1],
                'is_correct': selected == correct,
                'explanation': explanation
            })

    return render_template("summary.html",
                           score=session.get('score', 0),
                           total=len(all_question_ids),
                           answers=detailed_answers,
                           history=results,
                           username=session.get('username', ''))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
