from celery import Celery
from PIL import Image, ImageFilter
from io import BytesIO
import os

app = Celery(
    'tasks',
    broker=os.environ.get('CELERY_BROKER_URL'),
    backend=os.environ.get('CELERY_RESULT_BACKEND')
)

@app.task
def process_image(file_data, options):
    img = Image.open(BytesIO(file_data))

    if options.get('grayscale'):
        img = img.convert('L')

    if options.get('resize'):
        width = options.get('width')
        height = options.get('height')
        img = img.resize((width, height))

    if options.get('blur'):
        radius = options.get('blur_radius', 1.0)
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))

    output = BytesIO()
    img.save(output, format='PNG')
    return output.getvalue()
