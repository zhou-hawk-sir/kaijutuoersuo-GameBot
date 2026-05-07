import pyautogui
import copy
import time
import base64
import ast
import re
from io import BytesIO
from PIL import ImageGrab
from openai import OpenAI

# ================= 配置区域 =================
# 1. 填写你的坐标
START_X, START_Y = 1458, 254  
END_X, END_Y = 1856, 913      

# 2. 游戏行列数
COLS, ROWS = 10, 16

# 3. Kimi (Moonshot) API 配置
KIMI_API_KEY = "your_api_key"
# ==========================================

# 计算每个格子的步长
STEP_X = (END_X - START_X) / (COLS - 1) if COLS > 1 else 0
STEP_Y = (END_Y - START_Y) / (ROWS - 1) if ROWS > 1 else 0

def get_grid_centers():
    """计算所有 160 个格子的中心点坐标（用于鼠标点击）"""
    centers = []
    for r in range(ROWS):
        row_centers = []
        for c in range(COLS):
            x = int(START_X + c * STEP_X)
            y = int(START_Y + r * STEP_Y)
            row_centers.append((x, y))
        centers.append(row_centers)
    return centers

def read_board_with_kimi():
    """【Kimi 纯正视觉模型版】使用专门的 Vision 模型解析图像"""
    print("正在截取全局棋盘并呼叫 Kimi 视觉大模型...")
    
    # 1. 截取整个棋盘的图片 
    margin_x = int(STEP_X * 0.5)
    margin_y = int(STEP_Y * 0.5)
    bbox = (START_X - margin_x, START_Y - margin_y, END_X + margin_x, END_Y + margin_y)
    
    screen = ImageGrab.grab(bbox)
    screen.save("kimi_vision_debug.png")
    print("-> 棋盘截图已保存为 kimi_vision_debug.png")

    # 2. 将图片转换为 Base64 格式
    buffered = BytesIO()
    screen.save(buffered, format="PNG")
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 3. 初始化 Kimi 客户端
    client = OpenAI(
        api_key=KIMI_API_KEY,
        base_url="https://api.moonshot.cn/v1",
    )

    try:
        print("-> 正在将图片喂给 moonshot-v1-8k-vision-preview 视觉大模型...")
        response = client.chat.completions.create(
            model="moonshot-v1-8k-vision-preview", # 🚀 关键点：必须使用 Kimi 的专门视觉模型！
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "这是一张游戏截图，包含一个正好 16行、10列 的数字矩阵。请极其精确地识别图中的所有数字，并输出为一个 16x10 的 Python 二维列表。格式必须严格为：[[x,x...], [x,x...], ...]。一共16行，每行10个数字。只输出纯净的Python列表代码，不要加 ```python 的 markdown 标记，不要任何解释。"
                        },
                        {
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            temperature=0.0, # 必须为 0，防止大模型胡乱联想
        )
        
        # 4. 解析 Kimi 的返回结果
        result_str = response.choices[0].message.content
        print("\n--- Kimi 返回原始数据 ---")
        print(result_str)
        print("-------------------------\n")
        
        # 用正则表达式提取纯数组部分
        match = re.search(r'\[\s*\[.*?\]\s*\]', result_str, re.DOTALL)
        if match:
            clean_list_str = match.group(0)
            board = ast.literal_eval(clean_list_str)
            
            # 严谨校验行列数
            if len(board) == ROWS and len(board[0]) == COLS:
                print("✅ Kimi 识别成功且格式校验完美通过！")
                return board
            else:
                raise ValueError(f"大模型数错行了: 识别到 {len(board)}行, {len(board[0]) if len(board)>0 else 0}列")
        else:
            raise ValueError("未能从 Kimi 返回结果中提取出合法的 Python 列表。")
            
    except Exception as e:
        print(f"❌ Kimi 视觉 API 识别失败: {e}")
        exit(1)

def drag_and_eliminate(x1, y1, x2, y2):
    """【物理鼠标】"""
    pyautogui.moveTo(x1, y1)
    pyautogui.dragTo(x2, y2, duration=0.2)
    time.sleep(0.1)

def find_all_2d_moves(board):
    """【剪枝算法】"""
    moves = []
    for r1 in range(ROWS):
        for c1 in range(COLS):
            if board[r1][c1] == 0:
                continue 
            for r2 in range(r1, ROWS):
                for c2 in range(c1, COLS):
                    if board[r2][c2] == 0:
                        continue
                    current_sum = 0
                    for i in range(r1, r2 + 1):
                        for j in range(c1, c2 + 1):
                            current_sum += board[i][j]
                    if current_sum == 10:
                        moves.append((r1, c1, r2, c2))
                    elif current_sum > 10:
                        break 
    return moves

def solve_game(board, centers):
    """【大模型加持版 V3 竞速核心】"""
    print("========== 启动大模型加持 V3 竞速核心 ==========")
    pyautogui.PAUSE = 0 
    score = 0
    
    while True:
        moves = find_all_2d_moves(board)
        if not moves:
            print(f"\n[游戏结束] 棋盘无解！本次机器共计狂刷 {score} 分。")
            break
            
        best_move = None
        max_future_moves = -1
        min_area = 999 
        
        for move in moves:
            r1, c1, r2, c2 = move
            temp_board = copy.deepcopy(board)
            for i in range(r1, r2 + 1):
                for j in range(c1, c2 + 1):
                    temp_board[i][j] = 0
            
            future_moves_count = len(find_all_2d_moves(temp_board))
            area = (r2 - r1 + 1) * (c2 - c1 + 1)
            
            if future_moves_count > max_future_moves:
                max_future_moves = future_moves_count
                min_area = area
                best_move = move
            elif future_moves_count == max_future_moves:
                if area < min_area:
                    min_area = area
                    best_move = move
        
        r1, c1, r2, c2 = best_move
        x1, y1 = centers[r1][c1]
        x2, y2 = centers[r2][c2]
        
        drag_and_eliminate(x1, y1, x2, y2)
        
        for i in range(r1, r2 + 1):
            for j in range(c1, c2 + 1):
                board[i][j] = 0
                
        score += 1
        print(f"得分 +1 | 消除矩阵: ({r1},{c1}) 到 ({r2},{c2}) | 预判后路 {max_future_moves} 种 | 消耗方块 {min_area} 个")

if __name__ == "__main__":
    centers = get_grid_centers()
    
    # 核心变动：用 Kimi 替代了 Tesseract
    board = read_board_with_kimi()
    
    print("\n----- Kimi 确认的初始战局 -----")
    for row in board:
        print(row)
    print("--------------------------------\n")
    
    time.sleep(2) # 给你2秒钟切回游戏界面
    
    solve_game(board, centers)
