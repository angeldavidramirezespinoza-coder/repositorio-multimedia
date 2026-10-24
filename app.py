import os
import gc
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de carpetas y formatos permitidos
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'mp4', 'webm', 'mkv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Límite máximo de subida: 500 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in {'mp3', 'wav', 'ogg'}:
        return 'audio'
    elif ext in {'mp4', 'webm', 'mkv'}:
        return 'video'
    return 'unknown'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """Retorna la lista de archivos multimedia subidos."""
    files_list = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                files_list.append({
                    'title': filename,
                    'type': get_file_type(filename),
                    'url': f'/media/{filename}'
                })
    return jsonify(files_list)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Ruta para recibir y guardar archivos subidos."""
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({
            'message': 'Archivo subido exitosamente',
            'file': {
                'title': filename,
                'type': get_file_type(filename),
                'url': f'/media/{filename}'
            }
        }), 200
    
    return jsonify({'error': 'Formato de archivo no permitido'}), 400

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Elimina un archivo del servidor de forma segura."""
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(file_path):
        try:
            # Forzar recolección de basura para liberar cualquier referencia en Python
            gc.collect()
            os.remove(file_path)
            return jsonify({'message': 'Archivo eliminado correctamente'}), 200
        except PermissionError:
            return jsonify({'error': 'El archivo está siendo usado por otro proceso o reproductor.'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'El archivo no existe'}), 404

@app.route('/media/<filename>')
def serve_media(filename):
    """Servidor estático de los archivos multimedia almacenados."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Configuración de puerto dinámico compatible con Render y entorno local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)