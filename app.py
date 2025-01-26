from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
from oss import upload_file, is_oss_configured, reload_config
import time
import httpx
import json
import sys

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the base path for resources
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    BASE_DIR = sys._MEIPASS
else:
    # Running in normal Python environment
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Create static directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'static/pdfjs/cmaps'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static/pdfjs/standard_fonts'), exist_ok=True)

def get_config_path():
    """Get the absolute path of config.json"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是直接运行 Python 脚本
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, 'config.json')

settings = {}
try:
    config_path = get_config_path()
    settings = json.load(open(config_path, 'r', encoding='utf-8'))
    logger.info(f"Successfully loaded config from {config_path}")
except Exception as e:
    logger.warning(f"Failed to load config.json: {str(e)}")

# 从settings中获取配置，使用get方法设置默认值
ACCESS_KEY_ID = settings.get('ACCESS_KEY_ID', '')
ACCESS_KEY_SECRET = settings.get('ACCESS_KEY_SECRET', '')
BUCKET_NAME = settings.get('BUCKET_NAME', '')
ENDPOINT = settings.get('ENDPOINT', '')
REGION = settings.get('REGION', '')
COZE_APP_ID = settings.get('COZE_APP_ID', '')
COZE_TOKEN = settings.get('COZE_TOKEN', '')
WORKFLOW_IDS = settings.get('WORKFLOW_IDS', {
    'PROCESS_FILE': '',
    'SHOW_DATABASE': '',
    'ADD_DATABASE': '',
    'DELETE_DATABASE': ''
})

def is_coze_configured():
    """检查Coze API配置是否完整"""
    return all([COZE_TOKEN, COZE_APP_ID]) and all(WORKFLOW_IDS.values())

def call_coze_workflow(workflow_id, parameters=None, ext=None):
    if parameters is None:
        parameters = {}
    if ext is None:
        ext = {"": ""}

    headers = {
        'Authorization': f'Bearer {COZE_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'workflow_id': workflow_id,
        'app_id': COZE_APP_ID,
        'parameters': parameters,
        'ext': ext
    }
    
    try:
        logger.debug(f"Calling Coze API with data: {json.dumps(data)}")
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                'https://api.coze.cn/v1/workflow/run',
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error calling Coze API: {str(e)}")
        raise

@app.route('/')
def serve_static():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory(BASE_DIR, path)

@app.route('/static/pdfjs/<path:filename>')
def serve_pdfjs(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static/pdfjs'), filename)

@app.route('/api/config_status')
def config_status():
    """获取配置状态"""
    return jsonify({
        'oss_configured': is_oss_configured(),
        'coze_configured': is_coze_configured()
    })

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    try:
        # 生成唯一的文件名
        filename = file.filename
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{os.path.splitext(filename)[0]}_{int(time.time())}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # 确保上传目录存在
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # 保存文件
        logger.debug(f"Saving file to: {file_path}")
        file.save(file_path)
        
        # 上传到OSS并处理文件
        try:
            public_url = upload_file(file_path, unique_filename)
            logger.debug(f"File uploaded successfully. Public URL: {public_url}")
            # 调用Coze API处理文件
            result = call_coze_workflow(
                WORKFLOW_IDS['PROCESS_FILE'],
                {"file": public_url}
            )
            logger.debug(f"Coze API result: {result}")
            return jsonify(result)
        finally:
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs', methods=['GET'])
def get_configs():
    try:
        result = call_coze_workflow(WORKFLOW_IDS['SHOW_DATABASE'])
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting configs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs', methods=['POST'])
def add_config():
    try:
        data = request.json
        if not data or 'file_type' not in data or not data['file_type'].strip():
            return jsonify({'error': '文件类型不能为空'}), 400

        # 确保kv_fields和table_fields存在，如果为空则设为空字符串
        kv_fields = data.get('kv_fields', '').strip()
        table_fields = data.get('table_fields', '').strip()

        result = call_coze_workflow(
            WORKFLOW_IDS['ADD_DATABASE'],
            {
                "file_type": data['file_type'].strip(),
                "kv_fields": kv_fields,
                "table_fields": table_fields
            }
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error adding config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/configs/<file_type>', methods=['DELETE'])
def delete_config(file_type):
    try:
        result = call_coze_workflow(
            WORKFLOW_IDS['DELETE_DATABASE'],
            {"file_type": file_type}
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deleting config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        with open(get_config_path(), 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def save_settings():
    try:
        settings = request.get_json()
        
        # 保存到文件
        with open(get_config_path(), 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        
        # 更新程序中的变量
        global ACCESS_KEY_ID, ACCESS_KEY_SECRET, BUCKET_NAME, ENDPOINT, REGION, COZE_TOKEN, WORKFLOW_IDS, COZE_APP_ID
        ACCESS_KEY_ID = settings['ACCESS_KEY_ID']
        ACCESS_KEY_SECRET = settings['ACCESS_KEY_SECRET']
        BUCKET_NAME = settings['BUCKET_NAME']
        ENDPOINT = settings['ENDPOINT']
        REGION = settings['REGION']
        COZE_APP_ID = settings['COZE_APP_ID']
        COZE_TOKEN = settings['COZE_TOKEN']
        WORKFLOW_IDS = settings['WORKFLOW_IDS']
        
        # 更新 OSS 客户端配置并重新加载 oss.py 中的配置
        reload_config()
        
        return jsonify({'message': 'Settings saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
