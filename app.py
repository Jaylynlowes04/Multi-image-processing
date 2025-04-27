from flask import Flask, request, send_file, jsonify, render_template
from PIL import Image, ImageFilter
from io import BytesIO
import concurrent.futures
import zipfile

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')  

@app.route('/process')
def process():
    return render_template('index.html')  

def process_single_image(file, options):
    try:
        img = Image.open(file)

        if options.get("grayscale"):
            img = img.convert('L')

        if options.get("resize"):
            width = options.get("width")
            height = options.get("height")
            if width and height:
                img = img.resize((width, height))

        if options.get("blur"):
            radius = options.get("blur_radius", 1.0)
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return file.filename, buffer.read()

    except Exception as e:
        return file.filename, f"error: {str(e)}"

# Grayscale, Resize, Blur Route
@app.route('/grayscale', methods=['POST'])
def grayscale_batch():
    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No images uploaded'}), 400

    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []

        for file in files:
            filename = file.filename

            options = {
                "grayscale": request.form.get(f"grayscale-{filename}") == 'true',
                "resize": request.form.get(f"resize-{filename}") == 'true',
                "blur": request.form.get(f"blur-{filename}") == 'true',
            }

            if options["resize"]:
                try:
                    options["width"] = int(request.form.get(f"width-{filename}", 0))
                    options["height"] = int(request.form.get(f"height-{filename}", 0))
                except (ValueError, TypeError):
                    options["width"] = None
                    options["height"] = None

            if options["blur"]:
                try:
                    options["blur_radius"] = float(request.form.get(f"blur-radius-{filename}", 1.0))
                except (ValueError, TypeError):
                    options["blur_radius"] = 1.0

            futures.append(executor.submit(process_single_image, file, options))

        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename, data in results:
            if isinstance(data, bytes):
                zip_file.writestr(f"processed_{filename}", data)
            else:
                zip_file.writestr(f"{filename}_error.txt", data)

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='processed_images.zip')

# Run App
if __name__ == '__main__':
    app.run(debug=True)
