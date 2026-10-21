import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
# Support comma-separated pool of multiple Gemini API keys for seamless quota failover
raw_keys = os.getenv('GEMINI_API_KEYS', '')
GEMINI_API_KEYS = [k.strip() for k in raw_keys.split(',') if k.strip()]
if GEMINI_API_KEY and GEMINI_API_KEY not in GEMINI_API_KEYS:
    GEMINI_API_KEYS.insert(0, GEMINI_API_KEY)

TINYFISH_API_KEY = os.getenv('TINYFISH_API_KEY', 'sk-tinyfish-izjo87yS42UZbOzdqMc4IHjievGNTGwG')
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', '0.0.0.0')
