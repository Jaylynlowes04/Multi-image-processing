#Add blurring and connect to website
#Think of something else to add.

from flask import Flask, request, send_file, jsonify, render_template
from PIL import Image, ImageFilter
from io import BytesIO
import concurrent.futures
import zipfile

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Main processing logic: grayscale, resize, blur
def process_image(file, resize_dims=None, blur_radius=None):
    try:
        img = Image.open(file).convert('L')  # Grayscale

        if resize_dims:
            img = img.resize(resize_dims)

        if blur_radius:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return file.filename, buffer.read()
    except Exception as e:
        return file.filename, f"error: {str(e)}"

@app.route('/grayscale', methods=['POST'])
def grayscale_batch():
    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No images uploaded'}), 400

    # Resize
    resize = request.form.get('resize') == 'true'
    resize_dims = None
    if resize:
        try:
            width = int(request.form.get('width'))
            height = int(request.form.get('height'))
            resize_dims = (width, height)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid resize dimensions'}), 400

    # Blur
    blur = request.form.get('blur') == 'true'
    blur_radius = None
    if blur:
        try:
            blur_radius = float(request.form.get('blur_radius', 1.0))
        except ValueError:
            return jsonify({'error': 'Invalid blur radius'}), 400

    # Process each image
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_image, file, resize_dims, blur_radius)
            for file in files
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # Package into ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename, data in results:
            if isinstance(data, bytes):
                zip_file.writestr(f"processed_{filename}", data)
            else:
                zip_file.writestr(f"{filename}_error.txt", data)

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='processed_images.zip')

if __name__ == '__main__':
    app.run(debug=True)
