from flask import Flask, request, render_template, jsonify
import json
from openai import AzureOpenAI

app = Flask(__name__)

with open("ChatSetup.json", "r") as file:
    chat_setup = json.load(file)

search_endpoint = "https://ehb-search.search.windows.net"
search_key = chat_setup["searchKey"]
search_index_name = "ehb"

client = AzureOpenAI(azure_endpoint="https://ehb-france-central.openai.azure.com/", api_key=chat_setup["api_key"], api_version="2024-02-01")

conversation = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
