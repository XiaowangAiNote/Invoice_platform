import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--add-data=static;static',
    '--add-data=config.json;.',
    '--add-data=index.html;.',
    '--add-data=styles.css;.',
    '--add-data=main.js;.',
    '--name=InvoicePlatform',
    '--clean',
    '--exclude-module=numpy',
    '--exclude-module=pandas',
    '--exclude-module=matplotlib',
    '--exclude-module=scipy',
    '--exclude-module=PIL',
    '--exclude-module=cv2',
    '--hidden-import=flask',
    '--hidden-import=flask_cors',
    '--hidden-import=requests',
    '--hidden-import=oss2',
    '--hidden-import=httpx',
    '--hidden-import=webview'
])
