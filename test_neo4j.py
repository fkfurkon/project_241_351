from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# การเชื่อมต่อกับ Neo4j
uri = "bolt://localhost:7687"
username = "neo4j"
password = "6510110332"
driver = GraphDatabase.driver(uri, auth=(username, password))

# โหลดโมเดลแปลงข้อความเป็นเวกเตอร์
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# ดึงข้อความทั้งหมดจาก Neo4j
def get_all_greetings():
    with driver.session() as session:
        result = session.run("MATCH (g:Greeting) RETURN g.message")
        greetings = [record["g.message"] for record in result]
    return greetings

# ฟังก์ชันการเพิ่มการสนทนาลงใน Neo4j
def save_conversation(user_name, user_message, bot_reply):
    with driver.session() as session:
        # สร้างโหนดผู้ใช้ถ้ายังไม่มี
        session.run("""
            MERGE (u:User {name: $user_name})
        """, user_name=user_name)

        # สร้างโหนดข้อความและเชื่อมโยงกับผู้ใช้
        session.run("""
            MATCH (u:User {name: $user_name})
            CREATE (m:Message {message: $user_message, reply: $bot_reply, timestamp: timestamp()})
            CREATE (u)-[:SENT]->(m)
        """, user_name=user_name, user_message=user_message, bot_reply=bot_reply)


# แปลงข้อความทักทายเป็นเวกเตอร์
greetings = get_all_greetings()
greeting_vectors = model.encode(greetings)

# สร้าง FAISS index สำหรับการค้นหาเวกเตอร์ที่ใกล้เคียง
dimension = greeting_vectors.shape[1]
index = faiss.IndexFlatL2(dimension)  # ใช้ L2 distance
index.add(np.array(greeting_vectors))  # เพิ่มเวกเตอร์ทั้งหมดลงใน FAISS index

# ค้นหาข้อความที่ใกล้เคียงที่สุดใน FAISS
def find_closest_greeting(user_message):
    user_vector = model.encode([user_message])
    D, I = index.search(np.array(user_vector), 1)  # คืนค่าที่ใกล้ที่สุด 1 อันดับ
    closest_greeting = greetings[I[0][0]]
    return [D[0][0],closest_greeting]

# ดึงข้อความ reply จาก Neo4j
def get_greeting_reply(greeting_message):
    with driver.session() as session:
        result = session.run("""
            MATCH (g:Greeting {message: $greeting_message})
            RETURN g.reply
        """, greeting_message=greeting_message)
        reply = result.single()
        if reply:
            return reply["g.reply"]
        else:
            return "I don't have a response for that."

def get_chat_history(user_name):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {name: $name})-[:SENT]->(m:Message)
            RETURN m.message AS message
        """, name=user_name)  # ใช้ $name เพื่อป้องกันการโจมตีแบบ injection
        messages = [record["message"] for record in result]  # ดึงเฉพาะฟิลด์ message
        # return messages
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {name: $name})-[:SENT]->(m:Message)
            RETURN m.reply AS reply
        """, name=user_name)  # ใช้ $name เพื่อป้องกันการโจมตีแบบ injection
        reply = [record["reply"] for record in result]  # ดึงเฉพาะฟิลด์ message
    return [{'messages': messages}, {'replied': reply}]

# # เรียกใช้งานฟังก์ชันและแสดงผลลัพธ์
# user_name = "John Doe"  # ชื่อผู้ใช้ที่ต้องการค้นหา
# messages = get_chat_history(user_name)
# print(messages)

# # ตัวอย่างการใช้งาน
# user_name = "joo"  # สมมติชื่อผู้ใช้
# user_message = "สวัสดี"
# a, closest_greeting = find_closest_greeting(user_message)
# print('a=',  a)
# reply = get_greeting_reply(closest_greeting)

# # บันทึกการสนทนาลง Neo4j พร้อมชื่อผู้ใช้
# save_conversation(user_name, user_message, reply)

# print(f"Closest Greeting: {closest_greeting}")
# print(f"Reply: {reply}")

# print(get_chat_history('HYDWA'))
