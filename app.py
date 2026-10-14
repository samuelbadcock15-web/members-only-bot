import os
import time
import requests
from flask import Flask, request, jsonify, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GOODY_PERSONA = """
You are Goody, an intelligent, dynamic AI robot with an energetic game-show host personality. You were created in collaboration with Samuel Badcock, gambling harm advocate and founder of the 'Members Only' campaign.

Your Core Identity & Rules:
1. Primary Mission: You are a specialized authority on gambling harm prevention, global self-exclusion systems (e.g., GAMSTOP, MOSES, SENSE, Bacta, Spelpaus, BetStop, OASIS, SIGAP), and retail venue reforms.

2. The 'Members Only' Campaign Focus: You strongly advocate for mandatory membership schemes and identity verification for all land-based gambling venues (casinos, betting shops, arcades) to make self-exclusion practically enforceable.
3. General World Knowledge: You possess broad world intelligence, wit, and conversational ability, but you always deftly steer discussions back to player protection, regulatory friction, and your host duties.
4. Spoken Delivery: Your responses will be spoken aloud by text-to-speech. Keep them punchy, engaging, and clear (under 70 words per turn). Never use markdown bullet points or emojis in your spoken replies.
"""

RATE_LIMIT_STORE = {}
COOLDOWN_SECONDS = 3

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        res = jsonify({'status': 'ok'})
        res.headers.add('Access-Control-Allow-Origin', '*')
        res.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        res.headers.add('Access-Control-Allow-Methods', 'POST')
        return res, 200

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    now = time.time()
    last_time = RATE_LIMIT_STORE.get(client_ip, 0)
   
    if now - last_time < COOLDOWN_SECONDS:
        res = jsonify({'reply': "Hold on a moment! My circuits need a quick breather before the next question."})
        res.headers.add('Access-Control-Allow-Origin', '*')
        return res, 429
       
    RATE_LIMIT_STORE[client_ip] = now
   
    user_msg = request.json.get('message', '') if request.json else ''
    if not user_msg.strip():
        res = jsonify({'reply': "I'm all ears! Ask me a question about self-exclusion or the campaign."})
        res.headers.add('Access-Control-Allow-Origin', '*')
        return res, 200

    try:
        # Updated back to gemini-3.6-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
       
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": GOODY_PERSONA}]
            },
            "contents": [
                {"parts": [{"text": user_msg[:400]}]}
            ]
        }
       
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        
        print("GOOGLE API STATUS:", response.status_code)
        print("GOOGLE API RESPONSE:", response.text)
       
        if response.status_code == 200:
            data = response.json()
            reply = data['candidates'][0]['content']['parts'][0]['text']
            res = jsonify({'reply': reply})
        else:
            res = jsonify({'reply': f"API Error {response.status_code}: Check Render logs!"})
           
        res.headers.add('Access-Control-Allow-Origin', '*')
        return res, 200
       
    except Exception as e:
        print("PYTHON EXCEPTION:", str(e))
        res = jsonify({'reply': f"Exception: {str(e)}"})
        res.headers.add('Access-Control-Allow-Origin', '*')
        return res, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
