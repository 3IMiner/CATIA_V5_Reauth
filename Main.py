import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

DEFAULT_SERVER_PATH = r"C:\Program Files (x86)\Dassault Systemes\DS License Server\intel_a\code\bin"

# ======================== 多语言文本 ========================
T = {
    "zh": {
        "win_title":       "CATIA V5 2012-2016 重新授权唤醒工具",
        "heading":         "CATIA V5 2012-2016 重新授权唤醒工具",
        "lang_btn":        "EN",
        "bin_frame":       "授权服务器 bin 目录",
        "browse_btn":      "浏览...",
        "reconnect_btn":   "重新连接服务器",
        "dialog_title":    "选择 DS License Server 的 bin 目录",
        "err_path_title":  "路径错误",
        "err_path_msg":    "bin 目录不存在：",
        "err_file_title":  "文件缺失",
        "err_file_msg":    "未找到 DSLicSrv.exe：",
        "status_connecting": "正在重新连接服务器...",
        "status_ok":       "服务器已重新连接！你可以在控制台窗口中手动输入指令。",
        "status_fail":     "重新连接服务器失败",
        "console_title":   "DSLicSrv 控制台 — 可直接输入指令",
    },
    "en": {
        "win_title":       "CATIA V5 2012-2016 Re-auth Wake Tool",
        "heading":         "CATIA V5 2012-2016 Re-auth Wake Tool",
        "lang_btn":        "中文",
        "bin_frame":       "License Server bin Directory",
        "browse_btn":      "Browse...",
        "reconnect_btn":   "Reconnect Server",
        "dialog_title":    "Select DS License Server bin Directory",
        "err_path_title":  "Path Error",
        "err_path_msg":    "bin directory not found:",
        "err_file_title":  "File Missing",
        "err_file_msg":    "DSLicSrv.exe not found:",
        "status_connecting": "Reconnecting to server...",
        "status_ok":       "Server reconnected! You can type commands in the console.",
        "status_fail":     "Reconnect failed",
        "console_title":   "DSLicSrv Console — type commands here",
    },
}


class LicenseServerGUI:
    def __init__(self, root):
        self.root = root
        self.lang = "zh"
        self.root.geometry("550x250")

        # ---------- 顶栏：标题 + 语言切换 ----------
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=(10, 0))

        self.heading_label = ttk.Label(top, font=("Arial", 12, "bold"))
        self.heading_label.pack(side="left")

        self.lang_btn = ttk.Button(top, width=5, command=self.toggle_lang)
        self.lang_btn.pack(side="right")

        # ---------- bin 目录 ----------
        self.bin_frame = ttk.LabelFrame(self.root, padding=5)
        self.bin_frame.pack(fill="x", padx=10, pady=5)

        self.bin_var = tk.StringVar(value=DEFAULT_SERVER_PATH)
        self.bin_entry = ttk.Entry(self.bin_frame, textvariable=self.bin_var, width=50)
        self.bin_entry.pack(side="left", padx=(5, 2), pady=5, fill="x", expand=True)

        self.browse_btn = ttk.Button(self.bin_frame, width=8, command=self.browse_bin)
        self.browse_btn.pack(side="left", padx=(2, 5), pady=5)

        # ---------- 操作按钮 ----------
        self.reconnect_btn = ttk.Button(self.root, width=24, command=self.reconnect_server)
        self.reconnect_btn.pack(pady=10)

        # ---------- 状态 ----------
        self.status_label = ttk.Label(self.root, font=("Arial", 8))
        self.status_label.pack(pady=(0, 10))

        # 首次刷新 UI
        self._update_ui()

    # ---------- 语言切换 ----------
    def toggle_lang(self):
        self.lang = "en" if self.lang == "zh" else "zh"
        self._update_ui()

    def t(self, key):
        """取当前语言的文本"""
        return T[self.lang].get(key, key)

    def _update_ui(self):
        """根据当前语言刷新所有控件文本"""
        self.root.title(self.t("win_title"))
        self.heading_label.config(text=self.t("heading"))
        self.lang_btn.config(text=self.t("lang_btn"))
        self.bin_frame.config(text=self.t("bin_frame"))
        self.browse_btn.config(text=self.t("browse_btn"))
        self.reconnect_btn.config(text=self.t("reconnect_btn"))
        # 状态不在这里改，保持实际状态

    # ---------- 路径浏览 ----------
    def browse_bin(self):
        folder = filedialog.askdirectory(
            title=self.t("dialog_title"),
            initialdir=self.bin_var.get() if os.path.isdir(self.bin_var.get()) else "C:\\"
        )
        if folder:
            self.bin_var.set(folder)

    # ---------- 路径获取 ----------
    def get_bin_dir(self):
        return self.bin_var.get().strip()

    def get_dslicsrv(self):
        return os.path.join(self.get_bin_dir(), "DSLicSrv.exe")

    # ---------- 路径验证 ----------
    def validate(self):
        bin_dir = self.get_bin_dir()
        dslicsrv = self.get_dslicsrv()

        if not os.path.isdir(bin_dir):
            messagebox.showerror(
                self.t("err_path_title"),
                f"{self.t('err_path_msg')}\n{bin_dir}"
            )
            return False
        if not os.path.isfile(dslicsrv):
            messagebox.showerror(
                self.t("err_file_title"),
                f"{self.t('err_file_msg')}\n{dslicsrv}"
            )
            return False
        return True

    # ---------- 关闭旧进程 ----------
    def _kill_old_proc(self):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "DSLicSrv.exe"],
                capture_output=True, timeout=5
            )
        except Exception:
            pass
        if hasattr(self, "_bat_path") and self._bat_path:
            try:
                os.remove(self._bat_path)
            except Exception:
                pass
            self._bat_path = None

    # ---------- 启动 DSLicSrv ----------
    def _send_and_keep_alive(self, commands):
        bin_dir = self.get_bin_dir()
        dslicsrv = self.get_dslicsrv()

        self._kill_old_proc()

        echo_cmds = " & ".join(f"echo {cmd}" for cmd in commands)

        bat_path = os.path.join(os.environ.get("TEMP", "."), "_dslic_srv.bat")
        with open(bat_path, "w") as f:
            f.write("@echo off\r\n")
            f.write(f'cd /d "{bin_dir}"\r\n')
            f.write("echo ============================================\r\n")
            f.write(f"echo   {self.t('console_title')}\r\n")
            f.write("echo ============================================\r\n")
            f.write(f'({echo_cmds} & more) | "{dslicsrv}" /test -admin\r\n')

        self._bat_path = bat_path

        subprocess.Popen(
            f'start "DS License Server Console" cmd /k "{bat_path}"',
            shell=True,
        )
        return True

    # ---------- 重新连接服务器 ----------
    def reconnect_server(self):
        if not self.validate():
            return

        self.status_label.config(text=self.t("status_connecting"), foreground="blue")
        self.root.update()

        if self._send_and_keep_alive(["c localhost 4084"]):
            self.status_label.config(text=self.t("status_ok"), foreground="green")
        else:
            self.status_label.config(text=self.t("status_fail"), foreground="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = LicenseServerGUI(root)
    root.mainloop()
