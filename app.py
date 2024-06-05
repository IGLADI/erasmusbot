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

# Hardcoded credentials (in a real application, use a database)
users = {"user1": "password1"}

# Dictionary to store conversations based on user
conversations = {}
@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    if "username" in session:
        username = session["username"]
        conversations[username] = []  # Clear conversation for the user
        return jsonify({"success": True}), 200
    return jsonify({"error": "Unauthorized"}), 401

@app.route("/")
def index():
    if "username" in session:
        username = session["username"]
        old_messages = conversations.get(username, [])
        return render_template("index.html", conversation_log=old_messages)
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.json.get("username")
        password = request.json.get("password")
        if username in users and users[username] == password:
            session["username"] = username
            old_messages = conversations.get(username, [])
            return jsonify({"success": True, "old_messages": old_messages}), 200
        return jsonify({"success": False}), 401
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json.get("message")
    username = session["username"]

    if username not in conversations:
        conversations[username] = []

    conversation = conversations[username]
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
    conversations[username] = conversation  # Update conversation in the dictionary

    old_messages = conversations.get(username, [])
    session["old_messages"] = old_messages

    return jsonify({"response": system_response})


@app.route("/logout")
def logout():
    # Get the username from the session
    username = session.get("username")
    # If username exists in the session, store old messages and then remove the username
    if username:
        session.pop("username")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
