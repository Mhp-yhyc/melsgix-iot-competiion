from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import base64
import logging
import json
import datetime

app = Flask(__name__)
# 全局跨域放行
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================== 全局配置 ======================
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_OWNER = "Mhp-yhyc"
REPO_NAME = "melsgix-iot-competiion"
GITHUB_BRANCH = "main"
START_DIR = "docs"  # 根目录固定为 docs
SCAN_DEPTH = 2

# GitHub 通用请求头
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ====================== 工具函数 ======================
def get_repo_contents_with_depth(path: str, current_depth: int = 0) -> list:
    """递归获取目录内容（带深度限制）"""
    if current_depth >= SCAN_DEPTH:
        return []
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        logger.info(f"API 响应: {resp.status_code} | 路径: {path} | 深度: {current_depth}")
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
                content["sub_contents"] = get_repo_contents_with_depth(item.get("path"), current_depth + 1)
            contents.append(content)
        return contents
    except requests.exceptions.RequestException as e:
        logger.error(f"获取目录失败: {str(e)}")
        return []

def get_repo_folders(path: str = "") -> list:
    """获取指定路径下 一级文件夹名称列表"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}?ref={GITHUB_BRANCH}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        return [item.get("name") for item in items if item.get("type") == "dir"]
    except requests.exceptions.RequestException as e:
        logger.error(f"获取文件夹失败: {str(e)}")
        return []

def get_file_raw_content(file_path: str) -> str:
    """读取 GitHub 上单个 MD 文件原始内容"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}?ref={GITHUB_BRANCH}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # GitHub 返回 base64 编码内容
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"读取文件失败 {file_path}: {str(e)}")
        return ""

