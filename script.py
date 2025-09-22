import sqlite3

# Connexion à la BDD
def connect_db():
    conn = sqlite3.connect('kahoot_local.db')
    cursor = conn.cursor()
    # Création des tables si elles n'existent pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL  -- 'super_admin', 'super_user', 'prof', 'eleve'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL,  -- 1 à 4
            explanation TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn, cursor

# Ajouter un utilisateur
def add_user(cursor, conn, username, password, role, current_role, current_username):
    allowed_roles = {
        'super_admin': ['super_user', 'prof', 'eleve'],
        'super_user': ['prof', 'eleve'],
        'prof': ['eleve'],
        'eleve': []
    }
    if role not in allowed_roles.get(current_role, []):
        print(f"Vous n'avez pas le droit de créer un utilisateur avec le rôle '{role}'.")
        return
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        print(f"Utilisateur {username} ajouté avec rôle {role}.")
    except sqlite3.IntegrityError:
        print("Utilisateur déjà existant.")

# Inscription pour élèves (self-register)
def register_eleve(cursor, conn):
    username = input("Choisissez un nom d'utilisateur: ")
    password = input("Choisissez un mot de passe: ")
    add_user(cursor, conn, username, password, 'eleve', 'eleve', None)  # Appel avec rôle fictif pour permettre

# Supprimer un utilisateur
def delete_user(cursor, conn, current_role, current_username):
    username_to_delete = input("Nom d'utilisateur à supprimer: ")
    if username_to_delete == current_username:
        print("Vous ne pouvez pas supprimer votre propre compte.")
        return
    cursor.execute("SELECT role FROM users WHERE username=?", (username_to_delete,))
    user_to_delete = cursor.fetchone()
    if not user_to_delete:
        print("Utilisateur non trouvé.")
        return
    role_to_delete = user_to_delete[0]
    allowed_deletes = {
        'super_admin': ['super_user', 'prof', 'eleve'],  # Peut supprimer super_user, prof, eleve
        'super_user': ['prof', 'eleve']                  # Peut supprimer prof, eleve
    }
    if role_to_delete not in allowed_deletes.get(current_role, []):
        print(f"Vous n'avez pas le droit de supprimer un utilisateur avec le rôle '{role_to_delete}'.")
        return
    cursor.execute("DELETE FROM users WHERE username=?", (username_to_delete,))
    conn.commit()
    print(f"Utilisateur {username_to_delete} supprimé.")

# Lister les utilisateurs (pour admins)
def list_users(cursor, role):
    if role in ['super_admin', 'super_user', 'prof']:
        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()
        print("Liste des utilisateurs:")
        for u in users:
            print(f"- {u[0]} ({u[1]})")
    else:
        print("Action non autorisée.")

# Authentification
def login(cursor):
    username = input("Nom d'utilisateur: ")
    password = input("Mot de passe: ")
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    if result:
        return result[0], username  # Retourne rôle et username
    else:
        print("Échec de connexion.")
        return None, None

# Ajouter une question
def add_question(cursor, conn):
    question_text = input("Texte de la question: ")
    option1 = input("Option 1: ")
    option2 = input("Option 2: ")
    option3 = input("Option 3: ")
    option4 = input("Option 4: ")
    correct_option = int(input("Numéro de la bonne option (1-4): "))
    explanation = input("Explication: ")
    cursor.execute('''
        INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (question_text, option1, option2, option3, option4, correct_option, explanation))
    conn.commit()
    print("Question ajoutée.")

# Afficher questions pour quiz avec scoring
def play_quiz(cursor, role):
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    if not questions:
        print("Aucune question disponible. Ajoutez-en d'abord !")
        return
    
    score = 0
    total_questions = len(questions)
    print(f"\nQuiz démarré ! {total_questions} questions. Répondez à toutes pour voir votre score.")

    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}/{total_questions}: {q[1]}")
        print(f"1: {q[2]}")
        print(f"2: {q[3]}")
        print(f"3: {q[4]}")
        print(f"4: {q[5]}")
        if role in ['super_admin', 'super_user', 'prof']:
            print(f"(Admin/Prof only) Bonne réponse: {q[6]}, Explication: {q[7]}")
        
        answer = input("Votre réponse (1-4): ").strip()
        try:
            answer_int = int(answer)
            if 1 <= answer_int <= 4:
                if answer_int == q[6]:
                    print("Correct ! +1 point")
                    score += 1
                else:
                    if role in ['super_admin', 'super_user', 'prof']:
                        print(f"Incorrect ! La bonne réponse était {q[6]}. Explication: {q[7]}")
                    else:
                        print("Incorrect !")
            else:
                print("Réponse invalide (doit être 1-4). Pas de point.")
        except ValueError:
            print("Réponse invalide (doit être un nombre). Pas de point.")
    
    # Affichage final du score
    percentage = (score / total_questions) * 100
    print(f"\nQuiz terminé ! Score: {score}/{total_questions} ({percentage:.0f}%)")
    if percentage >= 80:
        print("Excellent !")
    elif percentage >= 60:
        print("Bien joué !")
    else:
        print("Améliore-toi pour la prochaine !")

# Menu principal
def main():
    conn, cursor = connect_db()
    
    # Bootstrap: Ajoute un super_admin par défaut si aucun utilisateur
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("superadmin", "password", "super_admin"))
            conn.commit()
            print("Super admin par défaut créé: username='superadmin', password='password'.")
        except sqlite3.IntegrityError:
            pass
    
    # Option d'inscription ou login
    print("1: Se connecter")
    print("2: S'inscrire (élèves seulement)")
    initial_choice = input("Choix: ")
    if initial_choice == '2':
        register_eleve(cursor, conn)
    
    role, current_username = login(cursor)
    if role:
        while True:
            print("\nMenu:")
            if role == 'super_admin':
                print("1: Ajouter une question")
                print("2: Ajouter un utilisateur (tous rôles)")
                print("3: Supprimer un utilisateur (super_user/prof/eleve)")
                print("4: Lister les utilisateurs")
            elif role == 'super_user':
                print("1: Ajouter une question")
                print("2: Ajouter un utilisateur (prof/eleve)")
                print("3: Supprimer un utilisateur (prof/eleve)")
                print("4: Lister les utilisateurs")
            elif role == 'prof':
                print("1: Ajouter une question")
                print("2: Ajouter un utilisateur (eleve)")
                print("4: Lister les utilisateurs")
            print("5: Jouer au quiz")
            print("6: Quitter")
            choice = input("Choix: ")
            
            if choice == '1' and role in ['super_admin', 'super_user', 'prof']:
                add_question(cursor, conn)
            elif choice == '2' and role in ['super_admin', 'super_user', 'prof']:
                username = input("Nom d'utilisateur: ")
                password = input("Mot de passe: ")
                user_role = input("Rôle (super_user/prof/eleve selon vos droits): ")
                add_user(cursor, conn, username, password, user_role, role, current_username)
            elif choice == '3' and role in ['super_admin', 'super_user']:
                delete_user(cursor, conn, role, current_username)
            elif choice == '4' and role in ['super_admin', 'super_user', 'prof']:
                list_users(cursor, role)
            elif choice == '5':
                play_quiz(cursor, role)
            elif choice == '6':
                break
            else:
                print("Action non autorisée.")
    
    conn.close()

if __name__ == "__main__":
    main()