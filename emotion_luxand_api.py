from flask import Flask, request, jsonify
import requests
import json
import base64
from io import BytesIO
from PIL import Image

API_TOKEN = "3760ad39c6fd49c2bd4742a60aa8e884"

app = Flask(__name__)

@app.route('/predict_emotion', methods=['POST'])
def predict_emotion():
    try:
        # Get base64 image from request
        img_data = request.json['image']
        img_data = img_data.split(',')[1]  # Remove "data:image/jpeg;base64,"
        img_bytes = base64.b64decode(img_data)
        img = BytesIO(img_bytes)

        url = "https://api.luxand.cloud/photo/emotions"
        headers = {"token": API_TOKEN}
        files = {"photo": img}

        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": response.text}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 