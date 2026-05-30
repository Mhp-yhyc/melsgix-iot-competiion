from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import base64

app = Flask(__name__)
CORS(app)  # 全局允许跨域，前端正常调用

# ===================== 【必填配置，手动修改】 =====================
# 从 Railway 环境变量读取 GitHub 令牌
GITHUB_TOKEN = os.getenv("GH_TOKEN")
# 你的 GitHub 用户名 / 仓库名
REPO_OWNER = "Mhp-yhyc"
REPO_NAME = "melsgix-iot-competiion"
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
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return []
    items = resp.json()
    folders = []
    for item in items:
        if item.get("type") == "dir":
            folders.append(item.get("name"))
    return folders

# 工具函数：向 GitHub 指定路径写入 Markdown 文件
def write_markdown_file(file_path: str, md_content: str, commit_msg: str):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    encode_content = base64.b64encode(md_content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_msg,
        "content": encode_content
    }
    requests.put(url, json=payload, headers=HEADERS, timeout=10)

# 接口1：获取仓库【根目录下所有一级文件夹】
@app.route("/api/get-first-dir", methods=["GET"])
def get_first_dir():
    folders = get_repo_folders("")
    # 过滤掉 backend 目录（后端代码目录，不展示为分类）
    filter_folders = [f for f in folders if f != "backend"]
    return jsonify({"data": filter_folders})

# 接口2：根据一级目录名称，获取其下【二级子文件夹】
@app.route("/api/get-second-dir", methods=["GET"])
def get_second_dir():
    first_dir = request.args.get("first_dir", "")
    if not first_dir:
        return jsonify({"data": []})
    folders = get_repo_folders(first_dir)
    return jsonify({"data": folders})

# 接口3：提交笔记到对应目录（核心上传接口）
@app.route("/api/upload-note", methods=["POST"])
def upload_note():
    try:
        data = request.json
        first_dir = data.get("first_dir", "")   # 一级目录 如：01-嵌入式硬件
        second_dir = data.get("second_dir", "") # 二级目录 如：传感器
        note_title = data.get("title", "").strip()
        note_content = data.get("content", "").strip()

        # 基础校验
        if not note_title or not note_content or not first_dir:
            return jsonify({"code": 400, "msg": "分类、标题、内容不能为空"}), 400

        # 拼接完整存储路径
        if second_dir:
            full_dir_path = f"{first_dir}/{second_dir}"
        else:
            full_dir_path = first_dir

        # 处理文件名（替换特殊字符，避免 GitHub 路径错误）
        safe_filename = note_title.replace("/", "-").replace("\\", "-") + ".md"
        full_file_path = f"{full_dir_path}/{safe_filename}"

        # 拼接标准 Markdown 内容
        md_body = f"# {note_title}\n\n{note_content}"
        commit_info = f"【智能护宝技术库】新增笔记：{note_title}"

        # 写入文件到 GitHub
        write_markdown_file(full_file_path, md_body, commit_info)
        return jsonify({"code": 200, "msg": f"笔记已成功保存至：{full_dir_path}"}), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": f"上传失败：{str(e)}"}), 500

# ------------------- 新增：获取指定路径下所有内容（文件夹+文件） -------------------
def get_repo_contents(path: str = "") -> list:
    """
    获取仓库指定路径下的所有内容（文件夹和文件）
    :param path: 仓库内路径，如 "01-嵌入式硬件/传感器"
    :return: 包含名称、类型、路径、链接的列表
    """
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return []
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

@app.route("/api/get-contents", methods=["GET"])
def get_contents():
    """前端调用此接口，获取指定目录下的所有内容"""
    target_path = request.args.get("path", "")
    contents = get_repo_contents(target_path)
    return jsonify({"data": contents})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
