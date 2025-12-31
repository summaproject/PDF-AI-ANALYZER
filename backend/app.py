# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv
import os

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# -------------------------
# Configure Gemini
# -------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

# Store extracted text in memory
extracted_text_store = {}

# -------------------------
# Upload route
# -------------------------
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    extracted_text = ""

    if file.filename.lower().endswith(".pdf"):
        # Extract text from PDF
        with pdfplumber.open(filepath) as pdf:
            extracted_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        # Assume image -> use Gemini for OCR
        img = genai.upload_file(filepath)
        result = model.generate_content(["Extract text from this image.", img])
        extracted_text = result.text

    # store (in memory) for later Q&A
    extracted_text_store["text"] = extracted_text

    # return only a preview to the frontend to avoid huge payloads
    return jsonify({
        "message": "File uploaded & text extracted successfully!",
        "text_preview": extracted_text[:10000]
    })

# -------------------------
# Ask question route
# -------------------------
@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json or {}
    question = data.get("question", "").strip()
    language = data.get("language", "").strip()
    context_text = extracted_text_store.get("text", "")

    if not context_text:
        return jsonify({"answer": "No file uploaded yet."}), 400

    # Primary prompt: ask Gemini to answer based on context
    prompt = f"""
The following text was extracted from a file:

{context_text}

User question: {question}

Answer appropriately, using only the context above where possible. Be concise.
"""

    # If user selected a language, ask the model to translate the final answer
    if language:
        prompt += f"\n\nFinally, translate the final answer into {language}."

    response = model.generate_content(prompt)

    return jsonify({"answer": response.text})

# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
