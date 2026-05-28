$folders = @(
    "01-嵌入式硬件/传感器",
    "01-嵌入式硬件/通信协议",
    "01-嵌入式硬件/电源管理",
    "02-嵌入式软件/FreeRTOS",
    "02-嵌入式软件/驱动开发",
    "03-AI与算法/TinyML",
    "03-AI与算法/信号处理",
    "04-云端与后端/物联网平台",
    "04-云端与后端/MQTT协议",
    "05-前端与可视化/Web仪表盘",
    "05-前端与可视化/3D数字孪生",
    "06-调试与问题库",
    "07-项目管理"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force
    $title = ($folder -split '/')[-1]
    Set-Content -Path "$folder/index.md" -Value "# $title`n`n内容待补充"
}

Write-Host "完成！所有目录和占位文件已创建。"