import re
from datetime import datetime
import tkinter as tk

class LogFileHandler:
    def __init__(self, log_file, player_info_label, status_label):
        self.log_file = log_file
        self.file_position = 0
        self.player_info_label = player_info_label
        self.status_label = status_label
        self.replacement_patterns = {
            r'Players updated: (\d+) total, (\d+) in level': self.update_player_info,
            r'Authority revoked from local because of server request': self.update_status_changing_room,
            r'Synchronized authority with LevelServer because of election': self.update_status_joined_room,
            r'Local elected by server as authority': self.update_status_owner,
            r'Connecting to server': self.update_status_connecting,
            r'.*error.*': self.update_error,  # 检测到错误
        }

    def update_player_info(self, total, level):
        info_text = f"服务器总人数：{total}，房间人数：{level}"
        self.player_info_label.config(text=info_text)

    def update_status_changing_room(self):
        self.status_label.config(text="房间状态：正在更换房间")

    def update_status_joined_room(self):
        self.status_label.config(text="房间状态：您已加入他人房间")

    def update_status_owner(self):
        self.status_label.config(text="房间状态：您当前为房主")

    def update_status_connecting(self):
        self.status_label.config(text="房间状态：正在连接服务器")

    def update_error(self):
        self.player_info_label.config(text="错误：由于日志输出error,此时日志会暂停所有信息输出，需要您重启游戏和脚本")
        self.status_label.config(text="错误：由于日志输出error,此时日志会暂停所有信息输出，需要您重启游戏和脚本")

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
    print("游戏只有每次启动进入主菜单才会清空日志内容，请确保游戏已启动并登陆成功再启动监听")
    log_file_path = input("请输入日志文件的路径到具体log文件: ")

    root = tk.Tk()
    root.title("Sky日志监控器")
    root.attributes("-topmost", True)  # 设置窗口始终在最前面

    # 创建两个标签，一个用于显示玩家信息，另一个用于显示房间状态
    player_info_label = tk.Label(root, text="当前总人数：0，房间人数：0", font=("Helvetica", 12))
    player_info_label.pack(fill=tk.BOTH, expand=True)

    status_label = tk.Label(root, text="状态：未知", font=("Helvetica", 12))
    status_label.pack(fill=tk.BOTH, expand=True)

    log_handler = LogFileHandler(log_file_path, player_info_label, status_label)

    def poll_log_file():
        log_handler.process_new_lines()
        root.after(10, poll_log_file)  # 每秒检查一次日志文件

    poll_log_file()  # 启动轮询

    def on_closing():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()
