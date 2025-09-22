import sqlite3, json, time
import paho.mqtt.client as mqtt

BROKER_IP = "localhost"  # ou IP hotspot
QUESTION_TOPIC = "diplearning/question"
ANSWER_TOPIC = "diplearning/answer/+"
SCORE_TOPIC = "diplearning/score"

# Connexion BDD
conn = sqlite3.connect("kahoot_local.db")
cursor = conn.cursor()

# MQTT
client = mqtt.Client("Prof")
client.connect(BROKER_IP)

scores = {}

def on_message(client, userdata, msg):
    topic = msg.topic
    username = topic.split("/")[-1]
    answer = int(msg.payload.decode())
    q = userdata['current_question']
    if username not in scores:
        scores[username] = 0
    if answer == q[6]:
        scores[username] += 1
    print(f"{username} score: {scores[username]}")
    client.publish(SCORE_TOPIC, json.dumps(scores))

client.user_data_set({'current_question': None})
client.subscribe(ANSWER_TOPIC)
client.on_message = on_message
client.loop_start()

cursor.execute("SELECT * FROM questions")
questions = cursor.fetchall()
for q in questions:
    payload = {"id": q[0], "question": q[1], "options": [q[2],q[3],q[4],q[5]]}
    client.user_data_set({'current_question': q})
    client.publish(QUESTION_TOPIC, json.dumps(payload))
    time.sleep(10)  # temps pour répondre

print("Quiz terminé ! Scores:", scores)
client.loop_stop()
conn.close()
