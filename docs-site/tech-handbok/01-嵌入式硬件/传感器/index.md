<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>传感器 | 嵌入式硬件 | 智能护宝技术库</title>
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}
body {
    font-family: "Microsoft YaHei", Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    padding: 20px;
    min-height: 100vh;
}
/* 页面容器 */
.container {
    max-width: 1200px;
    margin: 0 auto;
}
/* 页面头部 */
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(255,255,255,0.2);
}
.page-title {
    font-size: 28px;
    font-weight: 600;
}
.back-btn {
    background: rgba(255,255,255,0.2);
    color: #fff;
    padding: 8px 16px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.2s;
}
.back-btn:hover {
    background: rgba(255,255,255,0.3);
}
/* 内容卡片网格 */
.content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 20px;
}
/* 卡片样式 */
.card {
    background: rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 20px;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}
.card-icon {
    font-size: 24px;
    margin-bottom: 10px;
}
.card-title {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 8px;
}
.card-desc {
    font-size: 14px;
    opacity: 0.8;
    margin-bottom: 15px;
}
/* 按钮组 */
.card-buttons {
    display: flex;
    gap: 10px;
}
.btn {
    padding: 8px 14px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    text-decoration: none;
    transition: background 0.2s;
}
.btn-primary {
    background: #409eff;
    color: #fff;
}
.btn-primary:hover {
    background: #3b82f6;
}
.btn-secondary {
    background: rgba(255,255,255,0.2);
    color: #fff;
}
.btn-secondary:hover {
    background: rgba(255,255,255,0.3);
}
/* 加载提示 */
.loading-tip {
    text-align: center;
    font-size: 18px;
    margin-top: 50px;
    opacity: 0.8;
}
/* 空状态 */
.empty-tip {
    text-align: center;
    font-size: 16px;
    opacity: 0.7;
    margin-top: 50px;
}
</style>
</head>
<body>
<div class="container">
    <!-- 页面头部 -->
    <div class="page-header">
        <div class="page-title">📦 传感器 | 嵌入式硬件</div>
        <a href="../../index.md" class="back-btn">← 返回上级</a>
    </div>

    <!-- 内容加载区域 -->
    <div id="loadingTip" class="loading-tip">正在加载目录内容...</div>
    <div id="contentGrid" class="content-grid" style="display: none;"></div>
    <div id="emptyTip" class="empty-tip" style="display: none;">
        当前目录下暂无内容，点击下方按钮新建笔记
    </div>
</div>

<script>
// ===================== 已配置你的PythonAnywhere后端地址 =====================
const API_BASE = "https://mhp.pythonanywhere.com";
const API_GET_CONTENTS = API_BASE + "/api/get-contents";
const CREATE_NOTE_URL = "../../create-note.md"; 
// ======================================================================

// 1. 获取当前页面的目录路径
function getCurrentDirPath() {
    const pathname = window.location.pathname;
    const dirPath = pathname.substring(0, pathname.lastIndexOf("/"));
    return dirPath.replace(/^\//, "");
}

// 2. 渲染目录/文件卡片
function renderContents(contents, currentDir) {
    const grid = document.getElementById("contentGrid");
    grid.style.display = "grid";
    document.getElementById("loadingTip").style.display = "none";

    const folders = contents.filter(item => item.type === "dir");
    const files = contents.filter(item => item.type === "file" && item.name !== "index.md");

    folders.forEach(folder => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <div class="card-icon">📁</div>
            <div class="card-title">${folder.name}</div>
            <div class="card-desc">子目录 · 点击进入查看</div>
            <div class="card-buttons">
                <a href="${folder.path}/index.md" class="btn btn-secondary">进入目录</a>
                <a href="${CREATE_NOTE_URL}?first_dir=${encodeURIComponent(currentDir.split("/")[0])}&second_dir=${encodeURIComponent(currentDir.split("/")[1] + "/" + folder.name)}" class="btn btn-primary">新建笔记</a>
            </div>
        `;
        grid.appendChild(card);
    });

    files.forEach(file => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <div class="card-icon">📄</div>
            <div class="card-title">${file.name.replace(".md", "")}</div>
            <div class="card-desc">笔记文件 · 点击查看原文</div>
            <div class="card-buttons">
                <a href="${file.html_url}" target="_blank" class="btn btn-secondary">查看原文</a>
            </div>
        `;
        grid.appendChild(card);
    });

    if (folders.length === 0 && files.length === 0) {
        document.getElementById("emptyTip").style.display = "block";
        const emptyBtn = document.createElement("div");
        emptyBtn.style.textAlign = "center";
        emptyBtn.style.marginTop = "20px";
        emptyBtn.innerHTML = `
            <a href="${CREATE_NOTE_URL}?first_dir=${encodeURIComponent(currentDir.split("/")[0])}&second_dir=${encodeURIComponent(currentDir.split("/")[1])}" class="btn btn-primary">新建笔记</a>
        `;
        document.getElementById("emptyTip").appendChild(emptyBtn);
    }
}

// 3. 页面加载：自动拉取当前目录内容（适配后端接口）
window.onload = async function() {
    const currentDir = getCurrentDirPath();
    try {
        // 适配你的后端路由：/api/get-contents/路径
        const res = await fetch(`${API_GET_CONTENTS}/${encodeURIComponent(currentDir)}`);
        const data = await res.json();
        renderContents(data.data, currentDir);
    } catch (err) {
        document.getElementById("loadingTip").innerText = "加载失败，请检查后端服务";
        document.getElementById("loadingTip").style.color = "#ff6b6b";
        console.error("请求错误：", err);
    }
};
</script>
</body>
</html>
