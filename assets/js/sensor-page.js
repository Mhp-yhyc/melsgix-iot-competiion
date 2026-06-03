// assets/js/sensor-page.js（全局保留，不用删）
document$.subscribe(() => {
  (function() {
    const rawPath = window.location.pathname;
    const path = decodeURIComponent(rawPath);
    const API_BASE = "https://mhp.pythonanywhere.com";
    const API_GET_CONTENTS = API_BASE + "/api/get-contents";

    // ========== 1）嵌入式硬件 总分类页（显示子文件夹） ==========
    if (path.includes("01-嵌入式硬件/") && !path.includes("/传感器/")) {
      console.log("✅ 全局JS：嵌入式硬件分类页");

      function renderFolders(contents) {
        const grid = document.getElementById("contentGrid");
        const loading = document.getElementById("loading");
        const empty = document.getElementById("empty");
        if (!grid) return;

        grid.innerHTML = "";
        const folders = contents.filter(item => item.type === "dir");
        if (loading) loading.style.display = "none";

        if (folders.length === 0) {
          if (empty) empty.style.display = "block";
          return;
        }
        if (empty) empty.style.display = "none";

        grid.style.display = "grid";
        folders.forEach(folder => {
          const card = document.createElement("div");
          card.className = "card";
          card.innerHTML = `
            <div class="card-icon">📁</div>
            <div class="card-title">${folder.name}</div>
            <a href="${folder.name}/" class="btn btn-primary">进入分类</a>
          `;
          grid.appendChild(card);
        });
      }

      (async () => {
        try {
          const res = await fetch(`${API_GET_CONTENTS}/01-嵌入式硬件`);
          if (!res.ok) throw new Error("请求失败");
          const data = await res.json();
          renderFolders(data.data);
        } catch (err) {
          console.error("❌ 分类页API失败：", err);
          const loading = document.getElementById("loading");
          const error = document.getElementById("error");
          if (loading) loading.style.display = "none";
          if (error) error.style.display = "block";
        }
      })();
      return;
    }

    // ========== 2）传感器 笔记页（显示.md笔记） ==========
    if (path.includes("01-嵌入式硬件/传感器/")) {
      console.log("✅ 全局JS：传感器笔记页");

      const parts = path.split('/').filter(Boolean);
      const currentDir = `${parts[1]}/${parts[2]}`;

      function renderNotes(contents) {
        const grid = document.getElementById("contentGrid");
        const loading = document.getElementById("loading");
        if (!grid) return;

        grid.innerHTML = "";
        if (loading) loading.style.display = "none";
        grid.style.display = "grid";

        // 只拿 .md 且不是 index.md
        const files = contents.filter(item =>
          item.type === "file" &&
          item.name.endsWith(".md") &&
          item.name !== "index.md"
        );

        files.forEach(file => {
          const title = file.name.replace(".md", "");
          const card = document.createElement("div");
          card.className = "card";
          card.innerHTML = `
            <div class="card-icon">📄</div>
            <div class="card-title">${title}</div>
            <div class="card-desc">传感器笔记</div>
            <div style="display:flex;gap:0.5rem;">
              <a href="${file.html_url}" target="_blank" class="btn btn-secondary">查看原文</a>
              <a href="${file.html_url.replace('/blob/','/delete/')}" target="_blank" class="btn btn-danger">删除</a>
            </div>
          `;
          grid.appendChild(card);
        });

        // 新建笔记卡片
        const newCard = document.createElement("div");
        newCard.className = "card";
        newCard.innerHTML = `
          <div class="card-icon">➕</div>
          <div class="card-title">新建传感器笔记</div>
          <div class="card-desc">点击创建</div>
          <a href="/melsgix-iot-competiion/create-note/?first_dir=01-嵌入式硬件&second_dir=传感器" class="btn btn-primary">新建笔记</a>
        `;
        grid.appendChild(newCard);
      }

      (async () => {
        try {
          const res = await fetch(`${API_GET_CONTENTS}/${currentDir}`);
          if (!res.ok) throw new Error("请求失败");
          const data = await res.json();
          renderNotes(data.data);
        } catch (err) {
          console.error("❌ 传感器页API失败：", err);
          const loading = document.getElementById("loading");
          const error = document.getElementById("error");
          if (loading) loading.style.display = "none";
          if (error) error.style.display = "block";
        }
      })();
      return;
    }

    // ========== 3）其他页面：啥也不干 ==========
    console.log("ℹ️ 全局JS：非目标页面，跳过");
  })();
});