
# 项目设计文档：智能流式 Panel 生成器 (FlowCyt LLM-Agent)

**版本：** 1.1 (Environment Update)
**核心模型：** GPT-OSS-20B (运行于 LM Studio)
**API 端点：** `http://127.0.0.1:1234`
**适用场景：** 实验室内部抗体库存管理与多色流式方案自动设计

-----

## 1\. 项目背景与目标

### 1.1 痛点

  * **人工耗时：** 设计多色 Panel 需要同时查阅库存、抗原密度、光谱重叠和仪器配置，耗时且易错。
  * **库存浪费：** 往往忽略库存量（Quantity），导致过期或死库存堆积。
  * **知识门槛：** 新手难以掌握“弱抗原配强荧光”等配色原则。

### 1.2 目标

构建一个自动化工具，用户输入实验目的（如“检测小鼠 Treg”），系统基于**实验室真实库存 CSV**，利用本地部署的 **GPT-OSS-20B** 进行逻辑决策，自动生成符合物理规则的最优 Panel。

-----

## 2\. 系统核心架构 (The "Sandwich" Architecture)

采用 **Python (预处理) - LLM (决策) - Python (校验)** 的三层架构。利用 LM Studio 作为推理服务器，Python 通过 API 接口与其交互。

| 层级 | 模块名称 | 职责 | 关键技术/数据 |
| :--- | :--- | :--- | :--- |
| **L1: 数据准备层** | **Python预处理器** | **“翻译官”**：读取 CSV，清洗别名，将商标名映射为物理通道 ID (System\_Code)。 | `Pandas`, `JSON Mapping` |
| **L2: 核心决策层** | **GPT-OSS-20B (LM Studio)** | **“战术指挥”**：通过 HTTP API 接收请求。基于抗原强弱和库存量进行逻辑连线。 | `LM Studio Server`, `OpenAI SDK` |
| **L3: 校验执行层** | **Python 裁判** | **“物理否决”**：检查光谱重叠、通道冲突，并生成最终表格。 | `Spectral Matrix`, `Rule Engine` |

-----

## 3\. 详细功能模块设计

### 3.1 模块 A：数据标准化 (Data Normalization)

*不依赖 LLM，完全由 Python 处理。*

  * **输入：** `流式抗体库-20250625小鼠.csv`
  * **核心动作：**
    1.  **加载映射表：** 读取 `channel_mapping.json` (如 `APC/Fire™ 750` -\> `ID: RED_780`)。
    2.  **生成增强数据：** 遍历 CSV，为每一行抗体添加 `System_Code` (物理通道) 和 `Brightness_Level` (亮度)。
  * **目的：** 消除模型对商业名称的理解偏差，让 GPT-OSS-20B 专注于逻辑匹配。

### 3.2 模块 B：决策引擎 (Strategy Engine)

  * **运行环境：** 本地 LM Studio (`http://127.0.0.1:1234`)
  * **Prompt 策略：**
      * **角色设定：** 流式细胞术专家。
      * **输入内容：** 用户需求 Markers + **经过清洗并带有 System\_Code 的库存列表**。
      * **核心指令：**
        > "请从库存中选择抗体。必须遵守：1. 若库存量(Quantity) \< 2，尽量不选。2. **System\_Code 绝对不能重复**。3. 弱抗原优先匹配高亮度荧光。"
  * **输出：** JSON 格式的初步方案。

### 3.3 模块 C：物理裁判 (The Referee)

  * **运行环境：** Python 本地脚本
  * **核心动作：**
      * 解析 GPT-OSS-20B 返回的 JSON。
      * **硬约束检查：** 如果 JSON 中存在两个抗体的 `System_Code` 相同，直接判定失败。
      * **光谱检查：** (进阶) 查阅光谱重叠矩阵，计算干扰指数。若过高，自动生成“修正指令”反馈给 LLM 重试。

-----

