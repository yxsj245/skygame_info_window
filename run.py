import os
import sys
import ctypes
import configparser
import re
from datetime import datetime
import tkinter as tk

# 定义配置文件的路径
CONFIG_FILE = 'config.ini'

# 创建配置文件解析器
config = configparser.ConfigParser()

# 全局变量
errorTimes = 0  # 新增的 错误次数 全局变量

# 检查管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False 
 
# 请求管理员权限 
def request_admin():

    # 检查配置文件是否存在
    if config.get('CONFIG', 'run_as_admin')=='':# 配置项不存在
        # 如果配置文件不存在，等待用户输入
        print("检测到没有管理员运行，请问是否要启用管理员权限以保证对日志的访问？程序会记住您的选择，下次默认使用您选的方式运行") 
        print("只是作为保险，不启用也大概率不影响，如果信息一直显示未知可以尝试启用（Y 启用/N 不启用）")
        print("请输入你的选择（Y/N）：",end='')
 
        # 获取用户输入
        user_input = input().strip().lower()
 
        # 根据用户输入进行判断
        if user_input == 'y': 
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        elif user_input == 'n': 
            pass
        else: 
            print("无效的输入，请输入 Y 或 N。点击任意键退出。。。")
            input()# 等待输入
            sys.exit(1)

        # 写入配置文件
        config['CONFIG']['run_as_admin'] = user_input
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        # 如果配置文件存在，读取路径
        user_input = config.get('CONFIG', 'run_as_admin')
        # 判断配置是否管理员运行
        if user_input == 'y': 
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        elif user_input == 'n': 
            return
        else:
            print("配置项出现错误，尝试清除。任意键退出。。。")
            # 清除配置文件
            config['CONFIG']['run_as_admin'] = ''
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
            input()

        


def prepare_config():
    # 检查config.ini文件是否存在
    if not os.path.exists('config.ini'):
       # 添加一个名为 "CONFIG" 的节
        config['CONFIG'] = {}
        
        # 在 "CONFIG" 节中添加配置项
        config['CONFIG']['run_as_admin'] = ''
        config['CONFIG']['log_file_path'] = ''
         
        # 写入配置文件 
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    



class LogFileHandler:
    def __init__(self, log_file, player_info_label, status_label, error_times_label):
        self.log_file = log_file
        self.file_position = 0
        self.player_info_label = player_info_label
        self.status_label = status_label
        self.error_times_label = error_times_label  # 新增的标签
        self.replacement_patterns = {
            r'Players updated: (\d+) total, (\d+) in level': self.update_player_info,
            r'Authority revoked from local because of server request': self.update_status_changing_room,
            r'Synchronized authority with LevelServer because of election': self.update_status_joined_room,
            r'Local elected by server as authority': self.update_status_owner,
            r'Connecting to server: \[(.*?)\]': self.update_status_connecting,
            r'.*error.*': self.update_error,  # 检测到错误
        }

    def update_player_info(self, total, level):
        info_text = f"服务器总人数：{total}，房间人数：{level}"
        self.player_info_label.config(text=info_text)

    def update_status_changing_room(self):
        self.status_label.config(text="房间状态：正在更换房间")

    def update_status_joined_room(self):
        self.status_label.config(text="房间状态：您当前位于他人房间")

    def update_status_owner(self):
        self.status_label.config(text="房间状态：您当前为房主")

    def update_status_connecting(self, ip_port):
        self.status_label.config(text=f"房间状态：正在连接服务器: [{ip_port}]")

    def update_error(self):# 【Debug用，后续版本会删除】
        global errorTimes  # 使用全局变量
        errorTimes += 1  # 错误次数自增
        self.error_times_label.config(text=f"【Debug】错误次数：{errorTimes}")  # 更新错误次数标签

    def apply_replacements(self, line):
        for pattern, replacer in self.replacement_patterns.items():
            match = re.search(pattern, line)
            if match:
                if callable(replacer):
                    replacer(*match.groups())
                else:
                    replacer()
                return

    def process_new_lines(self):
        with open(self.log_file, 'r', encoding='utf-8') as file:
            file.seek(self.file_position)
            new_lines = file.readlines()
            self.file_position = file.tell()

        if new_lines:
            last_line = new_lines[-1].strip()
            self.apply_replacements(last_line)

def main():
    prepare_config()# 如果没有，创建配置文件
    config.read(CONFIG_FILE)# 读取config文件

    # 检查是否具有管理员权限 
    if not is_admin():
        # 请求管理员权限 
        request_admin()
    
    print("游戏只有每次启动进入主菜单才会清空日志内容，请确保游戏已启动并登陆成功再启动监听")
    
    # 检查配置值是否存在
    if config.get('CONFIG', 'log_file_path')=='':
        # 如果配置值不存在，等待用户输入路径
        log_file_path = input("请输入日志文件的路径到具体log文件: ").replace('"', '') # 支持双引号的路径
        # 写入配置文件
        config['CONFIG']['log_file_path'] = log_file_path
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        # 如果配置文件存在，读取路径
        log_file_path = config.get('CONFIG', 'log_file_path')

    root = tk.Tk()
    root.title("Sky日志监控器")
    root.attributes("-topmost", True)  # 设置窗口始终在最前面

    # 创建三个标签，一个用于显示玩家信息，另一个用于显示房间状态，第三个用于显示错误次数(隐藏)
    player_info_label = tk.Label(root, text="当前总人数：未知，房间人数：未知", font=("微软雅黑", 12))
    player_info_label.pack(fill=tk.BOTH, expand=True)

    status_label = tk.Label(root, text="状态：未知", font=("微软雅黑", 12))
    status_label.pack(fill=tk.BOTH, expand=True)

    error_times_label = tk.Label(root, text="错误次数：0", font=("微软雅黑", 12), fg="red")  # 新增 错误次数的标签
    #error_times_label.pack(fill=tk.BOTH, expand=True)# 仅作为调试，默认不显示
    error_times_label.pack_forget()  # 隐藏标签

    log_handler = LogFileHandler(log_file_path, player_info_label, status_label, error_times_label)

    def poll_log_file():
        log_handler.process_new_lines()
        root.after(10, poll_log_file)  # 每0.01秒检查一次日志文件

    poll_log_file()  # 启动轮询

    def on_closing():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()
