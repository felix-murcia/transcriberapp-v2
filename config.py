"""Configuration for TranscriberApp."""
import os
import random
from dotenv import load_dotenv
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

load_dotenv()

APP_VERSION = random.randint(1, 1000000)  # Para evitar cache en el frontend
AVAILABLE_MODES = [
    "default", "tecnico", "refinamiento", "ejecutivo", "bullet",
    "comparative", "product_manager", "project_manager", "quality_assurance"
]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_MODEL = os.getenv("USE_MODEL", "gemini-2.5-flash-lite")
LANGUAGE = os.getenv("LANGUAGE", "es")

GROQ_API_URL = os.getenv("GROQ_API_URL")
GROQ_MODEL_TRANSCRIBER = os.getenv("GROQ_MODEL_TRANSCRIBER")

FFMPEG_API_URL = os.getenv("FFMPEG_API_URL", "http://ffmpeg-api-prod:8080")

AVAILABLE_MODES_DICT = {
    "default": "default",
    "tecnico": "tecnico",
    "refinamiento": "refinamiento",
    "ejecutivo": "ejecutivo",
    "bullet": "bullet",
    "comparative": "comparative",
    "product_manager": "product_manager",
    "project_manager": "project_manager",
    "quality_assurance": "quality_assurance",
}

logger.info("[CONFIG] Configuración cargada correctamente")
