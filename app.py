import os
from flask import Flask, request, jsonify
from config import config
from flask_cors import CORS
from transformers import pipeline, AutoTokenizer
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mongoengine import Document, StringField, DateTimeField, BooleanField
from bson.objectid import ObjectId
from flask.json.provider import DefaultJSONProvider
import logging

# --- Setup logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask app setup ---
app = Flask(__name__)

# --- Custom JSON Encoder ---
class JSONEncoder(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%SZ')
        return DefaultJSONProvider.default(self, o)

app.json = JSONEncoder(app)

# --- Load configuration from config.py ---
app.config['DEBUG'] = config.DEBUG
app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', None)
app.config['MONGO_URI'] = os.getenv('MONGO_DBURI', None)

# --- CORS setup ---
CORS(app, supports_credentials=True, origins=config.CORS_ALLOWED_ORIGINS)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Required for cross-origin cookies
app.config['SESSION_COOKIE_SECURE'] = True      # Required for HTTPS

# --- Rate Limiting ---
limiter = Limiter(get_remote_address, app=app)

# --- MongoDB Model ---
from mongoengine import connect
connect(app.config['MONGO_DBNAME'], host=app.config['MONGO_URI'])

class SummaryRecord(Document):
    text = StringField(required=True)
    summary = StringField(required=True)
    title = StringField(required=True)
    createdAt = DateTimeField(default=datetime.utcnow)
    success = BooleanField(default=True)
    error = StringField(default="")

# --- Load Model ---
MODEL_NAME = "facebook/bart-large-cnn"
summarizer = pipeline("summarization", model=MODEL_NAME, device=-1)  # Use CPU
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

MAX_TOKENS = 1024

# --- Helper: Split text into chunks ---
def chunk_text(text, max_words=700, overlap=100):
    words = text.split()
    for i in range(0, len(words), max_words - overlap):
        yield " ".join(words[i:i + max_words])

# --- Helper: Re-summarize combined chunks for more diversity ---
def summarize_combined_chunks(chunks, preset_max, preset_min, mode):
    combined_summary = " ".join(chunks)
    summary = summarizer(
        combined_summary,
        max_length=preset_max,
        min_length=preset_min,
        num_beams=5,
        do_sample=True if mode == "creative" else False,
        temperature=1.2,
        top_k=100,
        top_p=0.95
    )[0]["summary_text"]
    return summary

# --- Summarize Route ---
@app.route("/summarize", methods=["POST"])
@limiter.limit("10 per minute")
def summarize():
    data = request.json
    text = data.get("text", "")
    length = data.get("length", "medium")
    mode = data.get("mode", "reliable")
    
    logger.info("Summarization request initiated.")

    # Input validation
    if not text:
        logger.error("No input text provided.")
        return jsonify({"ok": False, "error": "Input text is required."}), 400

    # Warning for very short inputs
    if len(text.split()) < 10:
        logger.warning("Short input received. The summary might not be accurate.")

    try:
        # Set summary length limits based on user input
        preset_min, preset_max = {
            "short": (15, 30),
            "medium": (50, 100),
            "long": (100, 180)
        }.get(length, (50, 100))

        # Tokenize the text to count tokens
        input_tokens = len(tokenizer.encode(text, truncation=False))
        logger.info(f"Received text with {input_tokens} tokens.")

        # If the input text exceeds the model's token limit, chunk it
        if input_tokens > MAX_TOKENS:
            logger.warning(f"Input exceeds {MAX_TOKENS} tokens. Chunking the text.")
            chunks = list(chunk_text(text))  # Split the text into chunks

            # First summarize chunks reliably (faster)
            partials = [summarizer(chunk, max_length=preset_max, min_length=preset_min, do_sample=False)[0]["summary_text"] for chunk in chunks]
            
            # Re-summarize the combined chunks for more varied output (creative)
            summary = summarize_combined_chunks(partials, preset_max, preset_min, mode)
        else:
            # Otherwise, summarize the whole text with more creative settings for mode="creative"
            summary = summarizer(
                text,
                max_length=preset_max,
                min_length=preset_min,
                num_beams=5,  # Increased beams to get better diversity
                do_sample=True if mode == "creative" else False,
                temperature=1.2,  # Increase temperature for more creativity
                top_k=50,  # More diversity in the next token choices
                top_p=0.9  # Ensure more varied outputs (nucleus sampling)
            )[0]["summary_text"]

        # Generate a title (first 12 words of summary)
        title = " ".join(summary.split()[:12])
        if not title:
            title = "Untitled Summary"
        if not title.endswith('.'):
            title += "..."

        # Save to MongoDB
        summary_record = SummaryRecord(
            text=text,
            summary=summary,
            title=title,
            createdAt=datetime.utcnow(),
            success=True
        )
        summary_record.save()

        # Log success
        logger.info(f"Summary generated successfully for text of length {len(text)}.")

        # Return the summary and title
        return jsonify({
            "title": title,
            "summary": summary,
            "original_length": len(text.split()),
            "summary_length": len(summary.split()),
            "token_count": input_tokens
        })

    except IndexError as e:
        logger.error(f"IndexError: {e}")
        return jsonify({"error": "Index error during summarization."}), 500

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        logger.info("Summarization request completed.")


# --- Run the Flask app ---
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=config.DEBUG)
