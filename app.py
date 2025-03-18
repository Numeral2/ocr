import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # Import CORS
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract  # Import pytesseract for OCR
from io import BytesIO
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for the entire application

# Function to preprocess the image
def preprocess_image(image):
    image = image.convert('L')  # Convert to grayscale
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Increase contrast
    image = image.filter(ImageFilter.SHARPEN)  # Sharpen the image
    return image

# Function to extract text
def extract_text_from_image(image):
    preprocessed_image = preprocess_image(image)
    image_bytes = BytesIO()
    preprocessed_image.save(image_bytes, format='PNG')
    image_bytes = image_bytes.getvalue()
    
    # Use pytesseract to extract text
    text = pytesseract.image_to_string(preprocessed_image)
    return text

# Route to serve index.html
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Route to process image
@app.route('/process-image', methods=['POST'])
def process_image():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part'}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    if len(files) > 10:
        return jsonify({'error': 'You can upload a maximum of 10 images'}), 400
    
    extracted_text = ""
    for file in files:
        try:
            image = Image.open(file)
            extracted_text += extract_text_from_image(image) + "\n\n"
        except Exception as e:
            return jsonify({'error': f'Error processing file: {file.filename}, {str(e)}'}), 500
    
    return jsonify({'extracted_text': extracted_text})

# Route to send extracted text to Make.com
@app.route('/send-to-make', methods=['POST'])
def send_to_make():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    make_url = "https://hook.eu2.make.com/y94u5xvkf97g5nym3trgz2j2107nuu12"
    
    try:
        response = requests.post(make_url, json={'text': text})
        response.raise_for_status()
        summarized_text = response.json().get('summary', ' ')
        return jsonify({'summary': summarized_text}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to send to Make.com', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
