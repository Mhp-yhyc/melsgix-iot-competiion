from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import base64
import logging  

app = Flask(__name__)
CORS(app)  # 全局允许跨域，前端正常调用

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# 从 Railway 环境变量读取 GitHub 令牌
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_OWNER = "Mhp-yhyc"
REPO_NAME = "melsgix-iot-competiion"
GITHUB_BRANCH = "main"
# =================================================================

# GitHub 请求公共请求头
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 工具函数：读取指定路径下 所有文件夹（只过滤目录，排除文件）
def get_repo_folders(path: str = "") -> list:
    """
    path: 仓库内路径，空=根目录
    return: 目录名列表
    """
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"  # ?ref=分支名
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()  # 触发HTTP错误（404/401等）
        logger.info(f"GitHub API 响应状态码: {resp.status_code}")
        items = resp.json()
        folders = []
        for item in items:
            if item.get("type") == "dir":
                folders.append(item.get("name"))
        logger.info(f"找到目录: {folders}")
        return folders
    except requests.exceptions.RequestException as e:
        # 详细错误日志
        logger.error(f"GitHub API 调用失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"错误响应: {e.response.status_code} - {e.response.text}")
        return []

# 工具函数：向 GitHub 指定路径写入 Markdown 文件
def write_markdown_file(file_path: str, md_content: str, commit_msg: str):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}?ref={GITHUB_BRANCH}"  # ?ref=分支名
    encode_content = base64.b64encode(md_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_msg,
        "content": encode_content,
        "branch": GITHUB_BRANCH  #指定分支
    }
    try:
        resp = requests.put(url, json=payload, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        logger.info(f"文件写入成功: {file_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"文件写入失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"错误响应: {e.response.status_code} - {e.response.text}")

# 接口1：获取仓库【根目录下所有一级文件夹】
@app.route("/api/get-first-dir", methods=["GET"])
def get_first_dir():
    folders = get_repo_folders("")
    # 过滤掉 backend 目录（后端代码目录，不展示为分类）
    filter_folders = [f for f in folders if f != "backend"]
    return jsonify({"data": filter_folders, "branch": GITHUB_BRANCH})  #返回分支名，方便前端调试

# 工具函数：获取指定路径下所有内容（文件夹+文件）
def get_repo_contents(path: str = "") -> list:
    """
    获取仓库指定路径下的所有内容（文件夹和文件）
    :param path: 仓库内路径，如 "01-嵌入式硬件/传感器"
    :return: 包含名称、类型、路径、链接的列表
    """
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"  # 新增：?ref=分支名
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        contents = []
        for item in items:
            contents.append({
                "name": item.get("name"),
                "type": item.get("type"),  # "dir" 或 "file"
                "path": item.get("path"),
                "html_url": item.get("html_url")
            })
        return contents
    except requests.exceptions.RequestException as e:
        logger.error(f"获取内容失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"错误响应: {e.response.status_code} - {e.response.text}")
        return []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
