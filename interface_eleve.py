import streamlit as st
import sqlite3
import random

DB_PATH = "kahoot_local.db"

# --- Fonction rerun compatible ---
def rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        # Pour les versions plus récentes de Streamlit, on force un rerun via exception
        from streamlit.runtime.scriptrunner import RerunException
        from streamlit.runtime.scriptrunner import script_runner
        raise RerunException(script_runner.RerunData())
# -----------------------------------

# Connexion DB
def connect_db():
    return sqlite3.connect(DB_PATH)

# Créer table results si elle n'existe pas
def create_results_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Récupérer questions
def get_questions():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question_text, option1, option2, option3, option4, correct_option, explanation FROM questions")
    questions = cursor.fetchall()
    conn.close()
    return questions

# Authentifier utilisateur élève
def login(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user and user[1] == 'eleve':
        return user[0]  # user_id
    return None

# Vérifier si l'élève a déjà passé le quiz
def has_passed_quiz(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM results WHERE user_id=?", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# Enregistrer résultat
def save_result(user_id, score, total):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO results (user_id, score, total) VALUES (?, ?, ?)", (user_id, score, total))
    conn.commit()
    conn.close()

# Récupérer historique des scores
def get_results(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT score, total, date FROM results WHERE user_id=? ORDER BY date DESC", (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

# Initialiser la table results
create_results_table()

st.title("🧑‍🎓 Quiz Élève - Connexion")

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.quiz_finished = False
    st.session_state.question_index = 0
    st.session_state.score = 0
    st.session_state.answers = []

if st.session_state.user_id is None:
    # Formulaire login
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            user_id = login(username, password)
            if user_id:
                st.success("Connexion réussie !")
                st.session_state.user_id = user_id
                st.session_state.username = username  # On garde le nom pour affichage
                # Reset quiz state
                st.session_state.question_index = 0
                st.session_state.score = 0
                st.session_state.quiz_finished = False
                st.session_state.answers = []
                rerun()
            else:
                st.error("Identifiants invalides ou rôle non autorisé.")
else:
    # Utilisateur connecté
    st.write(f"Connecté en tant que : **{st.session_state.username}**")



    # Récupérer questions
    questions = get_questions()
    if not questions:
        st.warning("Aucune question disponible. Contacte ton enseignant.")
        st.stop()

    random.seed(st.session_state.user_id)  # Pour cohérence quiz même ordre par élève
    questions = list(questions)
    random.shuffle(questions)

    if st.session_state.question_index >= len(questions):
        st.session_state.quiz_finished = True

    if not st.session_state.quiz_finished:
        current_q = questions[st.session_state.question_index]
        q_id, q_text, op1, op2, op3, op4, correct_option, explanation = current_q

        st.subheader(f"Question {st.session_state.question_index + 1}/{len(questions)}")
        st.write(q_text)

        options = [op1, op2, op3, op4]
        selected_option = st.radio("Choisissez une réponse :", options, key=f"q_{q_id}")

        if st.button("Valider la réponse"):
            if selected_option is None:
                st.warning("Veuillez sélectionner une réponse.")
            else:
                selected_index = options.index(selected_option) + 1
                st.session_state.answers.append((q_id, selected_index))

                if selected_index == correct_option:
                    st.success("✅ Bonne réponse !")
                    st.session_state.score += 1
                else:
                    st.error("❌ Mauvaise réponse.")
                    st.info(f"La bonne réponse était : **{options[correct_option - 1]}**")
                    st.markdown(f"📘 Explication : {explanation}")

                st.session_state.question_index += 1
                rerun()

    else:
        st.success("🎉 Quiz terminé !")
        st.write(f"Votre score : **{st.session_state.score} / {len(questions)}**")

        # Enregistrer résultat si pas déjà enregistré
        if not has_passed_quiz(st.session_state.user_id):
            save_result(st.session_state.user_id, st.session_state.score, len(questions))

        st.markdown("### 📚 Résumé :")
        for i, (q_id, selected) in enumerate(st.session_state.answers):
            q = next((q for q in questions if q[0] == q_id), None)
            if q:
                correct = q[6]
                explanation = q[7]
                q_text = q[1]
                options = q[2:6]

                st.markdown(f"**Q{i+1}: {q_text}**")
                st.write(f"Votre réponse : {options[selected - 1]}")
                if selected == correct:
                    st.success("✅ Correct")
                else:
                    st.error(f"❌ Incorrect — Bonne réponse : {options[correct - 1]}")
                    st.markdown(f"💡 Explication : {explanation}")

        if st.button("Déconnexion"):
            for key in ['user_id', 'quiz_finished', 'question_index', 'score', 'answers', 'username']:
                if key in st.session_state:
                    del st.session_state[key]
            rerun()
