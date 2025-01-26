import oss2
import json
import os
import logging
import sys

logger = logging.getLogger(__name__)

# Global variables
access_key_id = None
access_key_secret = None
bucket_name = None
endpoint = None
region = None
bucket = None
is_configured = False

def get_config_path():
    """Get the absolute path of config.json"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是直接运行 Python 脚本
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, 'config.json')

def load_config():
    """Load configuration from config.json file"""
    global access_key_id, access_key_secret, bucket_name, endpoint, region, is_configured
    try:
        config_path = get_config_path()
        settings = json.load(open(config_path, 'r', encoding='utf-8'))
        access_key_id = settings.get('ACCESS_KEY_ID', '')
        access_key_secret = settings.get('ACCESS_KEY_SECRET', '')
        bucket_name = settings.get('BUCKET_NAME', '')
        endpoint = settings.get('ENDPOINT', '')
        region = settings.get('REGION', '')
        
        # Check if all required fields are properly configured
        is_configured = all([
            access_key_id,
            access_key_secret,
            bucket_name,
            endpoint,
            region
        ])
        
        if not is_configured:
            logger.warning("OSS configuration is incomplete")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        return False

def init_oss_client(access_key_id, access_key_secret, endpoint, bucket_name):
    """Initialize OSS client with given credentials"""
    global bucket
    if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
        logger.warning("Cannot initialize OSS client: missing configuration")
        return False
    try:
        bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)
        return True
    except Exception as e:
        logger.error(f"Failed to initialize OSS client: {str(e)}")
        return False

def reload_config():
    """Reload configuration and reinitialize OSS client"""
    if load_config():
        return init_oss_client(access_key_id, access_key_secret, endpoint, bucket_name)
    return False

def is_oss_configured():
    """Check if OSS is properly configured"""
    return is_configured and bucket is not None

# Initial loading of configuration
load_config()
init_oss_client(access_key_id, access_key_secret, endpoint, bucket_name)

def upload_file(file_path, object_name):
    """
    上传文件到OSS
    :param file_path: 本地文件路径
    :param object_name: OSS中的文件名
    :return: 文件的公开访问URL或None（如果上传失败）
    """
    if not is_oss_configured():
        logger.error("Cannot upload file: OSS is not properly configured")
        return None
        
    try:
        # 确保文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.debug(f"Uploading file: {file_path} to OSS as {object_name}")
        bucket.put_object_from_file(object_name, file_path)

        public_url = f"https://{bucket_name}.{endpoint.lstrip('http://')}/{object_name}"
        logger.debug(f"File uploaded successfully. Public URL: {public_url}")
        return public_url

    except Exception as e:
        logger.error(f"Failed to upload file to OSS: {str(e)}")
        return None
