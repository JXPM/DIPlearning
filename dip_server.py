import paho.mqtt.client as mqtt
import sqlite3
import json

DB_FILE = "diplearning_local.db"

# --- Gestion des requêtes ---
def handle_message(request):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        data = json.loads(request)
        action = data.get("action")

        # --- LOGIN ---
        if action == "login":
            cursor.execute("SELECT role FROM users WHERE username=? AND password=?",
                           (data["username"], data["password"]))
            result = cursor.fetchone()
            if result:
                return {"status": "ok", "role": result[0]}
            else:
                return {"status": "fail", "message": "Identifiants invalides."}

        # --- AJOUT UTILISATEUR ---
        elif action == "add_user":
            if data["role_requester"] != "super_admin":
                return {"status": "fail", "message": "Permission refusée."}
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           (data["username"], data["password"], data["role"]))
            conn.commit()
            return {"status": "ok", "message": f"Utilisateur {data['username']} ajouté."}

        # --- AJOUT QUESTION ---
        elif action == "add_question":
            if data["role_requester"] not in ["prof", "super_admin", "super_user"]:
                return {"status": "fail", "message": "Permission refusée."}
            cursor.execute("""
                INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data["question_text"], data["option1"], data["option2"],
                  data["option3"], data["option4"], data["correct_option"], data["explanation"]))
            conn.commit()
            return {"status": "ok", "message": "Question ajoutée."}

        # --- OBTENIR QUESTIONS ---
        elif action == "get_questions":
            cursor.execute("SELECT id, question_text, option1, option2, option3, option4 FROM questions")
            rows = cursor.fetchall()
            return {"status": "ok", "questions": rows}

        # --- JOUER QUIZ ---
        elif action == "play_quiz":
            cursor.execute("SELECT id, question_text, option1, option2, option3, option4, correct_option FROM questions")
            questions = cursor.fetchall()
            return {"status": "ok", "questions": questions}

        else:
            return {"status": "fail", "message": "Action inconnue."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

# --- MQTT ---
def on_message(client, userdata, msg):
    request = msg.payload.decode()
    response = handle_message(request)
    client.publish("diplearning/response", json.dumps(response))

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.subscribe("diplearning/request")
print("✅ Serveur DIPlearning démarré (MQTT en écoute sur diplearning/request)")
client.loop_forever()
