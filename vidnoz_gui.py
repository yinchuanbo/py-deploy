import sys
import os
import json
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import importlib.util
from pathlib import Path

# 导入主自动化脚本作为模块
def import_vidnoz_automation():
    try:
        # 获取当前脚本的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建 vidnoz_automation.py 的路径
        script_path = os.path.join(script_dir, "vidnoz_automation.py")
        
        # 动态导入模块
        spec = importlib.util.spec_from_file_location("vidnoz_automation", script_path)
        vidnoz_automation = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vidnoz_automation)
        return vidnoz_automation
    except Exception as e:
        print(f"导入模块出错: {e}")
        return None

# 加载站点配置
def load_sites_config():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sites_path = os.path.join(script_dir, "sites.json")
        
        if not os.path.exists(sites_path):
            return {}
        
        with open(sites_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], dict):
                return data['urls']
    except Exception as e:
        print(f"加载站点配置出错: {e}")
    return {}

# 重定向控制台输出到GUI
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        if '\n' in self.buffer or len(self.buffer) > 80:
            self.flush()
    
    def flush(self):
        if self.buffer:
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state="disabled")
            self.buffer = ""

# 主应用
class VidnozApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vidnoz 自动化工具")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 加载模块
        self.vidnoz_automation = import_vidnoz_automation()
        if not self.vidnoz_automation:
            messagebox.showerror("错误", "无法加载自动化模块，程序无法启动")
            root.destroy()
            return
        
        # 加载站点配置
        self.sites = load_sites_config()
        if not self.sites:
            messagebox.showerror("错误", "无法加载站点配置，请确保sites.json文件存在")
            root.destroy()
            return
        
        # 创建界面
        self.create_widgets()
        
        # 任务运行状态
        self.is_running = False
        self.thread = None
        
        # 定时器更新UI
        self.update_ui()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 站点选择区域
        sites_frame = ttk.Frame(control_frame)
        sites_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 站点选择模式
        self.site_mode = tk.StringVar(value="all")
        ttk.Label(sites_frame, text="站点选择:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        site_mode_frame = ttk.Frame(sites_frame)
        site_mode_frame.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Radiobutton(site_mode_frame, text="所有站点", variable=self.site_mode, value="all", 
                      command=self.update_site_selection).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(site_mode_frame, text="包含特定站点", variable=self.site_mode, value="include", 
                      command=self.update_site_selection).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(site_mode_frame, text="排除特定站点", variable=self.site_mode, value="exclude", 
                      command=self.update_site_selection).pack(side=tk.LEFT, padx=5)
        
        # 站点多选框架
        self.sites_selection_frame = ttk.Frame(sites_frame)
        self.sites_selection_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 站点复选框
        self.site_vars = {}
        self.site_checkbuttons = {}
        
        # 每行显示4个站点选项
        for i, (site_id, url) in enumerate(self.sites.items()):
            var = tk.BooleanVar(value=False)
            self.site_vars[site_id] = var
            row, col = divmod(i, 4)
            cb = ttk.Checkbutton(self.sites_selection_frame, text=f"{site_id} ({url.split('/')[2]})", 
                               variable=var, state=tk.DISABLED)
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.site_checkbuttons[site_id] = cb
        
        # 更新模式
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(options_frame, text="更新模式:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.update_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="多页面更新（更新所有页面和样式）", 
                      variable=self.update_mode).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 控制按钮
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_button = ttk.Button(buttons_frame, text="开始执行", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="停止", state=tk.DISABLED, command=self.stop_automation)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始站点选择状态
        self.update_site_selection()
    
    def update_site_selection(self):
        mode = self.site_mode.get()
        
        for site_id, checkbutton in self.site_checkbuttons.items():
            if mode == "all":
                checkbutton.configure(state=tk.DISABLED)
                self.site_vars[site_id].set(False)
            else:
                checkbutton.configure(state=tk.NORMAL)
    
    def get_selected_sites(self):
        mode = self.site_mode.get()
        
        if mode == "all":
            return self.sites.copy()
        
        # 获取选中的站点
        selected = {}
        for site_id, var in self.site_vars.items():
            if var.get() and site_id in self.sites:
                selected[site_id] = self.sites[site_id]
        
        # 如果是包含模式，直接返回选中的站点
        if mode == "include":
            return selected
        
        # 如果是排除模式，返回未选中的站点
        excluded = {}
        for site_id, url in self.sites.items():
            if site_id not in selected:
                excluded[site_id] = url
        
        return excluded
    
    def start_automation(self):
        if self.is_running:
            return
        
        # 获取选中的站点
        sites_to_process = self.get_selected_sites()
        
        if not sites_to_process:
            messagebox.showwarning("警告", "没有选择任何站点，请至少选择一个站点")
            return
        
        # 设置多页面更新模式
        multi_page_mode = self.update_mode.get()
        
        # 清空日志
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # 禁用开始按钮
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        
        # 重定向控制台输出
        self.original_stdout = sys.stdout
        self.redirector = ConsoleRedirector(self.log_text)
        sys.stdout = self.redirector
        
        # 更新状态
        self.is_running = True
        self.status_var.set("正在执行...")
        
        # 设置多页面更新模式
        self.vidnoz_automation.EXECUTE_MULTI_PAGE_UPDATE = multi_page_mode
        
        # 创建新线程执行自动化任务
        self.thread = threading.Thread(target=self.run_automation, args=(sites_to_process,))
        self.thread.daemon = True
        self.thread.start()
    
    def run_automation(self, sites):
        try:
            # 执行自动化任务
            self.vidnoz_automation.automate_vidnoz(sites)
        except Exception as e:
            print(f"\n[X] 执行过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 恢复控制台输出
            sys.stdout = self.original_stdout
            
            # 更新UI状态
            if self.is_running:
                self.is_running = False
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, self.update_after_completion)
    
    def update_after_completion(self):
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("执行完成")
        
        # 刷新最后的日志
        if hasattr(self, 'redirector'):
            self.redirector.flush()
    
    def stop_automation(self):
        if not self.is_running:
            return
        
        self.is_running = False
        self.status_var.set("正在停止...")
        
        # 注意：简单地将is_running设为False只能在主代码中检查时起作用
        # Selenium无法直接中断，但下一个站点不会开始
        print("\n用户请求停止处理，将在当前站点完成后退出...")
    
    def update_ui(self):
        # 定时更新UI
        if hasattr(self, 'redirector'):
            self.redirector.flush()
        
        # 每100毫秒更新一次UI
        self.root.after(100, self.update_ui)

# 主程序
def main():
    try:
        # 确保应用在PyInstaller打包后能找到正确路径
        if getattr(sys, 'frozen', False):
            # 运行打包后的应用
            os.chdir(os.path.dirname(sys.executable))
        else:
            # 运行源代码
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        root = tk.Tk()
        app = VidnozApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("程序错误", f"发生了一个未预期的错误：\n{e}")

if __name__ == "__main__":
    main() 