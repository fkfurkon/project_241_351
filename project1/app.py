import requests
import json
from neo4j import GraphDatabase
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from sentence_transformers import SentenceTransformer, util,InputExample
from sentence_transformers import models, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
import numpy as np
import faiss

# LLaMA 3 API Endpoint
LLAMA_API_URL = "http://localhost:11434/api/generate"  # Change to your LLaMA 3 API URL

# Headers for the LLaMA API request
LLAMA_HEADERS = {
    "Content-Type": "application/json"
}

def generate_text(prompt: str, model: str = "supachai/llama-3-typhoon-v1.5"):
    # Payload for the LLaMA API request
    llama_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    # Send POST request to the LLaMA API
    response = requests.post(LLAMA_API_URL, headers=LLAMA_HEADERS, data=json.dumps(llama_payload))

    # Print status code and response text for debugging
    data_dict = json.loads(response.text)

    # Check if the request was successful
    if response.status_code == 200:
        return data_dict['response']
    else:
        print("Error:", response.status_code, response.text)
        return None

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j://localhost"
AUTH = ("neo4j", "6510110332")


with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
#model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')
import json
cypher_query = '''
MATCH (n:Question) RETURN n.question as name, n.answer as reply;
'''
greeting_corpus = []
greeting_responses = {}
with driver.session() as session:
    results = session.run(cypher_query)
    for record in results:
        greeting_corpus.append(record['name'])
        greeting_responses[record['name']] = record['reply']
    #greeting_corpus = ["สวัสดีครับ","ดีจ้า"]
    greeting_vec = model.encode(greeting_corpus, convert_to_tensor=True,normalize_embeddings=True)    

# Function to build FAISS index with normalized embeddings
def build_faiss_index(corpus):
    corpus_vectors = model.encode(corpus, normalize_embeddings=True)
    
    # Dimension of the embeddings
    vector_dimension = corpus_vectors.shape[1]
    
    # Initialize FAISS index
    index = faiss.IndexFlatL2(vector_dimension)
    
    # Normalize the vectors for cosine similarity approximation
    faiss.normalize_L2(corpus_vectors)
    
    # Add corpus vectors to the FAISS index
    index.add(corpus_vectors)
    
    return index, corpus_vectors

# Modified compute_similar using FAISS
def compute_similar(faiss_index, corpus_vectors, sentence):
    sentence_vector = model.encode([sentence], normalize_embeddings=True)
    
    # Normalize sentence vector
    faiss.normalize_L2(sentence_vector)
    
    # Search FAISS index for top-k nearest neighbors
    k = faiss_index.ntotal  # Search for all corpus entries
    distances, ann = faiss_index.search(np.array(sentence_vector), k)
    
    # Return the indices of the nearest neighbors and their distances
    return distances[0], ann[0]

greeting_faiss_index, greeting_vectors = build_faiss_index(greeting_corpus)
# Modified compute_response using FAISS
def compute_response(sentence):
    sentence_vector = model.encode([sentence], normalize_embeddings=True)
    
    # Normalize sentence vector
    faiss.normalize_L2(sentence_vector)
    
    # Search FAISS index for the best match
    k = 1  # We just want the best match
    distances, ann = greeting_faiss_index.search(np.array(sentence_vector), k)
    
    best_match_idx = ann[0][0]
    
    # Check if the similarity is high enough
    if distances[0][0] < 0.5:  # Adjust threshold as needed
        best_match = greeting_corpus[best_match_idx]
        return 'neo4j : '+greeting_responses.get(best_match, "Sorry, I don't understand.")
    else:
        result = generate_text(sentence+' ขอคำตอบสั้นๆ ไม่เกิน 50 คำ')
        return "ollama : "+result
    
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
        tk = json_data['events'][0]['replyToken']            
        response_msg = compute_response(msg)
        line_bot_api.reply_message( tk, TextSendMessage(text=response_msg) )
        print(msg, tk)                                      
    except:
        print(body)                                          
    return 'OK'                
if __name__ == '__main__':
    #For Debug
    compute_response("ดีจ๋า")
    app.run(port=5000)