def write_markdown_file(file_path: str, md_content: str, commit_msg: str):
    """写入/更新 MD 文件到 GitHub（自动处理 SHA）"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    # 1. 先尝试获取现有文件信息
    sha = None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            sha = data.get("sha")
    except:
        pass

    encode_content = base64.b64encode(md_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_msg,
        "content": encode_content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    try:
        resp = requests.put(url, json=payload, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        logger.info(f"文件提交成功: {file_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"文件提交失败 {file_path}: {str(e)}")
        return False

# ====================== 原有基础接口（保留） ======================
@app.route("/api/get-first-dir", methods=["GET"])
def get_first_dir():
    """获取一级分类目录（给编辑器初始化下拉）"""
    folders = get_repo_folders(START_DIR)
    return jsonify({"list": folders})

@app.route("/api/get-two-level-contents", methods=["GET"])
def get_two_level_contents():
    full_contents = get_repo_contents_with_depth(START_DIR)
    return jsonify({
        "data": full_contents,
        "start_dir": START_DIR,
        "scan_depth": SCAN_DEPTH,
        "branch": GITHUB_BRANCH
    })

@app.route("/api/get-contents/<path:dir_path>", methods=["GET"])
def get_contents(dir_path):
    """目录列表页使用：获取指定目录下所有文件/文件夹"""
    full_path = f"{START_DIR}/{dir_path}"
    contents = get_repo_contents_with_depth(full_path)
    return jsonify({
        "data": contents,
        "current_path": full_path,
        "scan_depth": SCAN_DEPTH,
        "branch": GITHUB_BRANCH
    })

# ====================== 【新增】编辑器专用接口（关键） ======================
@app.route("/api/list-second-dir", methods=["POST"])
def list_second_dir():
    """根据一级分类，获取二级子分类"""
    data = request.get_json()
    first_dir = data.get("firstDir", "")
    if not first_dir:
        return jsonify({"list": []})
    full_path = f"{START_DIR}/{first_dir}"
    sub_dirs = get_repo_folders(full_path)
    # 前置空选项 = 无二级分类
    res_list = [""] + sub_dirs
    return jsonify({"list": res_list})

@app.route("/api/list-notes", methods=["POST"])
def list_notes():
    """获取指定目录下所有 .md 笔记名称（不含后缀）"""
    data = request.get_json()
    first_dir = data.get("firstDir", "")
    second_dir = data.get("secondDir", "")

    if not first_dir:
        return jsonify({"list": []})

    # 拼接完整路径
    if second_dir:
        full_path = f"{START_DIR}/{first_dir}/{second_dir}"
    else:
        full_path = f"{START_DIR}/{first_dir}"

    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{full_path}?ref={GITHUB_BRANCH}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        # 只筛选 md 文件，去掉后缀
        note_list = []
        for item in items:
            if item.get("type") == "file" and item["name"].lower().endswith(".md"):
                note_name = os.path.splitext(item["name"])[0]
                note_list.append(note_name)
        return jsonify({"list": note_list})
    except Exception as e:
        logger.error(f"获取笔记列表失败: {e}")
        return jsonify({"list": []})

@app.route("/api/get-note-content", methods=["POST"])
def get_note_content():
    """读取单篇笔记内容（编辑模式加载原文）"""
    data = request.get_json()
    first_dir = data.get("firstDir", "")
    second_dir = data.get("secondDir", "")
    note_name = data.get("noteName", "")

    if not first_dir or not note_name:
        return jsonify({"success": False, "msg": "参数不全"})

    # 拼接完整文件路径
    file_name = f"{note_name}.md"
    if second_dir:
        full_file_path = f"{START_DIR}/{first_dir}/{second_dir}/{file_name}"
    else:
        full_file_path = f"{START_DIR}/{first_dir}/{file_name}"

    content = get_file_raw_content(full_file_path)
    if content == "":
        return jsonify({"success": False, "msg": "笔记不存在或读取失败"})
    return jsonify({"success": True, "content": content})

# ====================== 笔记提交接口（对接编辑器正式提交） ======================
@app.route("/api/submit-note", methods=["POST"])
def submit_note():
    """编辑器正式提交：新建/覆盖笔记"""
    data = request.get_json()
    first_dir = data.get("firstDir", "")
    second_dir = data.get("secondDir", "")
    note_name = data.get("noteName", "")
    markdown = data.get("markdown", "")

    if not first_dir or not note_name or not markdown:
        return jsonify({"success": False, "msg": "参数缺失"})

    file_name = f"{note_name}.md"
    if second_dir:
        full_path = f"{START_DIR}/{first_dir}/{second_dir}/{file_name}"
    else:
        full_path = f"{START_DIR}/{first_dir}/{file_name}"

    commit_msg = f"更新笔记: {note_name}"
    ok = write_markdown_file(full_path, markdown, commit_msg)
    if ok:
        return jsonify({"success": True, "msg": "提交成功，已同步至GitHub"})
    else:
        return jsonify({"success": False, "msg": "提交失败，请检查权限或网络"})

# 草稿接口（仅前端临时保存，可选：如需云端草稿可自行扩展）
@app.route("/api/save-draft", methods=["POST"])
def save_draft():
    """本地临时草稿，这里只做返回（前端浏览器本地存储也可）"""
    return jsonify({"success": True, "msg": "草稿已保存"})

# ====================== 公告 + 最近提交记录（保留原有） ======================
NOTICE_FILE = "notice.json"
if not os.path.exists(NOTICE_FILE):
    with open(NOTICE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "content": "欢迎使用 MeLsGix 智护宝技术库！管理员可在后台发布团队任务～",
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }, f, ensure_ascii=False, indent=2)

def load_notice():
    with open(NOTICE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_notice(content):
    data = {
        "content": content,
        "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    with open(NOTICE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/api/get-notice", methods=["GET"])
def api_get_notice():
    return jsonify(load_notice())

@app.route("/api/edit-notice", methods=["POST"])
def api_edit_notice():
    data = request.json
    content = data.get("content", "")
    if not content:
        return jsonify({"code": 400, "msg": "公告内容不能为空"})
    save_notice(content)
    return jsonify({"code": 200, "msg": "公告更新成功"})

@app.route("/api/get-latest-commit", methods=["GET"])
def get_latest_commit():
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits?per_page=10"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        commits = resp.json()
        result = []
        for c in commits:
            try:
                result.append({
                    "author": c["commit"]["author"]["name"],
                    "commit_time": c["commit"]["author"]["date"].replace("T", " ")[:-6],
                    "msg": c["commit"]["message"],
                    "file_name": c["files"][0]["filename"] if "files" in c and len(c["files"]) > 0 else "更新目录"
                })
            except:
                continue
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        logger.error(f"获取提交记录失败: {e}")
        return jsonify({"code": 500, "msg": "获取失败"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
