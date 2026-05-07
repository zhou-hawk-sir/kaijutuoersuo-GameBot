# get_pos.py
import pyautogui
import keyboard
import time

print("【坐标获取工具】")
print("1. 请把鼠标移动到 左上角第一个数字 的中心位置，然后按下 'q' 键。")
keyboard.wait('q')
pos1 = pyautogui.position()
print(f"-> 左上角坐标: {pos1.x}, {pos1.y}")

time.sleep(0.5)

print("2. 请把鼠标移动到 右下角最后一个数字 的中心位置，然后按下 'w' 键。")
keyboard.wait('w')
pos2 = pyautogui.position()
print(f"-> 右下角坐标: {pos2.x}, {pos2.y}")

print("\n请把这两个坐标记下来，填入主程序中！")