import streamlit as st
import sqlite3

DB_PATH = 'kahoot_local.db'

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
    return conn

# --------------------------
# Fonctions CRUD Users
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

# --------------------------
# Fonctions CRUD Questions
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

# --------------------------
# Interface Streamlit
# --------------------------

def main():
    st.title("Interface Super Admin - Gestion Kahoot")

    conn = connect_db()

    menu = ["Gérer les utilisateurs", "Gérer les questions"]
    choice = st.sidebar.selectbox("Menu", menu, key="main_menu")

    if choice == "Gérer les utilisateurs":
        st.header("Gestion des utilisateurs")

        # Chargement initial des utilisateurs
        users = get_all_users(conn)

        # Affichage tableau utilisateurs
        user_df = [{"ID": u["id"], "Username": u["username"], "Rôle": u["role"]} for u in users]
        st.write("### Utilisateurs existants")
        st.table(user_df)

        # Ajouter utilisateur
        st.write("---")
        st.subheader("Ajouter un nouvel utilisateur")
        new_username = st.text_input("Nom d'utilisateur", key="new_username")
        new_password = st.text_input("Mot de passe", type="password", key="new_password")
        new_role = st.selectbox("Rôle", ['super_admin', 'super_user', 'prof', 'eleve'], key="new_role")

        if st.button("Ajouter utilisateur", key="add_user_btn"):
            if new_username.strip() == "" or new_password.strip() == "":
                st.error("Nom d'utilisateur et mot de passe requis")
            else:
                success, msg = add_user(conn, new_username.strip(), new_password.strip(), new_role)
                if success:
                    st.success(msg)
                    users = get_all_users(conn)  # Recharger liste utilisateurs après ajout
                else:
                    st.error(msg)

        # Modifier / Supprimer utilisateur
        st.write("---")
        st.subheader("Modifier / Supprimer un utilisateur")

        user_ids = [u["id"] for u in users]
        if user_ids:
            selected_user_id = st.selectbox("Sélectionnez un utilisateur", user_ids, key="selected_user_id")
            selected_user = next((u for u in users if u["id"] == selected_user_id), None)

            if selected_user:
                edit_username = st.text_input("Nom d'utilisateur", selected_user["username"], key=f"edit_username_{selected_user['id']}")
                edit_password = st.text_input("Nouveau mot de passe (laisser vide pour ne pas changer)", type="password", key=f"edit_password_{selected_user['id']}")
                roles_list = ['super_admin', 'super_user', 'prof', 'eleve']
                edit_role = st.selectbox(
                    "Rôle",
                    roles_list,
                    index=roles_list.index(selected_user["role"]),
                    key=f"edit_role_{selected_user['id']}"
                )

                if st.button("Mettre à jour utilisateur", key=f"update_user_{selected_user['id']}"):
                    if edit_username.strip() == "":
                        st.error("Le nom d'utilisateur ne peut pas être vide")
                    else:
                        success, msg = update_user(conn, selected_user_id, edit_username.strip(), edit_password, edit_role)
                        if success:
                            st.success(msg)
                            users = get_all_users(conn)  # Recharger liste utilisateurs après update
                        else:
                            st.error(msg)

                # Gestion confirmation suppression utilisateur
                if "confirm_delete" not in st.session_state:
                    st.session_state.confirm_delete = False

                if st.button("Supprimer utilisateur", key=f"delete_user_{selected_user['id']}"):
                    st.session_state.confirm_delete = True

                if st.session_state.confirm_delete:
                    confirm = st.checkbox("Confirmer la suppression de l'utilisateur ?", key=f"confirm_delete_user_{selected_user['id']}")
                    if confirm:
                        success, msg = delete_user(conn, selected_user_id)
                        if success:
                            st.success(msg)
                            st.session_state.confirm_delete = False
                            users = get_all_users(conn)  # Recharger liste utilisateurs après suppression
                        else:
                            st.error(msg)
                    else:
                        st.warning("Cochez la case pour confirmer la suppression.")

    elif choice == "Gérer les questions":
        st.header("Gestion des questions")

        # Chargement initial des questions
        questions = get_all_questions(conn)

        # Affichage tableau questions
        q_df = []
        for q in questions:
            q_df.append({
                "ID": q["id"],
                "Question": q["question_text"],
                "Option 1": q["option1"],
                "Option 2": q["option2"],
                "Option 3": q["option3"],
                "Option 4": q["option4"],
                "Bonne option": q["correct_option"],
                "Explication": q["explanation"]
            })
        st.write("### Questions existantes")
        st.table(q_df)

        # Ajouter question
        st.write("---")
        st.subheader("Ajouter une nouvelle question")
        new_q_text = st.text_input("Texte de la question", key="new_q_text")
        new_opt1 = st.text_input("Option 1", key="new_opt1")
        new_opt2 = st.text_input("Option 2", key="new_opt2")
        new_opt3 = st.text_input("Option 3", key="new_opt3")
        new_opt4 = st.text_input("Option 4", key="new_opt4")
        new_correct_opt = st.number_input("Numéro de la bonne option (1-4)", min_value=1, max_value=4, step=1, key="new_correct_opt")
        new_explanation = st.text_area("Explication", key="new_explanation")

        if st.button("Ajouter question", key="add_question_btn"):
            if not all([new_q_text.strip(), new_opt1.strip(), new_opt2.strip(), new_opt3.strip(), new_opt4.strip(), new_explanation.strip()]):
                st.error("Tous les champs doivent être remplis")
            else:
                success, msg = add_question(conn, new_q_text.strip(), new_opt1.strip(), new_opt2.strip(), new_opt3.strip(), new_opt4.strip(), new_correct_opt, new_explanation.strip())
                if success:
                    st.success(msg)
                    questions = get_all_questions(conn)  # Recharger liste questions après ajout
                else:
                    st.error(msg)

        # Modifier / Supprimer question
        st.write("---")
        st.subheader("Modifier / Supprimer une question")

        question_ids = [q["id"] for q in questions]
        if question_ids:
            selected_q_id = st.selectbox("Sélectionnez une question", question_ids, key="selected_q_id")

            selected_q = next((q for q in questions if q["id"] == selected_q_id), None)

            if selected_q:
                edit_q_text = st.text_input("Texte de la question", selected_q["question_text"], key=f"edit_q_text_{selected_q['id']}")
                edit_opt1 = st.text_input("Option 1", selected_q["option1"], key=f"edit_opt1_{selected_q['id']}")
                edit_opt2 = st.text_input("Option 2", selected_q["option2"], key=f"edit_opt2_{selected_q['id']}")
                edit_opt3 = st.text_input("Option 3", selected_q["option3"], key=f"edit_opt3_{selected_q['id']}")
                edit_opt4 = st.text_input("Option 4", selected_q["option4"], key=f"edit_opt4_{selected_q['id']}")
                edit_correct_opt = st.number_input(
                    "Numéro de la bonne option (1-4)",
                    min_value=1, max_value=4, step=1,
                    value=selected_q["correct_option"],
                    key=f"edit_correct_opt_{selected_q['id']}"
                )
                edit_explanation = st.text_area("Explication", selected_q["explanation"], key=f"edit_explanation_{selected_q['id']}")

                if st.button("Mettre à jour question", key=f"update_question_{selected_q['id']}"):
                    if not all([edit_q_text.strip(), edit_opt1.strip(), edit_opt2.strip(), edit_opt3.strip(), edit_opt4.strip(), edit_explanation.strip()]):
                        st.error("Tous les champs doivent être remplis")
                    else:
                        success, msg = update_question(
                            conn, selected_q_id,
                            edit_q_text.strip(), edit_opt1.strip(), edit_opt2.strip(), edit_opt3.strip(), edit_opt4.strip(),
                            edit_correct_opt,
                            edit_explanation.strip()
                        )
                        if success:
                            st.success(msg)
                            questions = get_all_questions(conn)  # Recharger liste questions après update
                        else:
                            st.error(msg)

                # Gestion confirmation suppression question
                if "confirm_delete_q" not in st.session_state:
                    st.session_state.confirm_delete_q = False

                if st.button("Supprimer question", key=f"delete_question_{selected_q['id']}"):
                    st.session_state.confirm_delete_q = True

                if st.session_state.confirm_delete_q:
                    confirm = st.checkbox("Confirmer la suppression de la question ?", key=f"confirm_delete_question_{selected_q['id']}")
                    if confirm:
                        success, msg = delete_question(conn, selected_q_id)
                        if success:
                            st.success(msg)
                            st.session_state.confirm_delete_q = False
                            questions = get_all_questions(conn)  # Recharger liste questions après suppression
                        else:
                            st.error(msg)
                    else:
                        st.warning("Cochez la case pour confirmer la suppression.")

    conn.close()

if __name__ == "__main__":
    main()
