import json
import paho.mqtt.client as mqtt

username = input("Nom d'utilisateur: ")
broker_ip = input("IP du prof: ")

QUESTION_TOPIC = "diplearning/question"
SCORE_TOPIC = "diplearning/score"
ANSWER_TOPIC = f"diplearning/answer/{username}"

def on_message(client, userdata, msg):
    if msg.topic == QUESTION_TOPIC:
        data = json.loads(msg.payload.decode())
        print(f"\nQuestion: {data['question']}")
        for i,opt in enumerate(data['options'],1):
            print(f"{i}: {opt}")
        ans = input("Votre réponse (1-4): ")
        client.publish(ANSWER_TOPIC, ans)
    elif msg.topic == SCORE_TOPIC:
        scores = json.loads(msg.payload.decode())
        print("Scores mis à jour:", scores)

client = mqtt.Client(username)
client.connect(broker_ip)
client.subscribe(QUESTION_TOPIC)
client.subscribe(SCORE_TOPIC)
client.on_message = on_message

print("Connecté au Prof...")
client.loop_forever()
