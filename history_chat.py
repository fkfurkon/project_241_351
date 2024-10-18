import requests
from test_neo4j import get_chat_history, save_conversation

# ส่งข้อความไปยัง Ollama API พร้อมข้อมูลจาก Knowledge Graph
def ollama_history_chat(prompt, database):
    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json",
    }

    # รวมประวัติการสนทนาใน Knowledge Graph กับข้อความใหม่
    # print('database: ', database)
    full_prompt = f"database: {database}\nUser: {prompt}\ndeveloper: Answer users' questions based on information from the database where you talk to them. If it's not in the database, you can answer in a general way. and answer in short Thai to get the point, no more than 40 words."
    # I'm a software developer and want you to chat with users. I prepared a database where you have talked to users and you might want to use it.
    # I'm a software developer and want you to talk to users. I prepared a database where you have discussed with users and you may want to use it. You need to make the conversation with your users natural. and shortened
    # I'm a software developer and need your help in answering user questions in a natural way. Without saying that the data was taken from the database. The answer may be in the database. It consists of messages users asked about and messages you responded to.
    # I'm a developer and would like your help in answering users' questions appropriately. The answer may be in the database. that consists of Messages that users have asked about and messages that you have responded to
    # Take the database and analyze it and answer the questions correctly. The responses in the database may not be completely accurate, so check carefully. If there is no information in the database, answer in ge.neral and answer directly to the question.
    # Take the database and analyze it and answer the questions correctly. If there is no information in the database, answer in general and answer directly to the question.
    # Answer questions appropriately. Based on information from the database first If there is none, please give a general answer.
    # Answer questions appropriately. Based on information from the database first. If not, please provide a general answer. The database will consist of previous chats or chats that have been discussed before and will be kept continuously.
    # Take the database and process it and answer questions appropriately.
    # Answer the questions briefly. Database based If there is no answer, answer the question as appropriate.
    # Answer user questions based on the database. If not, answer general questions. When answering a question, give a brief explanation to get the point across. Unless the user wants a long answer.
    # Answer user questions based on the database. If not, answer general questions.
    # Answering questions should be based on information from the database provided. If it's not in the database, just answer the question.
    # Take the previous message and process it to answer the question in line with the user's question.
    # Answers to questions are based on information from the user's database. which the user's information is Messages that the user tells, asks, etc. If they are not in the user's database, just give a general answer.
    # Previous chats
    # Answer questions based on the user's database and the bot's database. If the information is not available in either database, simply answer the questions using general knowledge.
    # Answers to questions are based on information from the user's database. If it isn't in the user's database, just answer the question.
    # Answers to questions are based on information from the user's database. which the user's information is Messages that users have told, asked, etc. If they are not in the user's database, just answer them.
    payload = {
        "model": "llama3.2",
        "prompt": full_prompt,
        "stream": False,
        "persona": "I'm a friendly and fun chatbot. I love making people smile! 😊"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("response", "No response from the model.")
    except requests.RequestException as e:
        return f"Error: {e}"

# # ฟังก์ชันสนทนา
# def chat():
#     print("Welcome to the Ollama chatbot! Type 'bye' to exit.")

#     user_name = "3"  # สมมุติว่าผู้ใช้ชื่อเจสัน

#     while True:
#         user_input = input("You: ")

#         if user_input.lower() in ['bye', 'exit']:
#             print("Bot: Goodbye! Have a great day!")
#             break

#         # ดึงประวัติการสนทนาจาก Knowledge Graph
#         graph_data = get_chat_history(user_name)

#         # เรียกใช้ Ollama API เพื่อรับคำตอบ
#         bot_response = get_ollama_response(user_input, graph_data)
#         print(f"Bot: {bot_response}")

#         # บันทึกข้อมูลใน Knowledge Graph
#         save_conversation(user_name, user_input, bot_response)

# if __name__ == "__main__":
#     chat()
