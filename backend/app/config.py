import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
TINYFISH_API_KEY = os.getenv('TINYFISH_API_KEY', 'sk-tinyfish-izjo87yS42UZbOzdqMc4IHjievGNTGwG')
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', '0.0.0.0')
