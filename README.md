# FilmLens AI 🎬 (学术级拉片辅助引擎)

**FilmLens AI** 是一款专为电影学者、学生及影评人设计的深度“拉片”工具。它结合了最新的 **Google Gemini 多模态大模型** 与 **学术文献检索技术**，能够将长达数小时的电影自动切分为独立镜头，并生成视听语言解析与学术互文报告。

---

## 🔥 核心特性

- **长片高效支持**：针对 2 小时+ 电影进行了深度优化，支持长片镜头并行分析。
- **AI 视听语言解析**：自动识别景别（Shot Scale）、运镜（Movement）、角度（Angle）、光影（Lighting）及导演作者风格（Auteur Style）。
- **学术互文图谱**：实时对接 **Semantic Scholar**、**SerpApi** 等学术数据库，自动匹配电影理论文献。
- **持久化分析报告**：所有分析结果自动保存为 `analysis.json`，支持任务重载与随时复盘，避免重复扣费。
- **Premium 设计**：精心构建的多分栏协作工作台，支持时间轴联动与实时 AI 对话。

---

## 🛡️ 隐私与安全说明 (GitHub 必读)

1.  **API Key 安全**：本项目已配置 `.gitignore` 自动忽略 `.env` 文件。**请永远不要将包含真实 Key 的 `.env` 推送到 GitHub。**
2.  **大文件过滤**：由于电影文件体积巨大（通常 > 1GB），项目已自动忽略 `/static/jobs/` 下的所有视频、帧图片及分析缓存，确保仓库整洁且符合 GitHub 上传限制。

---

## 🛠️ 环境准备

- **Python 3.10+** (后端 API)
- **Node.js 18+** (Next.js 前端)
- **Redis** (核心：用于 WebSocket 事件推送与数据缓存)
- **FFmpeg** (**必须安装**：用于视频、关键帧处理)

---

## 📦 安装与配置

### 1. 配置环境参数
在根目录下新建 `.env` 文件，填入：
```bash
# Google Gemini API Key (必须)
LLM_API_KEY="AIza..."
LLM_MODEL="gemini-2.0-flash"

# Redis 配置
REDIS_URL="redis://localhost:6379"

# 学术检索 API (可选)
SEMANTIC_SCHOLAR_API_KEY="..."
SERPAPI_API_KEY="..."
```

### 2. 后端安装
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 前端安装
```bash
npm install
```

---

## 🏃 运行程序

1.  **启动后端**：`python -m backend.main` (默认 8000 端口)
2.  **启动前端**：`npm run dev` (默认 3000 端口)

---

## 💡 特殊技巧：手动导入超长电影 (Import Hack)

如果你的计算机性能不足以支持 2 小时电影的**即时转码与切片**，可以参考以下步骤在其他高性能机器操作后导入：

1.  在高性能机器完成分析后，将对应的 `jobs/{uuid}/` 文件夹整体拷贝到本机 `static/jobs/` 下。
2.  确保文件夹内包含 `video.mp4`、`analysis.json` 和 `frames/` 目录。
3.  **无需重新上传**，直接在浏览器访问：`http://localhost:3000/analyze/{uuid}`。
4.  系统将自动检测现有数据，**秒级加载**全片分析结果。

---

## 📜 开源协议
MIT License. 共同推动电影研究数字化！
