from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage

from sentence_transformers import SentenceTransformer
import pandas as pd
import faiss
import numpy as np
import requests
import ollama
import json
from test_neo4j import save_conversation, find_closest_greeting, get_greeting_reply, get_chat_history
from history_chat import ollama_history_chat
def check_sentent(msg):
    distances, ann = find_closest_greeting(msg)
    print(distances)
    if distances <= 3:
        Sentence = ann
        category = get_greeting_reply(ann)
        print(Sentence, category)
    else:
        category = msg
        Sentence = msg
    results = [Sentence, category]        
    return results

def feed_url(url):

    # Send the GET request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        result = []
        for record in data:
            # Extract fields for each record
            title = record.get('title')
            price = record.get('price')
            href = record.get('link')
            promotion = record.get('promotion')
            img = record.get('img')
            result.append([title, price, href, promotion, img])
            # Append the new record to the data (list)
        
    return result



def get_ollama_response(prompt):
    
    # Combine prompt with chat history
    #history = "\n".join(history_chat)  # Join the history into a single string
    full_prompt = f"User: {prompt}\nBot: "  # Format the prompt


    try:
        response = ollama.chat(model='llama3.2:latest', messages=[
        {
            'role': 'user',
            'content': f'Briefly describe the details of the promotion in no more than 30 words to make it interesting and worth buying. Explained in Thai :"{full_prompt}" ',
            # Expand the following into shortest sentence and only 5 words quickly time
            # Briefly explain the details of the promotion in no more than 30 words to make it interesting and worth buying.
            # Take the details of the promotion and explain it further to make it interesting and worth buying.
            # Briefly describe the details of the promotion in no more than 30 words to make it interesting and worth buying. Explained in Thai
        },
        ])
        return response['message']['content']
    except:
        return f"Error:"

def encode_all_to_upper_ascii(text):
    result = ""
    
    for char in text:
        # เข้าถึงค่า ASCII ของตัวอักษรแต่ละตัว
        ascii_val = ord(char)
        
        # แปลงค่า ASCII ให้หมุนอยู่ในช่วงตัวอักษรพิมพ์ใหญ่ (A-Z, ASCII 65-90)
        new_ascii = 65 + (ascii_val % 26)
        result += chr(new_ascii)
    
    return result

