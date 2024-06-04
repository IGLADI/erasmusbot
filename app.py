from flask import Flask, request, render_template, jsonify, session, redirect, url_for
import json
from openai import AzureOpenAI

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

with open("ChatSetup.json", "r") as file:
    chat_setup = json.load(file)

search_endpoint = "https://ehb-search.search.windows.net"
search_key = chat_setup["searchKey"]
search_index_name = "ehb"

client = AzureOpenAI(
    azure_endpoint="https://ehb-france-central.openai.azure.com/",
    api_key=chat_setup["api_key"],
    api_version="2024-02-01",
)

conversation = []

# Hardcoded credentials (in a real application, use a database)
users = {"user1": "password1", "user2": "password2"}


@app.route("/")
def index():
    if "username" in session:
        return render_template("index.html")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.json.get("username")
        password = request.json.get("password")
        if username in users and users[username] == password:
            session["username"] = username
            return jsonify({"success": True}), 200
        return jsonify({"success": False}), 401
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.json.get("username")
    password = request.json.get("password")
    if username in users:
        return jsonify({"success": False, "message": "User already exists"}), 409
    users[username] = password
    return jsonify({"success": True}), 201


@app.route("/chat", methods=["POST"])
def chat():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    global conversation
    user_message = request.json.get("message")
    conversation.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=chat_setup["chatParameters"]["chatParameters"],
        messages=conversation,
        extra_body={
            "data_sources": [
                {
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": search_endpoint,
                        "index_name": search_index_name,
                        "semantic_configuration": "default",
                        "query_type": "simple",
                        "fields_mapping": {},
                        "role_information": chat_setup["systemPrompt"],
                        "strictness": 3,
                        "top_n_documents": 5,
                        "authentication": {"type": "api_key", "key": search_key},
                        "key": search_key,
                    },
                }
            ],
        },
    )

    system_response = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": system_response})

    return jsonify({"response": system_response})


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
