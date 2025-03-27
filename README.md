# AI Summarizer - BART (Facebook)

This project is a **Flask-based API** for summarizing text using the **Hugging Face Transformers** library with the **BART model**. The API processes input text and generates a summarized version using advanced natural language processing (NLP) techniques. The API allows you to choose between **creative** and **reliable** modes for generating summaries.

## Features

- **Text Summarization**: Summarize long text into shorter, concise versions.
- **Rate Limiting**: The API is rate-limited to **10 requests per minute** per IP.
- **MongoDB Integration**: Saves input text, summary, title, and error information in **MongoDB**.
- **CORS Support**: Allows cross-origin requests from allowed origins.
- **Logging**: All requests and errors are logged for monitoring.

## Requirements

- **Python 3.7+**
- **MongoDB** (either local or cloud such as MongoDB Atlas)
- **Hugging Face Transformers library**
- **Flask**
- **Flask-Limiter** for rate limiting

Optional: A **GPU** for faster processing (but **CPU** can be used for smaller texts).

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ai-summarizer.git
cd ai-summarizer
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up MongoDB
Ensure you have a MongoDB instance running locally or on MongoDB Atlas. You will need the URI for connecting to MongoDB.

```bash
pip install -r requirements.txt
```

### 5. Configuration
Create a config.py file with the following content:

```bash
DEBUG = True
CORS_ALLOWED_ORIGINS = ["*"]  # Or specify allowed domains like ["http://example.com"]
MONGO_DBNAME = "summarizer_db"  # Your MongoDB database name
MONGO_DBURI = "mongodb://localhost:27017/summarizer_db"  # Your MongoDB URI
FLASK_PORT = 5000  # Port to run the Flask app on
```

### 6. Run the application

```bash
python app.py
```

---

## API Endpoints

### POST /api/nlp/summarize


### Payload

```bash
{
  "text": "Your text to summarize...",
  "length": "medium",   // Options: "short", "medium", "long"
  "mode": "creative"    // Options: "reliable", "creative"
}
```

- **`text`**: The text you want to summarize.
- **`length`**: Length of the summary. Options are:
  - `"short"`: Very brief summary (15-30 words).
  - `"medium"`: Standard summary (50-100 words).
  - `"long"`: Extended summary (100-180 words).
- **`mode`**: Choose between `reliable` for standard, fast summaries or `creative` for more varied results.

### Rate Limiting

The API is rate-limited to **10 requests per minute** per IP. If the limit is exceeded, you will receive a `429 Too Many Requests` error.

## NOTE
As the BART model has a token limit of **1024** tokens, if the input text exceeds this limit, the summarization process will take longer. This is because we perform chunking (splitting the text into smaller parts) and then re-summarize the combined chunks to produce the final summary.

---

## License

MIT License

## Contributors

- [Gaurav Bhalerao](https://github.com/gaurav-bhalerao-107)

Feel free to open an issue or submit a pull request if you have suggestions or improvements!