## 4\. 技术栈选型与配置 (关键更新)

### 4.1 大语言模型 (Server 端)

  * **模型：** `gpt-oss-20b` (或其他在 LM Studio 中加载的 GGUF 模型)
  * **部署工具：** LM Studio
  * **服务地址：** `http://127.0.0.1:1234`
  * **兼容性：** 完全兼容 OpenAI Chat Completion API 格式。

### 4.2 后端开发 (Client 端)

  * **语言：** Python 3.10+
  * **核心库：**
      * `openai`: 用于连接 LM Studio。
      * `pandas`: 处理 CSV。
      * `streamlit`: 前端界面。

### 4.3 连接代码示例 (Python)

由于 LM Studio 模拟了 OpenAI 的接口，你可以直接使用 `openai` 官方库，只需修改 `base_url`。

```python
from openai import OpenAI
import pandas as pd

# 配置连接到本地 LM Studio
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",  # 指向 LM Studio
    api_key="lm-studio"  # LM Studio 通常不需要 Key，但这行必须填占位符
)

def consult_gpt_oss(prompt):
    """
    发送请求给本地的 GPT-OSS-20B
    """
    try:
        response = client.chat.completions.create(
            model="gpt-oss-20b",  # 这里的名字其实不重要，LM Studio 会用当前加载的模型
            messages=[
                {"role": "system", "content": "你是一个流式细胞术专家，请以 JSON 格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # 低温度保证逻辑稳定性
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"连接错误: {e}"

# 测试连接
# print(consult_gpt_oss("你好，请做个自我介绍"))
```

-----

## 5\. 项目实施路线图 (Roadmap)

### 第一阶段：数据治理 (本周重点)

  * [ ] **任务 1：** 编写 Python 脚本，加载您的 `流式抗体库-20250625小鼠.csv`。
  * [ ] **任务 2：** 建立 `channel_mapping.json`。重点解决 `APC/Fire™ 750` 与 `APC-Cy7` 的归一化。

### 第二阶段：连接与调试

  * [ ] **任务 3：** 启动 LM Studio，加载 `gpt-oss-20b`，开启 Server 模式。
  * [ ] **任务 4：** 运行上述 Python 代码片段，测试 Python 能否成功从 LM Studio 获取回复。

### 第三阶段：核心逻辑集成

  * [ ] **任务 5：** 将处理后的 CSV 数据嵌入 Prompt，发送给 GPT-OSS-20B，测试其是否遵守“通道唯一性”规则。
  * [ ] **任务 6：** 开发 Streamlit 界面，将输入框和输出表格可视化。

-----

## 6\. 风险与注意事项

1.  **Context Window (上下文窗口) 限制：**

      * 虽然 GPT-OSS-20B 性能不错，但如果您的 CSV 库存有几千行，直接全部塞进 Prompt 可能会通过 Context 长度限制（或者导致模型遗忘）。
      * **对策：** 在 Python 侧先根据用户输入的 Markers 做一步 `Filter` (筛选)，只把相关的抗体（例如：用户查 CD4，只把库存里的 CD4 相关行喂给模型，不要把 CD8 的库存也喂进去）。

2.  **模型推理速度：**

      * 20B 参数的模型在本地运行需要一定的显存和计算时间。
      * **对策：** 在 Streamlit 界面上增加“生成中...”的进度条，避免用户以为程序卡死。

3.  **JSON 格式稳定性：**

      * 本地模型偶尔会输出不完美的 JSON（比如少个括号）。
      * **对策：** 在 Python 中使用 `try...except json.JSONDecodeError` 进行捕获，如果解析失败，自动让模型重试一次。

-----

## 目前遇到的技术挑战：
1. 数据库的匹配问题：同一个抗原有多种注释，需要做一个dic来去完成准确的映射
2. 抗原选择的荧光泄露问题：更强调一下匹配的问题


1. 写一个染料的特性库
2. 