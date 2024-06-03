from flask import Flask, request, render_template, jsonify
import json
from openai import AzureOpenAI 

app = Flask(__name__)

with open("ChatSetup.json", "r") as file:
    chat_setup = json.load(file)

client = AzureOpenAI(azure_endpoint="https://ehb-france-central.openai.azure.com/", api_key=chat_setup["api_key"], api_version="2024-02-01")

conversation = [{"role": "system", "content": chat_setup["systemPrompt"]}]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    global conversation
    user_message = request.json.get("message")
    conversation.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=chat_setup["chatParameters"]["chatParameters"], messages=conversation)

    system_response = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": system_response})

    return jsonify({"response": system_response})


if __name__ == "__main__":
    app.run(debug=True)
