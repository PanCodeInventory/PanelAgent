# 智能流式 Panel 生成器 (FlowCyt LLM-Agent)

## 1. 项目简介

本项目旨在自动化多色流式细胞术 Panel 的设计过程。通过结合实验室的抗体库存信息和本地部署的大语言模型（LLM），本工具能够根据用户输入的 Markers 自动生成优化的 Panel 方案，并提供详细的溢漏补偿建议和设计理由。项目目标是解决人工设计 Panel 耗时、易错、易导致库存浪费以及知识门槛高的问题。

## 2. 如何使用

### 前提条件
1.  **LM Studio:** 确保已安装并运行 [LM Studio](https://lmstudio.ai/)。
2.  **LLM 模型:** 在 LM Studio 中下载并加载一个兼容 OpenAI API 的 GGUF 模型，例如 `GPT-OSS-20B` 。确保 LM Studio 的本地推理服务器正在运行在 `http://127.0.0.1:1234`。
3.  **Python 环境:** 确保您的环境中安装了 Python 3.9+。
4.  **Python 依赖:** 安装项目所需的 Python 库：
    ```bash
    pip install pandas streamlit openai
    ```
5.  **抗体库存文件:** 确保 `流式抗体库-20250625小鼠.csv` 文件存在于项目根目录。
6.  **通道映射文件:** 确保 `channel_mapping.json` 文件存在于项目根目录。

### 启动应用
1.  在终端中，导航到项目根目录。
2.  运行 Streamlit 应用：
    ```bash
    streamlit run streamlit_app.py
    ```
3.  应用程序将在您的默认网页浏览器中打开。

### 使用界面
*   在网页界面的输入框中，输入您希望检测的 Markers (例如: `CD4, CD8, CD3`)，使用逗号分隔。
*   点击 "生成 Panel" 按钮。
*   系统将显示生成的 Panel 详情，包括抗体信息、溢漏补偿建议和 Panel 设计理由。

## 3. 框架概述 ("三明治" 架构)

本项目采用 **Python (数据预处理) - LLM (核心决策) - Python (校验与反馈)** 的三层架构，也称作“三明治”架构：

*   **数据准备层 (L1 - Python):**
    *   `data_preprocessing.py`: 负责加载 `流式抗体库-20250625小鼠.csv`。
    *   `channel_mapping.json`: 存储荧光通道的标准化映射。
    *   对用户输入的 Markers 和抗体库存中的 Target 进行标准化处理，以提高匹配度（例如，将 `NK1.1` 匹配到 `NK-1.1`，`CD8` 匹配到 `CD8a`）。
    *   根据用户 Markers 过滤相关抗体，减少发送给 LLM 的 Prompt 长度。

*   **核心决策层 (L2 - LLM via LM Studio):**
    *   `llm_api_client.py`: 负责与本地 LM Studio 服务（LLM）进行通信。
    *   大语言模型接收处理过的库存信息和用户 Markers。
    *   **两阶段 LLM 交互:**
        1.  **初始选择:** LLM 推荐 Markers 对应的荧光抗体组合（例如 `CD4:FITC`），以简化、可控的格式返回。
        2.  **详细反馈:** LLM 接收最终验证过的 Panel，作为流式专家提供详细的溢漏补偿建议和 Panel 设计理由。

*   **校验与执行层 (L3 - Python):**
    *   `panel_generator.py`: 协调整个流程。
    *   根据 LLM 的选择结果，从原始库存中查找完整的抗体信息（包括 Brand, Catalog Number 等）。
    *   严格执行“System_Code 唯一性”等物理规则，确保生成的 Panel 合规。
    *   调用 LLM 获取详细的补偿建议和设计理由。
    *   `streamlit_app.py`: 提供直观的用户界面，展示 Panel、补偿建议和设计理由。

## 4. 当前开发进度

*   **核心功能:** 已实现根据用户 Markers 智能生成 Panel，并从本地 LLM 获取补偿建议和设计理由。
*   **数据预处理:** 完成抗体库存 CSV 加载、荧光通道标准化映射 (`channel_mapping.json`)。
*   **Marker 名称标准化:** 解决了用户输入与库存中 Marker 名称不一致的问题（如 `CD8` vs `CD8a`, `NK1.1` vs `NK-1.1`）。
*   **LLM 交互:** 实现了与 LM Studio 部署的 LLM 的稳定通信，并采用两阶段交互策略，提高输出的可靠性。
*   **健壮性:** 增强了对 LLM 输出格式变化的容错处理能力。
*   **用户界面:** 开发了基于 Streamlit 的交互式界面，用于输入 Markers 和展示结果，包括 Panel 详情、溢漏补偿建议和 Panel 设计理由。

目前项目已达到功能完善阶段，可以根据用户需求生成、分析并展示流式 Panel。
