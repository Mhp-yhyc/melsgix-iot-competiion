<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>智能护宝技术库 - 新建笔记</title>
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}
body {
    font-family: "Microsoft YaHei", Arial, sans-serif;
    background-color: #f5f7fa;
    color: #2c3e50;
    padding: 24px;
}
.container {
    max-width: 820px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
.page-header {
    text-align: center;
    background-color: #3b82f6;
    color: #fff;
    padding: 14px;
    border-radius: 8px;
    margin-bottom: 28px;
    font-size: 22px;
    font-weight: 600;
}
.form-group {
    margin-bottom: 22px;
}
label {
    display: block;
    font-weight: 500;
    color: #3b82f6;
    margin-bottom: 8px;
    font-size: 15px;
}
select, input, textarea {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 14px;
    background-color: #fafbfc;
    transition: border 0.2s;
}
select:focus, input:focus, textarea:focus {
    outline: none;
    border-color: #3b82f6;
}
textarea {
    min-height: 220px;
    resize: vertical;
}
.btn-submit {
    width: 100%;
    padding: 14px;
    background-color: #3b82f6;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.2s;
}
.btn-submit:disabled {
    background-color: #94a3b8;
    cursor: not-allowed;
}
.tip-box {
    text-align: center;
    margin-top: 18px;
    font-size: 14px;
    min-height: 20px;
}
.success {
    color: #059669;
}
.error {
    color: #dc2626;
}
.dir-row {
    display: flex;
    gap: 16px;
}
.dir-row .form-group {
    flex: 1;
    margin-bottom: 0;
}
</style>
</head>
<body>
<div class="container">
    <div class="page-header">智能护宝技术库 - 新建技术笔记</div>

    <div class="form-group">
        <label>选择存储目录（自动同步仓库架构）</label>
        <div class="dir-row">
            <div class="form-group">
                <select id="firstDir">
                    <option value="">加载中...</option>
                </select>
            </div>
            <div class="form-group">
                <select id="secondDir">
                    <option value="">请先选择一级目录</option>
                </select>
            </div>
        </div>
    </div>

    <div class="form-group">
        <label>笔记标题</label>
        <input type="text" id="noteTitle" placeholder="请输入笔记标题（如：DHT11 传感器驱动开发）">
    </div>

    <div class="form-group">
        <label>笔记内容</label>
        <textarea id="noteContent" placeholder="编写技术文档、代码、踩坑记录、学习总结..."></textarea>
    </div>

    <button class="btn-submit" id="submitBtn">提交到技术库</button>
    <div class="tip-box" id="tipBox"></div>
</div>

<script>
// 你的PythonAnywhere后端地址
const API_BASE = "https://mhp.pythonanywhere.com";
const API_GET_FIRST = API_BASE + "/api/get-first-dir";
const API_GET_SECOND = API_BASE + "/api/get-contents";
const API_UPLOAD = API_BASE + "/api/upload-note";

// DOM元素
const firstDir = document.getElementById("firstDir");
const secondDir = document.getElementById("secondDir");
const noteTitle = document.getElementById("noteTitle");
const noteContent = document.getElementById("noteContent");
const submitBtn = document.getElementById("submitBtn");
const tipBox = document.getElementById("tipBox");

// 1. 加载一级目录（修复错误处理）
async function loadFirstDir() {
    try {
        const response = await fetch(API_GET_FIRST);
        if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);
        
        const data = await response.json();
        firstDir.innerHTML = "<option value=''>请选择一级分类</option>";
        
        data.data.forEach(name => {
            const option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            firstDir.appendChild(option);
        });
    } catch (error) {
        console.error("加载一级目录失败:", error);
        tipBox.textContent = "❌ 目录加载失败: " + error.message;
        tipBox.className = "tip-box error";
        firstDir.innerHTML = "<option value=''>加载失败</option>";
    }
}

// 2. 一级目录切换加载二级目录
firstDir.addEventListener("change", async function() {
    const selectedFirst = this.value;
    secondDir.innerHTML = "<option value="">加载中...</option>";

    if (!selectedFirst) {
        secondDir.innerHTML = "<option value=''>请先选择一级目录</option>";
        return;
    }

    try {
        const response = await fetch(`${API_GET_SECOND}/${encodeURIComponent(selectedFirst)}`);
        if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);
        
        const data = await response.json();
        secondDir.innerHTML = "";

        if (!data.data || data.data.length === 0) {
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "当前目录无子分类";
            secondDir.appendChild(option);
        } else {
            data.data.forEach(item => {
                if (item.type === "dir") {
                    const option = document.createElement("option");
                    option.value = item.name;
                    option.textContent = item.name;
                    secondDir.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error("加载二级目录失败:", error);
        secondDir.innerHTML = "<option value=''>加载失败</option>";
    }
});

// 3. 提交笔记
submitBtn.addEventListener("click", async function() {
    const firstVal = firstDir.value;
    const secondVal = secondDir.value;
    const titleVal = noteTitle.value.trim();
    const contentVal = noteContent.value.trim();

    if (!firstVal) {
        tipBox.textContent = "请选择一级存储目录";
        tipBox.className = "tip-box error";
        return;
    }
    if (!titleVal || !contentVal) {
        tipBox.textContent = "标题和内容不能为空";
        tipBox.className = "tip-box error";
        return;
    }

    submitBtn.disabled = true;
    tipBox.textContent = "正在提交到GitHub仓库...";
    tipBox.className = "tip-box";

    try {
        const response = await fetch(API_UPLOAD, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                first_dir: firstVal,
                second_dir: secondVal,
                title: titleVal,
                content: contentVal
            })
        });

        const result = await response.json();
        if (result.code === 200) {
            tipBox.textContent = "✅ 笔记提交成功！已同步到GitHub仓库";
            tipBox.className = "tip-box success";
            noteTitle.value = "";
            noteContent.value = "";
        } else {
            tipBox.textContent = "❌ " + result.msg;
            tipBox.className = "tip-box error";
        }
    } catch (error) {
        console.error("提交笔记失败:", error);
        tipBox.textContent = "❌ 网络异常，提交失败: " + error.message;
        tipBox.className = "tip-box error";
    } finally {
        submitBtn.disabled = false;
    }
});

// 页面加载时调用
window.onload = loadFirstDir;
</script>
</body>
</html>