stage1 = 0
web_scrap_p1 = {}
def return_message(line_bot_api,tk,user_id,msg):
    print(user_id)
    global web_scrap_p1
    user_id1 = user_id
    user_id = encode_all_to_upper_ascii(user_id[:5])
    chk_msg = check_sentent(msg)
    reply = ''

    if (chk_msg[0] != chk_msg[1]):
        if 'สวัสดี' in chk_msg[0]:
            menu_options = [
            {"label": "สอบถาม", "text": "สอบถาม"},
        ]
            # Create an array of QuickReplyButtons dynamically from the menu options
            quick_reply_items = [
                QuickReplyButton(
                    action=MessageAction(label=option["label"], text=option["text"])
                ) for option in menu_options
            ]        
            # Create a QuickReply object
            quick_reply_buttons = QuickReply(items=quick_reply_items)
            reply = chk_msg[1]
            line_bot_api.reply_message(tk,TextSendMessage(text=reply,quick_reply=quick_reply_buttons))
        else:
            line_bot_api.reply_message(tk,TextSendMessage(text=chk_msg[1]))
            reply = chk_msg[1]

    elif (chk_msg[0] == 'สอบถาม'):
        menu_options = [
            {"label": "มือถือ", "text": "phones"},
            {"label": "แท็บเล็ต", "text": "tablets"},
        ]
        # Create an array of QuickReplyButtons dynamically from the menu options
        quick_reply_items = [
            QuickReplyButton(
                action=MessageAction(label=option["label"], text=option["text"])
            ) for option in menu_options
        ]        
        # Create a QuickReply object
        quick_reply_buttons = QuickReply(items=quick_reply_items)
        reply = 'ต้องการดูมือถือหรือแพ็กเกจมือถือครับ/ค่ะ'
        line_bot_api.reply_message(tk,TextSendMessage(text=reply,quick_reply=quick_reply_buttons))

    elif (msg in ['phones', 'tablets']):
        menu_options = [
            {"label": "Apple", "text": "Apple"},
            {"label": "OPPO", "text": "OPPO"},
            {"label": "vivo", "text": "vivo"},
            {"label": "Xiaomi", "text": "Xiaomi"},
            {"label": "Samsung", "text": "Samsung"},
        ]
        # Create an array of QuickReplyButtons dynamically from the menu options
        quick_reply_items = [
            QuickReplyButton(
                action=MessageAction(label=option["label"], text=msg+'/'+option["text"])
            ) for option in menu_options
        ]        
        # Create a QuickReply object
        quick_reply_buttons = QuickReply(items=quick_reply_items)
        reply = 'ต้องการดูยี่ห้ออะไรครับ/ค่ะ'
        line_bot_api.reply_message(tk,TextSendMessage(text=reply,quick_reply=quick_reply_buttons))

    elif len(msg.split('/')) == 2:
        # (msg.split('/')[1] in ['Apple', 'OPPO', 'vivo', 'Xiaomi', 'Samsung'])
        url="http://localhost:7777/api?msg="+msg
        my_result = feed_url(url)
        for phone in my_result:
            phone[1] = int(phone[1].replace("ราคาเริ่มต้น", "").replace(" บาท", "").replace(",", ""))
        sorted_phones = sorted(my_result, key=lambda x: x[1], reverse=True)
        # menu_options = []

        # for row in my_result:
        #     menu_options.append({"label": row[0][:20], "text": row[0]})
        #     web_scrap_p1[row[0]] = row[2]

        # # Create an array of QuickReplyButtons dynamically from the menu options
        # quick_reply_items = [
        #     QuickReplyButton(
        #         action=MessageAction(label=option["label"], text=option["text"])
        #     ) for option in menu_options
        # ]        
        # # Create a QuickReply object
        # quick_reply_buttons = QuickReply(items=quick_reply_items)
        # #line_bot_api.reply_message(tk, [TextSendMessage(quick_reply=quick_reply)])
        # reply = 'ต้องการดูรายละเอียดเครื่องไหนครับ/ค่ะ'
        # line_bot_api.reply_message(tk,TextSendMessage(text=reply,quick_reply=quick_reply_buttons))

        # ข้อมูลสินค้า
        
        # สร้าง Flex Message ที่มีรูปภาพและปุ่มเลือกพร้อมช่องว่างระหว่างปุ่ม

        flex_message = {
            "type": "carousel",
            "contents": []
        }

        for row in my_result[:5]:
            web_scrap_p1[row[0]] = row[2]
            bubble = {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": row[4],
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": row[0],
                            "weight": "bold",
                            "size": "xl"
                        },
                        {
                            "type": "text",
                            "text": 'ราคาเริ่มต้น '+ "{:,}".format(row[1]) + ' บาท',
                            "size": "sm",
                            "color": "#999999"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",  # กำหนดระยะห่างระหว่างปุ่ม
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "ดูสินค้า",
                                "uri": "https://www.ais.th/consumers/store/phones/apple/iphone-16"
                            },
                            "style": "primary",  # ปุ่มสีเขียว
                            "color": "#00b900"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "message",
                                "label": "โปรโมชั่น",
                                "text":  row[0]
                            },
                            "style": "primary",  # ปุ่มสีเขียว
                            "color": "#00b900",
                            "margin": "md"  # เพิ่มช่องว่างระหว่างปุ่ม
                        }
                    ]
                }
            }

            # เพิ่มการ์ดแต่ละอันใน carousel
            flex_message["contents"].append(bubble)

        # Convert เป็น JSON สำหรับส่งผ่าน LINE API
        flex_message_json = json.dumps(flex_message, ensure_ascii=False, indent=4)

        # สร้าง Flex Message object
        flex_message_obj = FlexSendMessage(
            alt_text='iPhone 16 - ข้อมูลสินค้า', 
            contents=flex_message
        )

        # ส่งข้อความไปยังผู้ใช้ (แทนที่ 'USER_ID' ด้วย ID ของผู้ใช้หรือกลุ่ม)
        line_bot_api.reply_message(tk, flex_message_obj)

    else:
        try:
            if web_scrap_p1[msg] :
                url="http://localhost:7777/api?msg="+web_scrap_p1[msg]
                my_result = feed_url(url)
                menu_options = []

                for row in my_result:
                    ollama_convert = get_ollama_response(row[3])
                    # menu_options.append({"label": row[3][:20], "text": ollama_convert})
                    menu_options.append(TextSendMessage(text=ollama_convert))

                # # Create an array of QuickReplyButtons dynamically from the menu options
                # quick_reply_items = [
                #     QuickReplyButton(
                #         action=MessageAction(label=option["label"], text=option["text"])
                #     ) for option in menu_options
                # ]        
                # # Create a QuickReply object
                # quick_reply_buttons = QuickReply(items=quick_reply_items)
                # #line_bot_api.reply_message(tk, [TextSendMessage(quick_reply=quick_reply)])
                reply = menu_options
                line_bot_api.push_message(user_id1, reply)

        except Exception as e:
            # Handle any other exception
            print(f"An error occurred: {e}")
            database = get_chat_history(user_id)
            reply = ollama_history_chat(msg, database)
            line_bot_api.reply_message(tk,TextSendMessage(text=reply))

    save_conversation(user_id, msg, reply)


app = Flask(__name__)

@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)                    
    try:
        json_data = json.loads(body)                         
        access_token = 'mK4QMUQ4TK2AOqmOtcvY0Tlj4f5UbcefwC+hTz4sKK7EKX7shhkhg83RMlb0710HzwWSADi4weaJr8WZpVR3gexbme11v6D/3UtIuX/WVfoftSqLMdoBvOJdJ497fDIykphdId/JmH3IhW7l/NBljQdB04t89/1O/w1cDnyilFU='
        secret = 'f224b3f3184f4c63f7c16747828b6ac7'
        line_bot_api = LineBotApi(access_token)              
        handler = WebhookHandler(secret)                     
        signature = request.headers['X-Line-Signature']      
        handler.handle(body, signature)                      
        msg = json_data['events'][0]['message']['text']      
        user_id = json_data['events'][0]['source']['userId']      
        tk = json_data['events'][0]['replyToken']            
        return_message(line_bot_api,tk,user_id,msg)
        print(msg, tk)                                      
    except:
        print(body)                                          
    return 'OK'                 
if __name__ == '__main__':
    app.run(port=5000)
