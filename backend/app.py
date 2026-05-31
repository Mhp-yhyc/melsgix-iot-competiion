from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import base64
import logging  

app = Flask(__name__)
# 强化跨域，解决前端本地访问卡住、跨域拦截问题
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# 核心配置
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_OWNER = "Mhp-yhyc"
REPO_NAME = "melsgix-iot-competiion" 
GITHUB_BRANCH = "main"
START_DIR = "docs"
SCAN_DEPTH = 2
# =================================================================

# GitHub 请求头
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 核心工具：带深度控制的递归获取目录内容
def get_repo_contents_with_depth(path: str, current_depth: int = 0) -> list:
    if current_depth >= SCAN_DEPTH:
        return []
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        logger.info(f"API 响应: {resp.status_code} | 路径: {path} | 当前深度: {current_depth}")
        items = resp.json()
        contents = []
        
        for item in items:
            content = {
                "name": item.get("name"),
                "type": item.get("type"),
                "path": item.get("path"),
                "html_url": item.get("html_url"),
                "sub_contents": []
            }
            
            if item.get("type") == "dir" and current_depth < SCAN_DEPTH - 1:
                content["sub_contents"] = get_repo_contents_with_depth(
                    item.get("path"), 
                    current_depth + 1
                )
            
            contents.append(content)
        return contents
    except requests.exceptions.RequestException as e:
        logger.error(f"获取内容失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"错误响应: {e.response.status_code} - {e.response.text}")
        return []

# 工具函数：获取指定路径下的一级文件夹（非递归）
def get_repo_folders(path: str = "") -> list:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        return [item.get("name") for item in items if item.get("type") == "dir"]
    except requests.exceptions.RequestException as e:
        logger.error(f"获取文件夹失败: {str(e)}")
        return []

# 工具函数：写入Markdown文件
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

# -------------------------- 业务接口 --------------------------
# 接口1：获取 tech-handbok 下一级分类
@app.route("/api/get-first-dir", methods=["GET"])
def get_first_dir():
    folders = get_repo_folders(START_DIR)
    logger.info(f"tech-handbok 下的一级分类: {folders}")
    return jsonify({
        "data": folders, 
        "start_dir": START_DIR,
        "branch": GITHUB_BRANCH
    })

# 接口2：获取两级完整目录结构
@app.route("/api/get-two-level-contents", methods=["GET"])
def get_two_level_contents():
    full_contents = get_repo_contents_with_depth(START_DIR)
    return jsonify({
        "data": full_contents,
        "start_dir": START_DIR,
        "scan_depth": SCAN_DEPTH,
        "branch": GITHUB_BRANCH
    })

# 接口3：获取指定目录内容
@app.route("/api/get-contents/<path:dir_path>", methods=["GET"])
def get_contents(dir_path):
    full_path = dir_path if dir_path.startswith(START_DIR) else f"{START_DIR}/{dir_path}"
    contents = get_repo_contents_with_depth(full_path)
    return jsonify({
        "data": contents,
        "current_path": full_path,
        "scan_depth": SCAN_DEPTH,
        "branch": GITHUB_BRANCH
    })

# 新增：上传笔记接口（前端提交功能必备）
@app.route("/api/upload-note", methods=["POST"])
def upload_note():
    try:
        data = request.get_json()
        first_dir = data.get("first_dir", "")
        second_dir = data.get("second_dir", "")
        title = data.get("title", "")
        content = data.get("content", "")

        if not first_dir or not title or not content:
            return jsonify({"code": 400, "msg": "参数不完整"})

        # 拼接文件存储路径
        if second_dir:
            file_path = f"{START_DIR}/{first_dir}/{second_dir}/{title}.md"
        else:
            file_path = f"{START_DIR}/{first_dir}/{title}.md"

        write_markdown_file(file_path, content, f"新增笔记：{title}")
        return jsonify({"code": 200, "msg": "笔记提交成功！已同步到GitHub"})

    except Exception as e:
        logger.error(f"上传笔记失败: {str(e)}")
        return jsonify({"code": 500, "msg": "服务器异常，提交失败"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
