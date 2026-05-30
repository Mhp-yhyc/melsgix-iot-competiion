from flask import Flask, request, jsonify
import requests
import base64
import os
from datetime import datetime

app = Flask(__name__)

# ===================== 你的配置（已自动填写）=====================
GH_OWNER = "Mhp-yhyc"
GH_REPO = "melsgix-iot-competiion"
GH_BRANCH = "main"
# =================================================================

# 跨域配置（解决前端访问报错）
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    return response

@app.route('/api/create-note', methods=['POST'])
def create_note():
    GH_TOKEN = os.getenv('GH_TOKEN')
    if not GH_TOKEN:
        return jsonify({"code": 500, "msg": "后端未配置GitHub令牌"}), 500

    try:
        data = request.json
        folder = data.get('folder', '07-项目管理')
        title = data.get('title', '未命名笔记').replace(r'[\\/:*?"<>|]', "")
        content = data.get('content', '')

        # 生成标准Markdown笔记
        md_content = f"""---
title: {title}
category: {folder.split('/').join(' > ')}
date: {datetime.now().strftime('%Y-%m-%d')}
---

# {title}

## 笔记信息
- 分类：{folder.split('/').join(' > ')}
- 创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 创建人：智护宝团队

## 内容
{content}

---
*MeLsGix 智护宝技术库 | 自动生成*
"""
        # 生成文件路径
        file_path = f"docs/{folder}/{title}.md"
        encoded_content = base64.b64encode(md_content.encode('utf-8')).decode('utf-8')

        # GitHub API
        url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/contents/{file_path}"
        headers = {"Authorization": f"token {GH_TOKEN}"}

        # 获取文件SHA（更新用）
        sha = None
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            sha = res.json()["sha"]

        # 提交文件
        payload = {
            "message": f"feat: 新增笔记 {title}",
            "content": encoded_content,
            "branch": GH_BRANCH
        }
        if sha:
            payload["sha"] = sha

        response = requests.put(url, json=payload, headers=headers)
        if response.ok:
            return jsonify({"code": 200, "msg": "✅ 提交成功！网站1分钟后自动更新"}), 200
        else:
            return jsonify({"code": 500, "msg": "❌ GitHub提交失败"}), 500

    except Exception as e:
        return jsonify({"code": 500, "msg": f"服务器错误：{str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
