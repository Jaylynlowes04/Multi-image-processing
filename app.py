from flask import Flask, request, send_file, jsonify, render_template
from celery import Celery
from io import BytesIO
import zipfile
import os
from tasks import process_image 

app = Flask(__name__)

# Celery Config 
celery = Celery(
    'tasks',
    broker=os.environ.get('CELERY_BROKER_URL'),
    backend=os.environ.get('CELERY_RESULT_BACKEND')
)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/process')
def process():
    return render_template('index.html')

@app.route('/grayscale', methods=['POST'])
def grayscale_batch():
    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No images uploaded'}), 400

    tasks = []
    for file in files:
        file_bytes = file.read()
        options = {
            'grayscale': request.form.get(f'grayscale-{file.filename}') == 'true',
            'resize': request.form.get(f'resize-{file.filename}') == 'true',
            'blur': request.form.get(f'blur-{file.filename}') == 'true',
            'width': int(request.form.get(f'width-{file.filename}', 0)),
            'height': int(request.form.get(f'height-{file.filename}', 0)),
            'blur_radius': float(request.form.get(f'blur-radius-{file.filename}', 1.0))
        }
        task = process_image.delay(file_bytes, options)
        tasks.append((file.filename, task))

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename, task in tasks:
            result = task.get(timeout=30)
            zip_file.writestr(f"processed_{filename}", result)

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='processed_images.zip')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
