from app import app
from models import Image

@app.route('/image/<int:id>')
def image(id):
    image = Image.query.get_or_404(id)
    return app.response_class(image.data, mimetype=image.encoding_format)