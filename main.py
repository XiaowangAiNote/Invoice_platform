import webview
import threading
from app import app
import requests
import json
import sys
import os

def run_flask():
    app.run(port=5000)

def check_config():
    try:
        response = requests.get('http://localhost:5000/api/config_status')
        status = response.json()
        if not status['oss_configured'] or not status['coze_configured']:
            message = "系统配置未完成，请先完成配置："
            if not status['oss_configured']:
                message += "\\n- OSS存储配置未完成"
            if not status['coze_configured']:
                message += "\\n- Coze API配置未完成"
            return message
    except Exception as e:
        return f"检查配置状态时出错：{str(e)}"
    return None

def show_config_status():
    message = check_config()
    if message:
        webview.windows[0].evaluate_js(f"alert('{message}')")

def create_window():
    # 设置环境变量
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    os.environ['no_proxy'] = 'localhost,127.0.0.1'
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)
    
    # 创建web视图
    webview.create_window(
        "发票管理平台",
        "http://localhost:5000",
        width=1200,
        height=800
    )
    
    # 启动定时器检查配置
    threading.Timer(2, show_config_status).start()
    
    # 启动窗口
    webview.start()

if __name__ == "__main__":
    # 确保配置文件存在
    if not os.path.exists('config.json'):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump({
                "ACCESS_KEY_ID": "",
                "ACCESS_KEY_SECRET": "",
                "BUCKET_NAME": "",
                "ENDPOINT": "",
                "REGION": "",
                "COZE_TOKEN": "",
                "COZE_APP_ID": "",
                "WORKFLOW_IDS": {
                    "PROCESS_FILE": "",
                    "SHOW_DATABASE": "",
                    "ADD_DATABASE": "",
                    "DELETE_DATABASE": ""
                }
            }, f, indent=4, ensure_ascii=False)
    
    # 启动Flask服务器
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # 创建窗口
    create_window()
