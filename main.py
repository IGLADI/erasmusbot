# this is just the hellow world as test

import json
from openai import AzureOpenAI

with open("ChatSetup.json", "r") as file:
    chat_setup = json.load(file)

client = AzureOpenAI(azure_endpoint="https://ehb-france-central.openai.azure.com/", api_key=chat_setup["api_key"], api_version="2024-02-01")

conversation = [{"role": "system", "content": chat_setup["systemPrompt"]}]

while True:
    user_message = input("You: ")
    conversation.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=chat_setup["chatParameters"]["chatParameters"], messages=conversation)

    system_response = response.choices[0].message.content
    print("Systeem:", system_response)

    conversation.append({"role": "assistant", "content": system_response})
