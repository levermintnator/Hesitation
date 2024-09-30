from flask import Flask, request, jsonify, render_template, Response
import google.generativeai as genai
import os
import json
from flask import stream_with_context

app = Flask(__name__)

# Cấu hình API key
api_key = os.getenv('API_KEY')
if not api_key:
    raise ValueError("API_KEY environment variable is not set")
genai.configure(api_key=api_key)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_content():
    data = request.get_json()

    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing prompt"}), 400

    prompt = data['prompt']

    def generate():
        buffer = ""

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt, stream=True, safety_settings={
                'HATE': 'BLOCK_NONE',
                'HARASSMENT': 'BLOCK_NONE',
                'SEXUAL': 'BLOCK_NONE',
                'DANGEROUS': 'BLOCK_NONE'
            })

            for chunk in response:
                if chunk.text:
                    for char in chunk.text:
                        buffer += char
                        if len(buffer) >= 1:
                            yield f"data: {json.dumps({'chunk': buffer})}\n\n"
                            buffer = ""

            if buffer:
                yield f"data: {json.dumps({'chunk': buffer})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)