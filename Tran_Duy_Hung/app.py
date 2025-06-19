from flask import Flask, render_template, request, send_file, jsonify, session
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import os
import base64
import json
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = os.urandom(24)  # Cho session

# Tạo thư mục uploads nếu chưa tồn tại
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Tạo file lưu trữ lịch sử nếu chưa tồn tại
HISTORY_FILE = 'history.json'
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w') as f:
        json.dump([], f)

def generate_key_pair():
    """Tạo cặp khóa RSA"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    
    # Lưu private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open('private_key.pem', 'wb') as f:
        f.write(private_pem)
    
    # Lưu public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open('public_key.pem', 'wb') as f:
        f.write(public_pem)
    
    return private_key, public_key

def sign_file(file_path, private_key):
    """Ký số file bằng private key"""
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    signature = private_key.sign(
        file_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(file_path, signature, public_key):
    """Xác thực chữ ký số"""
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    try:
        public_key.verify(
            base64.b64decode(signature),
            file_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def add_to_history(action, filename, signature, is_valid=None):
    """Thêm hoạt động vào lịch sử"""
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except:
        history = []
    
    history.append({
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'filename': filename,
        'signature': signature,
        'is_valid': is_valid
    })
    
    # Giới hạn lịch sử 100 mục gần nhất
    history = history[-100:]
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Lưu file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    try:
        # Tạo cặp khóa và ký số file
        private_key, public_key = generate_key_pair()
        signature = sign_file(file_path, private_key)
        
        # Thêm vào lịch sử
        add_to_history('Ký số', file.filename, signature)
        
        return jsonify({
            'filename': file.filename,
            'signature': signature
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Xóa file tạm
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/verify', methods=['POST'])
def verify_file():
    if 'file' not in request.files or 'signature' not in request.form:
        return jsonify({'error': 'Missing file or signature'}), 400
    
    file = request.files['file']
    signature = request.form['signature']
    
    # Lưu file tạm thời
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    try:
        # Đọc public key
        with open('public_key.pem', 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        
        # Xác thực chữ ký
        is_valid = verify_signature(file_path, signature, public_key)
        
        # Thêm vào lịch sử
        add_to_history('Xác thực', file.filename, signature, is_valid)
        
        return jsonify({'valid': is_valid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Xóa file tạm
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/history')
def get_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        return jsonify(history)
    except:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)