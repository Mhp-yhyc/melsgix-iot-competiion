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
# 核心配置（已按你的需求调整）
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_OWNER = "Mhp-yhyc"
REPO_NAME = "melsgix-iot-competiion"  # 注意：建议检查拼写是否为"competition"
GITHUB_BRANCH = "main"
# 关键修改：起始扫描目录设为 tech-handbok
START_DIR = "docs-site/tech-handbok"
# 关键修改：扫描深度设为2级（从START_DIR开始向下2级）
SCAN_DEPTH = 2
# =================================================================

# GitHub 请求头
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 核心工具：带深度控制的递归获取目录内容
def get_repo_contents_with_depth(path: str, current_depth: int = 0) -> list:
    """
    从指定路径开始，递归获取指定深度的目录内容
    :param path: 仓库内路径，如 "docs-site/tech-handbok"
    :param current_depth: 当前递归深度（起始为0）
    :return: 包含名称、类型、路径、链接、子内容的嵌套列表
    """
    # 如果当前深度达到设定的最大深度，停止递归
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
                "type": item.get("type"),  # "dir" 或 "file"
                "path": item.get("path"),
                "html_url": item.get("html_url"),
                "sub_contents": []  # 子内容容器
            }
            
            # 如果是文件夹，且当前深度小于最大深度，继续递归
            if item.get("type") == "dir" and current_depth < SCAN_DEPTH - 1:
                content["sub_contents"] = get_repo_contents_with_depth(
                    item.get("path"), 
                    current_depth + 1  # 深度+1
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
# 接口1：获取 tech-handbok 下的一级分类（01-嵌入式硬件等）
@app.route("/api/get-first-dir", methods=["GET"])
def get_first_dir():
    """获取 tech-handbok 下的一级文件夹（即你需要的分类）"""
    folders = get_repo_folders(START_DIR)
    logger.info(f"tech-handbok 下的一级分类: {folders}")
    return jsonify({
        "data": folders, 
        "start_dir": START_DIR,
        "branch": GITHUB_BRANCH
    })

# 接口2：获取 tech-handbok 下两级深度的完整目录结构
@app.route("/api/get-two-level-contents", methods=["GET"])
def get_two_level_contents():
    """从 tech-handbok 开始，向下扫描两级的完整目录结构"""
    full_contents = get_repo_contents_with_depth(START_DIR)
    return jsonify({
        "data": full_contents,
        "start_dir": START_DIR,
        "scan_depth": SCAN_DEPTH,
        "branch": GITHUB_BRANCH
    })

# 接口3：获取指定目录的内容（带深度控制）
@app.route("/api/get-contents/<path:dir_path>", methods=["GET"])
def get_contents(dir_path):
    """
    获取指定目录的内容（默认扫描两级）
    示例：/api/get-contents/docs-site/tech-handbok/01-嵌入式硬件
    """
    # 拼接完整路径
    full_path = dir_path if dir_path.startswith(START_DIR) else f"{START_DIR}/{dir_path}"
    contents = get_repo_contents_with_depth(full_path)
    return jsonify({
        "data": contents,
        "current_path": full_path,
        "scan_depth": SCAN_DEPTH,
        "branch": GITHUB_BRANCH
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
