import os
import logging
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from ImageGoNord import GoNord

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'), static_url_path='/static')

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'processed')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    processed_image_path = request.args.get('processed_image_path')
    processed_filename = request.args.get('processed_filename')
    return render_template('index.html',
                           processed_image_path=processed_image_path,
                           processed_filename=processed_filename)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        logging.debug("Arquivo salvo em: %s", upload_path)

        go_nord = GoNord()
        image = go_nord.open_image(upload_path)

        processed_filename = f"nordified_{os.path.splitext(filename)[0]}.jpg"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)

        go_nord.convert_image(image, save_path=processed_path)
        logging.debug("Imagem processada salva em: %s", processed_path)

        if not os.path.exists(processed_path):
            logging.error("Arquivo processado não encontrado em: %s", processed_path)
        else:
            is_readable = os.access(processed_path, os.R_OK)
            logging.debug("O arquivo processado é legível? %s", is_readable)
            logging.debug("Conteúdo da pasta processed: %s", os.listdir(app.config['PROCESSED_FOLDER']))

        processed_image_url = url_for('static', filename=f'images/processed/{processed_filename}')
        logging.debug("URL da imagem processada: %s", processed_image_url)

        return redirect(url_for('index',
                                processed_image_path=processed_image_url,
                                processed_filename=processed_filename))
    return "Invalid file format", 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    print("Diretório de trabalho atual:", os.getcwd())
    app.run(debug=True)
