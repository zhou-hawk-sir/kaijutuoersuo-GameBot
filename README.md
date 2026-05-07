# 🤖 开局托儿所 - 自动刷分机器人 (GameBot)

> 用魔法打败魔法！这是一个为数字消除小游戏《开局托儿所》量身定制的自动化刷分脚本。通过图像识别/大模型视觉提取游戏数据，并配合强大的“带有未来预判的二维寻路算法”，实现无情的高分收割。

## 🌟 项目亮点

*   **双引擎视觉识别**：提供了基于本地 OCR 的极速版和基于 Kimi 大模型的超高精度版。
*   **V3 竞速智能核心**：
    *   **二维视野寻路 (2D Bounding Box Search)**：打破常规的单线消除，完美识别 2x2, 2x3 等所有矩阵组合。
    *   **一步未来预判 (1-Step Lookahead AI)**：不再采用短视的“贪心算法”。程序在每次消除前，会在内存中平行推演所有走法，选择**留下后路最多、消耗方块最少**的最优解。
    *   **极限 0 值剪枝 (Pruning)**：通过对空白格的精准过滤，将 AI 的矩阵穷举运算速度提升 10 倍以上。
*   **防脱节机制**：模拟真实物理鼠标拖拽，解除系统隐藏限速，达到“手速与脑力”的巅峰配合。

## 🛠️ 技术栈 (Tech Stack)

*   **编程语言**：Python 3.x
*   **自动化控制**：`PyAutoGUI` (模拟鼠标无延迟滑动)
*   **图像处理**：`Pillow (PIL)` (屏幕截取、灰度转换、图片放大、Lanczos平滑、二值化去噪、Padding加白边)
*   **视觉识别 (main1)**：`pytesseract` (Tesseract-OCR 本地光学字符识别)
*   **大模型视觉 (main2)**：`openai` SDK (对接 Moonshot Kimi `moonshot-v1-8k-vision-preview` 多模态视觉模型)

---

## 📂 版本说明与目录结构

本项目包含两个独立的主程序文件，供不同需求的玩家选择：

*   `main1.py` **(本地 OCR 极速版)**：
    *   **原理**：将棋盘切割为 160 张小图，通过 OpenCV/PIL 进行图像增强（放大3倍 + 二值化 + 15px白边）后，送入本地 Tesseract 引擎识别。
    *   **优点**：完全免费，无需联网，识别与计算速度极快。
*   `main2.py` **(Kimi 大模型天眼版)** 🏆 推荐：
    *   **原理**：直接截取游戏全图转为 Base64，通过 API 喂给 Kimi 的原生视觉大模型，让大模型直接输出 16x10 的 Python 二维数组。
    *   **优点**：准确率碾压传统 OCR，无视游戏背景干扰，容错率极高，代码极其简洁。

---

## 🚀 快速开始 (Getting Started)

### 1. 环境准备
建议使用 Conda 创建独立环境：
```bash
conda create -n gamebot python=3.9
conda activate gamebot
```

安装所需依赖：
```bash
pip install pyautogui pillow pytesseract openai opencv-python numpy mss
```

### 2. 安装 Tesseract-OCR (仅运行 main1.py 需要)
前往 Tesseract GitHub 下载并安装 64位 Windows 版本。
记住安装路径（默认一般为 `C:\Program Files\Tesseract-OCR\tesseract.exe`）。

### 3. 配置游戏坐标 (极其重要)
由于每个人的电脑屏幕分辨率和游戏窗口位置不同，直接运行代码会导致鼠标乱飞。
将游戏画面打开并固定在屏幕上。
可以运行get_pos.py按照提示获取游戏界面位置坐标
修改代码顶部的坐标配置：

```python
# 左上角第一个数字(行1列1)的中心点坐标
START_X, START_Y = 1458, 254
# 右下角最后一个数字(行16列10)的中心点坐标
END_X, END_Y = 1856, 913
```

### 4. 运行脚本

#### 若运行 main1.py：
请确保代码中 `pytesseract.pytesseract.tesseract_cmd` 指向了你正确的本地安装路径。

```bash
python main1.py
```

#### 若运行 main2.py：
请前往 Moonshot 开放平台 申请 API Key，并填入代码中：

```python
KIMI_API_KEY = "sk-你的API密钥"
```

```bash
python main2.py
```

运行后，切回游戏界面，双手离开键盘鼠标，欣赏 AI 的极致表演即可！🎉

---

## 🧠 算法核心逻辑展示

为了防止 AI 陷入死胡同，本项目放弃了传统的贪心算法，加入了基于 DFS 思想的一步预判：

```python
# 核心 AI 决策片段
for move in moves:
    # 1. 内存中虚拟克隆棋盘
    temp_board = copy.deepcopy(board)
    # 2. 模拟消除动作
    eliminate(temp_board, move)
    # 3. 预判未来：计算消除后剩下的合法走法数量
    future_moves_count = len(find_all_2d_moves(temp_board))
    
    # 4. 择优录取：优先选择留下后路最多、消耗方块最少的解法
    if future_moves_count > max_future_moves:
        best_move = move
        max_future_moves = future_moves_count
```

---

## 🔒 开发者安全规范

如果你要 fork 本项目或在本地使用 main2.py，请务必保护好你的 API Key！
严禁将带有真实 `sk-xxx` 密钥的代码 commit 到公共仓库中，以免造成额度盗刷。建议使用环境变量 `os.environ.get("KIMI_API_KEY")` 的方式进行配置。

---

## � 免责声明

本项目仅供 Python 自动化编程、机器视觉及大模型 API 对接的学习与研究使用。请勿用于商业用途或破坏游戏公平性。
