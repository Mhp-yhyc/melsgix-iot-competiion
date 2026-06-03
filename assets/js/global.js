// 全局JS：兼容无刷新导航的终极方案
(function() {
    // 🔒 核心1：页面类型检测（只在对应页面执行对应代码）
    function getPageType() {
        const path = window.location.pathname;
        if (path.includes('/01-嵌入式硬件/传感器/')) return 'sensor';
        if (path.includes('/create-note/')) return 'create-note';
        return 'other'; // 其他页面
    }

    // 🔒 核心2：传感器页面专用逻辑（带DOM存在性检查）
    function initSensorPage() {
        // 先检查DOM元素是否存在，避免报错阻塞
        const grid = document.getElementById("contentGrid");
        const loading = document.getElementById("loading");
        const error = document.getElementById("error");
        const errorText = document.getElementById("errorText");

        if (!grid || !loading || !error || !errorText) {
            console.log("非传感器页面，跳过传感器逻辑");
            return; // 元素不存在，直接退出，不影响其他页面
        }

        // 👇 以下是原传感器页面功能代码（保留不变）👇
        const apiBase = "https://mhp.pythonanywhere.com";
        const apiGetContents = apiBase + "/api/get-contents";
        const fetchTimeout = 5000;
        const currentDir = "01-嵌入式硬件/传感器";

        // 带超时的fetch请求
        async function fetchWithTimeout(url, timeout) {
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);
            try {
                const response = await fetch(url, { signal: controller.signal });
                clearTimeout(id);
                return response;
            } catch (err) {
                clearTimeout(id);
                throw err;
            }
        }

        // 渲染笔记卡片
        function renderContents(contents) {
            loading.style.display = "none";
            error.style.display = "none";
            grid.style.display = "grid";

            // 过滤有效笔记文件
            const files = contents.filter(item => 
                item.type === "file" && 
                item.name.endsWith(".md") && 
                item.name !== "index.md"
            );

            // 渲染笔记卡片
            files.forEach(file => {
                const noteTitle = file.name.replace(".md", "");
                const card = document.createElement("div");
                card.className = "card";
                card.innerHTML = `
                    <div class="card-icon">📄</div>
                    <div class="card-title">${noteTitle}</div>
                    <div class="card-desc">传感器分类 · 笔记文件</div>
                    <div style="display: flex; gap: 0.5rem;">
                        <a href="${file.html_url}" target="_blank" class="btn btn-secondary">查看原文</a>
                        <a href="${file.html_url.replace('/blob/', '/delete/')}" target="_blank" class="btn btn-danger">删除笔记</a>
                    </div>
                `;
                grid.appendChild(card);
            });

            // 新建笔记卡片（关键：添加data-md-skip="true"）
            const newCard = document.createElement("div");
            newCard.className = "card";
            newCard.innerHTML = `
                <div class="card-icon">➕</div>
                <div class="card-title">新建传感器笔记</div>
                <div class="card-desc">点击创建新笔记</div>
                <div style="display: flex; gap: 0.5rem;">
                    <a href="../../create-note/?first_dir=01-嵌入式硬件&second_dir=传感器" 
                       class="btn btn-primary" 
                       data-md-skip="true">新建笔记</a>
                </div>
            `;
            grid.appendChild(newCard);
        }

        // 主逻辑
        async function init() {
            try {
                const apiUrl = `${apiGetContents}/${currentDir}`;
                const res = await fetchWithTimeout(apiUrl, fetchTimeout);
                if (!res.ok) throw new Error(`请求失败（状态码：${res.status}）`);
                const data = await res.json();
                if (!data || !data.data) throw new Error("API返回数据格式错误");
                renderContents(data.data);
            } catch (err) {
                console.error("加载错误:", err);
                loading.style.display = "none";
                error.style.display = "block";
                errorText.textContent = `加载失败：${err.message}`;
            }
        }

        init();
    }

    // 🔒 核心3：监听无刷新导航事件（页面切换时重新初始化）
    function bindInstantNavigationEvents() {
        // 页面加载完成时初始化
        document.addEventListener('DOMContentLoaded', function() {
            initCurrentPage();
        });

        // 无刷新导航完成后重新初始化
        document.addEventListener('DOMContentLoaded', function() {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.target.id === 'main') {
                        initCurrentPage();
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    }

    // 初始化当前页面
    function initCurrentPage() {
        const pageType = getPageType();
        switch (pageType) {
            case 'sensor':
                initSensorPage();
                break;
            case 'create-note':
                // 新建笔记页面逻辑（如果有的话）
                break;
            default:
                // 其他页面不执行传感器逻辑
                break;
        }
    }

    // 启动全局逻辑
    bindInstantNavigationEvents();
})();