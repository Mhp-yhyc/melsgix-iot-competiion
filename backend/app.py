from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import base64
import logging  

app = Flask(__name__)
CORS(app)  # 全局允许跨域

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# 核心配置（确认正确！）
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_OWNER = "Mhp-yhyc"
REPO_NAME = "melsgix-iot-competiion"
GITHUB_BRANCH = "main"
ROOT_CONTENT_DIR = "docs-site"  # 你的内容根目录
# =================================================================

# GitHub 请求头
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 核心工具：递归获取目录下所有内容（支持多级目录）
def get_repo_contents_recursive(path: str = "") -> list:
    """
    递归获取指定路径下所有内容（文件+文件夹），包含完整层级结构
    :param path: 仓库内路径，如 "docs-site/01-嵌入式硬件"
    :return: 包含名称、类型、路径、链接、子内容的嵌套列表
    """
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        logger.info(f"API 响应: {resp.status_code} | 路径: {path}")
        items = resp.json()
        contents = []
        
        for item in items:
            content = {
                "name": item.get("name"),
                "type": item.get("type"),  # "dir" 或 "file"
                "path": item.get("path"),
                "html_url": item.get("html_url"),
                "sub_contents": []  # 子内容容器（文件夹会填充）
            }
            
            # 如果是文件夹，递归获取子内容
            if item.get("type") == "dir":
                content["sub_contents"] = get_repo_contents_recursive(item.get("path"))
            
            contents.append(content)
        return contents
    except requests.exceptions.RequestException as e:
        logger.error(f"获取内容失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"错误响应: {e.response.status_code} - {e.response.text}")
        return []

# 工具函数：获取指定路径下的一级文件夹（非递归）
def get_repo_folders(path: str = "") -> list:
    """获取指定路径下的一级文件夹列表"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        return [item.get("name") for item in items if item.get("type") == "dir"]
    except requests.exceptions.RequestException as e:
        logger.error(f"获取文件夹失败: {str(e)}")
        return []

# 工具函数：写入Markdown文件（保持不变）
def write_markdown_file(file_path: str, md_content: str, commit_msg: str):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}?ref={GITHUB_BRANCH}"
    encode_content = base64.b64encode(md_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_msg,
        "content": encode_content,
        "branch": GITHUB_BRANCH
    }
    try:
        resp = requests.put(url, json=payload, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        logger.info(f"文件写入成功: {file_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"文件写入失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"错误响应: {e.response.status_code} - {e.response.text}")

# -------------------------- 接口调整 --------------------------
# 接口1：获取内容根目录（docs-site）下的一级分类文件夹
@app.route("/api/get-first-dir", methods=["GET"])
def get_first_dir():
    # 关键修改：从 ROOT_CONTENT_DIR（docs-site）获取一级文件夹
    folders = get_repo_folders(ROOT_CONTENT_DIR)
    logger.info(f"内容根目录下的一级分类: {folders}")
    return jsonify({
        "data": folders, 
        "root_dir": ROOT_CONTENT_DIR,
        "branch": GITHUB_BRANCH
    })

# 接口2：获取指定目录的完整内容（支持递归多层）
@app.route("/api/get-full-contents/<path:dir_path>", methods=["GET"])
def get_full_contents(dir_path):
    """
    获取指定目录的完整内容（含子目录和文件）
    示例：/api/get-full-contents/docs-site/01-嵌入式硬件
    """
    # 拼接完整路径（防止用户输入不带docs-site）
    full_path = f"{ROOT_CONTENT_DIR}/{dir_path}" if not dir_path.startswith(ROOT_CONTENT_DIR) else dir_path
    contents = get_repo_contents_recursive(full_path)
    return jsonify({
        "data": contents,
        "current_path": full_path,
        "branch": GITHUB_BRANCH
    })

# 接口3：获取内容根目录的完整目录树（一键获取所有层级）
@app.route("/api/get-full-tree", methods=["GET"])
def get_full_tree():
    """获取 docs-site 下的完整目录结构（含所有二级/三级内容）"""
    full_tree = get_repo_contents_recursive(ROOT_CONTENT_DIR)
    return jsonify({
        "data": full_tree,
        "root_dir": ROOT_CONTENT_DIR,
        "branch": GITHUB_BRANCH
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
