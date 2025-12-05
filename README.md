# 智能流式 Panel 生成器 (FlowCyt Panel Assistant)

## 1. 项目简介

本项目是一个结合了 **确定性算法** 与 **大语言模型 (LLM)** 的智能流式细胞术 Panel 设计工具。它能够基于实验室现有的抗体库存，辅助研究人员完成从“实验设计”到“Panel 搭建”的全流程。

与传统的纯 AI 生成不同，本项目采用了 **"混合智能" (Hybrid Intelligence)** 架构：
1.  **刚性搜索 (Python):** 使用回溯算法 (Backtracking) 穷举出所有物理上可行（无通道冲突）的 Panel 候选方案，确保方案的**绝对可用性**。
2.  **柔性评估 (LLM):** 利用本地部署的大模型 (如 Qwen, Llama) 扮演“流式专家”，从亮度匹配、光谱重叠等维度对候选方案进行评分、择优，并生成圈门策略。

## 2. 核心功能

### 🧠 AI 实验设计 (Experimental Design)
*   **场景:** 当你不确定该选哪些 Marker 时。
*   **功能:** 输入实验目的（例如：“分析肿瘤浸润淋巴细胞的耗竭状态”），AI 会从库存中推荐最相关的 Marker 组合，并解释选择理由。

### 🛠️ Panel 生成与评估 (Panel Generation & Eval)
*   **硬约束搜索:** 基于库存数据，自动搜索出多个无冲突的配色方案。如果无法生成，系统会提供详细的**冲突诊断报告**（例如：“Marker A 和 B 都在争夺 PE 通道”）。
*   **AI 专家评估:** 一键让 AI 对多个候选方案进行 PK，选出亮度搭配最合理的一个。
*   **📊 光谱可视化:** 内置光谱模拟器 (Spectral Simulator)，基于高斯拟合生成 Panel 中所有染料的发射光谱图，直观展示潜在的溢漏干扰。
*   **圈门策略:** AI 自动生成配套的分级圈门 (Gating Strategy) 建议。

### 3. 如何使用

### 前提条件
1.  **环境准备:** Python 3.9+
2.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **LLM 服务配置:**
    *   项目支持 **本地 LM Studio** 或 **云端 LLM (如 OpenAI, DeepSeek)**。
    *   **云端 LLM (推荐):** 在项目根目录创建 `.env` 文件，填入以下配置：
        ```env
        OPENAI_API_BASE=https://api.example.com/v1
        OPENAI_API_KEY=sk-your-api-key
        OPENAI_MODEL_NAME=gpt-4-turbo
        ```
    *   **本地 LM Studio:** 启动 Local Server (地址 `http://127.0.0.1:1234`)，无需 `.env` 配置即可默认连接。
4.  **数据文件:** 确保 `inventory/` 文件夹下有库存 CSV 文件，根目录下有 `channel_mapping.json`, `fluorochrome_brightness.json`, `spectral_data.json`。

### 启动应用
**方式一：直接运行 (Python)**
```bash
streamlit run streamlit_app.py
```

**方式二：Docker 部署 (推荐)**
1.  构建镜像：
    ```bash
    docker build -t panel-gpt-app .
    ```
2.  运行容器：
    ```bash
    docker run -p 8501:8501 --env-file .env panel-gpt-app
    ```
浏览器访问 `http://localhost:8501` 即可。

## 4. 系统架构

本项目采用 **Search-then-Evaluate** (先搜索后评估) 模式：

### 第一阶段：确定性搜索 (Python)
*   **模块:** `panel_generator.py` -> `find_valid_panels`
*   **逻辑:**
    *   **数据聚合:** `data_preprocessing.py` 将库存清洗并按 Marker 聚合。
    *   **回溯算法:** 深度优先搜索 (DFS) 寻找所有不冲突的 System Code 组合。
    *   **冲突诊断:** 如果搜索失败，利用抽屉原理 (Pigeonhole Principle) 分析是哪些 Marker 导致了资源死锁。

### 第二阶段：智能评估 (LLM)
*   **模块:** `panel_generator.py` -> `evaluate_candidates_with_llm`
*   **逻辑:**
    *   **差异分析:** 自动识别候选方案之间的关键差异点。
    *   **Prompt 工程:** 将差异点构建为 Prompt，请求 LLM 基于“强弱搭配”原则进行选择。
    *   **结构化输出:** LLM 返回 JSON 格式的决策理由和圈门策略。

## 5. 文件结构说明

*   `streamlit_app.py`: 前端交互界面 (Tabs: 实验设计 | Panel 生成)。
*   `panel_generator.py`: 核心业务逻辑 (回溯搜索算法、LLM 调用封装)。
*   `data_preprocessing.py`: 数据清洗、别名解析 (Target Aliases)、库存加载。
*   `spectral_viewer.py`: 光谱模拟与绘图模块 (Plotly + Scipy)。
*   `llm_api_client.py`: OpenAI API 客户端封装，适配 LM Studio。
*   `channel_mapping.json`: 定义荧光素到检测通道的映射 (如 `AF488` -> `FITC`)。
*   `fluorochrome_brightness.json`: 定义荧光素的亮度等级 (1-5)。
*   `spectral_data.json`: 存储荧光素的物理参数 (Peak, Sigma)，用于模拟光谱曲线。