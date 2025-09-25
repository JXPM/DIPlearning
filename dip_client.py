import paho.mqtt.client as mqtt
import json
import time

response = None

def on_message(client, userdata, msg):
    global response
    response = json.loads(msg.payload.decode())

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect("192.168.1.42", 1883, 60)  # Remplace par IP du Pi
client.subscribe("diplearning/response")
client.loop_start()

def send_request(data):
    global response
    response = None
    client.publish("diplearning/request", json.dumps(data))
    time.sleep(1)
    return response

# --- Connexion utilisateur ---
username = input("Nom d'utilisateur : ")
password = input("Mot de passe : ")

login_resp = send_request({"action": "login", "username": username, "password": password})

if login_resp["status"] != "ok":
    print("❌ Connexion échouée :", login_resp.get("message"))
    exit()

role = login_resp["role"]
print(f"✅ Connecté en tant que {username} (rôle: {role})")

# --- Menu dynamique selon rôle ---
while True:
    if role == "super_admin":
        print("\n1. Ajouter un utilisateur\n2. Ajouter une question\n3. Voir questions\n4. Quitter")
    elif role in ["prof", "super_user"]:
        print("\n1. Ajouter une question\n2. Voir questions\n3. Quitter")
    else:  # élève
        print("\n1. Jouer au quiz\n2. Quitter")

    choice = input("Votre choix : ")

    if role == "super_admin" and choice == "1":
        u = input("Nom nouvel utilisateur : ")
        p = input("Mot de passe : ")
        r = input("Rôle (eleve/prof/super_user) : ")
        resp = send_request({"action": "add_user", "role_requester": role, "username": u, "password": p, "role": r})
        print(resp)

    elif role in ["super_admin", "prof", "super_user"] and choice == "2":
        q = input("Question : ")
        o1 = input("Option 1 : ")
        o2 = input("Option 2 : ")
        o3 = input("Option 3 : ")
        o4 = input("Option 4 : ")
        correct = int(input("Bonne réponse (1-4) : "))
        exp = input("Explication : ")
        resp = send_request({"action": "add_question", "role_requester": role, "question_text": q,
                             "option1": o1, "option2": o2, "option3": o3, "option4": o4,
                             "correct_option": correct, "explanation": exp})
        print(resp)

    elif role in ["super_admin", "prof", "super_user"] and choice == "3":
        resp = send_request({"action": "get_questions"})
        for q in resp["questions"]:
            print(q)

    elif role == "eleve" and choice == "1":
        resp = send_request({"action": "play_quiz"})
        score = 0
        for q in resp["questions"]:
            print(f"\n{q[1]}")
            print(f"1. {q[2]}  2. {q[3]}  3. {q[4]}  4. {q[5]}")
            ans = int(input("Votre réponse : "))
            if ans == q[6]:
                print("✅ Correct")
                score += 1
            else:
                print("❌ Incorrect")
        print(f"\nVotre score : {score}/{len(resp['questions'])}")

    elif choice == "4" or (role == "eleve" and choice == "2"):
        break
    else:
        print("Choix invalide.")
