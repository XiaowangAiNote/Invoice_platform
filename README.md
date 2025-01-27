# 智能报销管理系统

智能报销管理系统，提供文件分类、抽取和管理功能。

## 可执行文件版本

windows系统运行`InvoicePlatform.exe`即可

## 系统要求

- Python 3.8 或更高版本

## 环境配置

1. 创建虚拟环境（二选一）

### 方法一：使用 venv

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
```

### 方法二：使用 conda

```bash
# 创建虚拟环境
conda create -n invoice_platform python=3.8

# 激活虚拟环境
conda activate invoice_platform
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

首次运行前需要配置以下内容：

1. OSS存储配置：用于上传本地文件生成url
2. Coze API配置：用于文件识别和数据库配置

配置文件位于 `config.json`，首次运行时会自动创建。

### 教程

[零代码搭建智能报销系统（一）](https://www.bilibili.com/video/BV1LYwHemE5V)

[手把手教你搭建智能报销系统（二）](https://www.bilibili.com/video/BV1KZfzYCEk1)

### Coze prompt

[prompt.md](prompt.md)


## 运行应用

```bash
python app.py
```

启动后会自动打开应用窗口，访问地址为：`http://localhost:5000` 或 `http://127.0.0.1:5000`

## 主要功能

- 文件上传和识别
- 文件配置管理

## 注意事项

1. 成功运行时需要完成系统配置
2. 确保端口5000未被其他应用占用

