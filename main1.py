import pyautogui
import pytesseract
from PIL import Image, ImageGrab, ImageDraw, ImageOps  # <--- 确保导入了 ImageOps 和 Image
import copy
import time
import os

# ================= 配置区域 =================
# 1. 填写刚才用 get_pos.py 获取的坐标
# 左上角第一个格子的中心点坐标
START_X, START_Y = 1458, 254  # <--- 请替换为你的实际坐标
# 右下角最后一个格子的中心点坐标
END_X, END_Y = 1856, 913      # <--- 请替换为你的实际坐标

# 2. Tesseract 安装路径
pytesseract.pytesseract.tesseract_cmd = r'E:\Tesseract-OCR\tesseract.exe'

# 3. 游戏行列数
COLS, ROWS = 10, 16
# ==========================================

# 计算每个格子的步长
STEP_X = (END_X - START_X) / (COLS - 1) if COLS > 1 else 0
STEP_Y = (END_Y - START_Y) / (ROWS - 1) if ROWS > 1 else 0

def get_grid_centers():
    """计算所有 160 个格子的中心点坐标"""
    centers = []
    for r in range(ROWS):
        row_centers = []
        for c in range(COLS):
            x = int(START_X + c * STEP_X)
            y = int(START_Y + r * STEP_Y)
            row_centers.append((x, y))
        centers.append(row_centers)
    return centers

def read_board(centers):
    """【高精度OCR版】截屏、放大3倍、加15px白边、二值化处理"""
    print("正在截屏并高精度识别数字...")
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    
    # 创建保存小图的文件夹
    save_dir = "debug_crops"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    screen = ImageGrab.grab()
    
    # 复制一份全屏图像用来画红框
    debug_screen = screen.copy()
    draw = ImageDraw.Draw(debug_screen)
    
    # 裁剪大小 (以中心点向外扩展的半边长)
    box_size = int(STEP_X * 0.30)  # 稍微缩小框，确保绝不切到周围的白框
    
    for r in range(ROWS):
        for c in range(COLS):
            cx, cy = centers[r][c]
            left, top = cx - box_size, cy - box_size
            right, bottom = cx + box_size, cy + box_size
            bbox = (left, top, right, bottom)
            
            # 画红框辅助调试
            draw.rectangle(bbox, outline="red", width=2)
            
            # 裁剪小图
            cell_img = screen.crop(bbox)
            
            # ----------------- 图像增强流水线 -----------------
            # 1. 转为灰度图
            cell_img = cell_img.convert("L") 
            
            # 2. 放大 3 倍 (在二值化前放大，边缘会更平滑)
            width, height = cell_img.size
            cell_img = cell_img.resize((width * 3, height * 3), resample=Image.Resampling.LANCZOS)
            
            # 3. 强力二值化：阈值160 (150-170之间微调)
            cell_img = cell_img.point(lambda x: 0 if x < 120 else 255, '1') 
            
            # 4. 加 15 像素纯白边框 (Tesseract 识别单字符的关键)
            cell_img = ImageOps.expand(cell_img, border=15, fill='white')
            # --------------------------------------------------
            
            # 保存查看
            img_name = f"r{r}_c{c}.png"
            cell_img.save(os.path.join(save_dir, img_name))
            
            # 识别
            custom_config = r'--oem 3 --psm 10 -c tessedit_char_whitelist=123456789'
            text = pytesseract.image_to_string(cell_img, config=custom_config).strip()
            
            if text.isdigit():
                board[r][c] = int(text)
            else:
                board[r][c] = 0
                
    # 保存画了红框的全图
    debug_screen.save("debug_full_screen.png")
    print(f"-> 调试全图已保存至: debug_full_screen.png")
    print(f"-> 160张数字截图已保存至文件夹: {save_dir}/")
    print("数字识别完成！")
    return board

def drag_and_eliminate(x1, y1, x2, y2):
    """【极速物理鼠标】"""
    pyautogui.moveTo(x1, y1)
    pyautogui.dragTo(x2, y2, duration=0.2)
    time.sleep(0.1) # 消除动画缓冲

def find_all_2d_moves(board):
    """【极限剪枝】找出当前所有满足和为 10 的矩形区域 (1D 和 2D)"""
    moves = []
    for r1 in range(ROWS):
        for c1 in range(COLS):
            # 🚀 剪枝 1：如果起点已经被消除(为0)，直接跳过
            if board[r1][c1] == 0:
                continue 
                
            for r2 in range(r1, ROWS):
                for c2 in range(c1, COLS):
                    # 🚀 剪枝 2：如果终点已经被消除(为0)，直接跳过
                    if board[r2][c2] == 0:
                        continue
                        
                    # 计算矩形总和
                    current_sum = 0
                    for i in range(r1, r2 + 1):
                        for j in range(c1, c2 + 1):
                            current_sum += board[i][j]
                    
                    if current_sum == 10:
                        moves.append((r1, c1, r2, c2))
                    elif current_sum > 10:
                        # 🚀 剪枝 3：矩阵内部正数和已超10，没必要继续向右延伸了
                        break 
    return moves

def solve_game(board, centers):
    """【V3 竞速核心】面积惩罚 + 极速鼠标动作 + 自动解限速"""
    print("========== 启动 V3 竞速智能核心 ==========")
    
    # 解除 pyautogui 默认延迟
    pyautogui.PAUSE = 0 
    score = 0
    
    while True:
        moves = find_all_2d_moves(board)
        
        if not moves:
            print(f"\n[游戏结束] 棋盘无解！本次机器共计狂刷 {score} 分。")
            break
            
        best_move = None
        max_future_moves = -1
        min_area = 999  # 用于记录当前步占用的方块数量
        
        for move in moves:
            r1, c1, r2, c2 = move
            temp_board = copy.deepcopy(board)
            for i in range(r1, r2 + 1):
                for j in range(c1, c2 + 1):
                    temp_board[i][j] = 0
            
            future_moves_count = len(find_all_2d_moves(temp_board))
            
            # 计算当前步的物理方块面积
            area = (r2 - r1 + 1) * (c2 - c1 + 1)
            
            # 决策权重优化：优先选留下后路最多的；若后路一样，选占用方块最少的（省资源）
            if future_moves_count > max_future_moves:
                max_future_moves = future_moves_count
                min_area = area
                best_move = move
            elif future_moves_count == max_future_moves:
                if area < min_area:
                    min_area = area
                    best_move = move
        
        # 执行最优步
        r1, c1, r2, c2 = best_move
        x1, y1 = centers[r1][c1]
        x2, y2 = centers[r2][c2]
        
        drag_and_eliminate(x1, y1, x2, y2)
        
        # 内部棋盘刷新
        for i in range(r1, r2 + 1):
            for j in range(c1, c2 + 1):
                board[i][j] = 0
                
        score += 1
        print(f"得分 +1 | 消除矩阵: ({r1},{c1}) 到 ({r2},{c2}) | 预判后路 {max_future_moves} 种 | 消耗方块 {min_area} 个")

if __name__ == "__main__":
    centers = get_grid_centers()
    board = read_board(centers)
    
    # 打印识别出的棋盘
    print("----- 识别结果 (100%高保真校验版) -----")
    for row in board:
        print(row)
    print("-------------------------------------")
    
    # 开始速刷
    solve_game(board, centers)