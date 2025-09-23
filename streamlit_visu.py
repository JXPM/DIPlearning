import streamlit as st
import sqlite3
import pandas as pd




# Connexion à la base
def connect_db():
    return sqlite3.connect("kahoot_local.db")

# Récupérer les noms des tables dans la base
def get_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

# Charger les données d'une table donnée
def get_table_data(table_name):
    conn = connect_db()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        st.error(f"Erreur lors de la lecture de la table {table_name} : {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

# ---------- INTERFACE STREAMLIT ----------------

st.set_page_config(page_title="Kahoot App", layout="centered")

st.title("🎓 Kahoot - Interface Classe")

# Choisir la table à afficher
st.subheader("📊 Explorer les données de la base")

tables = get_tables()
selected_table = st.selectbox("Choisissez une table :", tables)

if selected_table:
    df = get_table_data(selected_table)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        # Export CSV (bonus)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"{selected_table}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Aucune donnée trouvée dans cette table.")

st.markdown("---")
st.subheader("➕ Ajouter une nouvelle question")

with st.form("form_ajout_question"):
    question_text = st.text_input("Texte de la question")
    option1 = st.text_input("Option 1")
    option2 = st.text_input("Option 2")
    option3 = st.text_input("Option 3")
    option4 = st.text_input("Option 4")
    correct_option = st.selectbox("Bonne réponse (numéro)", [1, 2, 3, 4])
    explanation = st.text_area("Explication de la réponse")

    submitted_question = st.form_submit_button("Ajouter la question")

    if submitted_question:
        if all([question_text, option1, option2, option3, option4, explanation]):
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (question_text, option1, option2, option3, option4, correct_option, explanation))
                conn.commit()
                conn.close()
                st.success("✅ Question ajoutée avec succès !")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
        else:
            st.warning("Veuillez remplir **tous les champs**.")

st.markdown("---")
st.subheader("👤 Ajouter un nouvel utilisateur")

with st.form("form_ajout_user"):
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    role = st.selectbox("Rôle", ["eleve", "prof", "super_user", "super_admin"])

    submitted_user = st.form_submit_button("Ajouter l'utilisateur")

    if submitted_user:
        if username and password:
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
                conn.commit()
                conn.close()
                st.success(f"✅ Utilisateur '{username}' ajouté avec le rôle '{role}'")
            except sqlite3.IntegrityError:
                st.error("❌ Nom d'utilisateur déjà existant.")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
        else:
            st.warning("Veuillez remplir tous les champs.")
