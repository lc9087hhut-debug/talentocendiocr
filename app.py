import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import shutil
from factura_processor import FacturaProcessor
from main import detect_factura_type

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp(prefix='factura_uploads_')
app.config['SECRET_KEY'] = 'your-secret-key-here'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Detect invoice type
        factura_type = detect_factura_type(file_path)
        
        if factura_type == "desconocido":
            return jsonify({
                'success': False, 
                'error': 'Could not detect invoice type. Please try again or select manually.',
                'file_path': file_path
            }), 400
        
        success, data = FacturaProcessor.process_factura(file_path, factura_type)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to process invoice. Please check the file format.',
                'file_path': file_path
            }), 400
        
        csv_content = "Campo,Valor\n"
        for k, v in data.items():
            v_str = str(v).replace('"', '""')
            csv_content += f'"{k}","{v_str}"\n'
        
        return jsonify({
            'success': True,
            'data': data,
            'invoice_type': factura_type,
            'filename': filename,
            'csv_content': csv_content,
            'file_path': file_path
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }), 500

@app.route('/process_batch', methods=['POST'])
def process_batch():
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': 'No files selected'}), 400
        
        results = []
        errors = []
        
        for file in files:
            if not allowed_file(file.filename):
                errors.append({
                    'filename': file.filename,
                    'error': 'Only PDF files are allowed'
                })
                continue
            
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                factura_type = detect_factura_type(file_path)
                
                if factura_type == "desconocido":
                    errors.append({
                        'filename': filename,
                        'error': 'Could not detect invoice type'
                    })
                    continue
            
                success, data = FacturaProcessor.process_factura(file_path, factura_type)
                
                if success:
                    results.append({
                        'filename': filename,
                        'invoice_type': factura_type,
                        'data': data
                    })
                else:
                    errors.append({
                        'filename': filename,
                        'error': 'Failed to process invoice'
                    })
            
            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'errors': errors,
            'total_processed': len(results),
            'total_errors': len(errors)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing batch: {str(e)}'
        }), 500

@app.route('/download_csv', methods=['POST'])
def download_csv():
    try:
        data = request.json
        csv_content = data.get('csv_content', '')
        filename = data.get('filename', 'invoice_data')
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        temp_file.write(csv_content)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'{filename}_extracted.csv',
            mimetype='text/csv'
        )
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("\n" + "="*50)
    print("Factura OCR Processing Interface")
    print("="*50)
    print(f"Server starting on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)

