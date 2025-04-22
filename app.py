from flask import Flask, request, send_file, render_template, jsonify
from PIL import Image, ImageFilter
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def process_image(file, grayscale=True, resize_dims=None, blur_radius=None):
    try:
        img = Image.open(file)

        if grayscale:
            img = img.convert('L')

        if resize_dims:
            img = img.resize(resize_dims)

        if blur_radius:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    except Exception as e:
        raise RuntimeError(f"Processing error: {e}")

@app.route('/grayscale', methods=['POST'])
def grayscale_route():
    if 'images' not in request.files:
        return jsonify({"error": "No image uploaded."}), 400

    image = request.files['images']
    if image.filename == '':
        return jsonify({"error": "Empty filename."}), 400

    try:
        grayscale = request.form.get('grayscale', 'true') == 'true'
        resize = request.form.get('resize', 'false') == 'true'
        resize_dims = None

        if resize:
            try:
                width = int(request.form.get('width'))
                height = int(request.form.get('height'))
                resize_dims = (width, height)
            except Exception:
                return jsonify({"error": "Invalid resize dimensions."}), 400

        blur = request.form.get('blur', 'false') == 'true'
        blur_radius = None
        if blur:
            try:
                blur_radius = float(request.form.get('blur_radius', '0'))
            except Exception:
                return jsonify({"error": "Invalid blur radius."}), 400

        processed_img = process_image(image, grayscale, resize_dims, blur_radius)
        return send_file(processed_img, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
