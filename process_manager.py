import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import fnmatch
import threading
import time

class ProcessManager:
    def __init__(self, root):
        self.root = root
        self.root.title("进程管理器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 创建界面
        self.create_widgets()
        
        # 自动刷新进程列表
        self.refresh_processes()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 搜索框架
        search_frame = ttk.LabelFrame(main_frame, text="进程搜索", padding="5")
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="进程名模糊匹配:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # 按钮框架
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=0, column=2, padx=(5, 0))
        
        self.refresh_btn = ttk.Button(button_frame, text="刷新进程", command=self.refresh_processes)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        self.kill_selected_btn = ttk.Button(button_frame, text="关闭选中", command=self.kill_selected_processes)
        self.kill_selected_btn.pack(side=tk.LEFT, padx=2)
        
        self.kill_all_matched_btn = ttk.Button(button_frame, text="关闭所有匹配", command=self.kill_all_matched_processes)
        self.kill_all_matched_btn.pack(side=tk.LEFT, padx=2)
        
        # 提示文本
        tip_text = "提示: 使用 * 作为通配符，例如 'java*' 匹配所有java开头的进程，'*jdk*' 匹配包含jdk的进程"
        ttk.Label(search_frame, text=tip_text, foreground="gray").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # 统计信息框架
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        self.stats_label = ttk.Label(stats_frame, text="正在加载进程列表...")
        self.stats_label.pack(side=tk.LEFT)
        
        # 进程列表框架
        list_frame = ttk.LabelFrame(main_frame, text="进程列表", padding="5")
        list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview
        columns = ("PID", "进程名", "CPU使用率", "内存使用", "状态", "用户")
        self.process_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", selectmode="extended")
        
        # 设置列
        self.process_tree.heading("#0", text="选择")
        self.process_tree.column("#0", width=50, minwidth=50)
        
        self.process_tree.heading("PID", text="PID")
        self.process_tree.column("PID", width=80, minwidth=80)
        
        self.process_tree.heading("进程名", text="进程名")
        self.process_tree.column("进程名", width=200, minwidth=150)
        
        self.process_tree.heading("CPU使用率", text="CPU使用率")
        self.process_tree.column("CPU使用率", width=100, minwidth=80)
        
        self.process_tree.heading("内存使用", text="内存使用")
        self.process_tree.column("内存使用", width=100, minwidth=80)
        
        self.process_tree.heading("状态", text="状态")
        self.process_tree.column("状态", width=80, minwidth=60)
        
        self.process_tree.heading("用户", text="用户")
        self.process_tree.column("用户", width=100, minwidth=80)
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.process_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.process_tree.xview)
        self.process_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.process_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="5")
        log_frame.grid(row=3, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar.grid(row=0, column=1, sticky="ns")
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def get_process_info(self, proc):
        """获取进程信息"""
        try:
            with proc.oneshot():
                pid = proc.pid
                name = proc.name()
                
                try:
                    cpu_percent = proc.cpu_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu_percent = 0.0
                
                try:
                    memory_info = proc.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    memory_str = f"{memory_mb:.1f} MB"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    memory_str = "N/A"
                
                try:
                    status = proc.status()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    status = "Unknown"
                
                try:
                    username = proc.username()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    username = "N/A"
                
                return {
                    'pid': pid,
                    'name': name,
                    'cpu': f"{cpu_percent:.1f}%",
                    'memory': memory_str,
                    'status': status,
                    'username': username
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def refresh_processes(self):
        """刷新进程列表"""
        self.log_message("正在刷新进程列表...")
        
        # 清空现有列表
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # 获取所有进程
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            proc_info = self.get_process_info(proc)
            if proc_info:
                processes.append(proc_info)
        
        # 按PID排序
        processes.sort(key=lambda x: x['pid'])
        
        # 添加到树形视图
        for proc_info in processes:
            self.process_tree.insert("", "end", 
                                   values=(proc_info['pid'], proc_info['name'], 
                                          proc_info['cpu'], proc_info['memory'], 
                                          proc_info['status'], proc_info['username']))
        
        # 更新统计信息
        total_count = len(processes)
        self.stats_label.config(text=f"总进程数: {total_count}")
        
        # 应用当前搜索过滤
        self.filter_processes()
        
        self.log_message(f"进程列表刷新完成，共 {total_count} 个进程")
    
    def on_search_change(self, event=None):
        """搜索框内容变化时的处理"""
        self.filter_processes()
    
    def filter_processes(self):
        """根据搜索条件过滤进程"""
        search_pattern = self.search_var.get().strip().lower()
        
        if not search_pattern:
            # 显示所有进程
            for item in self.process_tree.get_children():
                self.process_tree.item(item, tags=())
            matched_count = len(self.process_tree.get_children())
        else:
            # 过滤进程
            matched_count = 0
            for item in self.process_tree.get_children():
                values = self.process_tree.item(item, "values")
                process_name = values[1].lower()  # 进程名
                
                # 使用fnmatch进行模糊匹配
                if fnmatch.fnmatch(process_name, search_pattern):
                    self.process_tree.item(item, tags=("matched",))
                    matched_count += 1
                else:
                    self.process_tree.item(item, tags=("hidden",))
            
            # 配置标签样式
            self.process_tree.tag_configure("matched", background="lightblue")
            self.process_tree.tag_configure("hidden", foreground="gray")
        
        # 更新统计
        total_count = len(self.process_tree.get_children())
        if search_pattern:
            self.stats_label.config(text=f"总进程数: {total_count}，匹配: {matched_count}")
        else:
            self.stats_label.config(text=f"总进程数: {total_count}")
    
    def get_matched_processes(self):
        """获取匹配的进程列表"""
        search_pattern = self.search_var.get().strip().lower()
        matched_processes = []
        
        for item in self.process_tree.get_children():
            values = self.process_tree.item(item, "values")
            process_name = values[1].lower()
            pid = int(values[0])
            
            if not search_pattern or fnmatch.fnmatch(process_name, search_pattern):
                matched_processes.append({'pid': pid, 'name': values[1]})
        
        return matched_processes
    
    def kill_selected_processes(self):
        """关闭选中的进程"""
        selected_items = self.process_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要关闭的进程")
            return
        
        selected_processes = []
        for item in selected_items:
            values = self.process_tree.item(item, "values")
            selected_processes.append({'pid': int(values[0]), 'name': values[1]})
        
        # 确认对话框
        result = messagebox.askyesno(
            "确认关闭进程",
            f"即将关闭 {len(selected_processes)} 个选中的进程:\n\n" +
            "\n".join([f"PID {p['pid']}: {p['name']}" for p in selected_processes[:5]]) +
            ("\n..." if len(selected_processes) > 5 else "") +
            "\n\n确定要继续吗？"
        )
        
        if result:
            self.kill_processes(selected_processes)
    
    def kill_all_matched_processes(self):
        """关闭所有匹配的进程"""
        search_pattern = self.search_var.get().strip()
        if not search_pattern:
            messagebox.showwarning("警告", "请先输入搜索模式")
            return
        
        matched_processes = self.get_matched_processes()
        if not matched_processes:
            messagebox.showinfo("信息", "没有找到匹配的进程")
            return
        
        # 确认对话框
        result = messagebox.askyesno(
            "确认关闭进程",
            f"即将关闭所有匹配 '{search_pattern}' 的进程:\n\n" +
            f"共 {len(matched_processes)} 个进程\n\n" +
            "\n".join([f"PID {p['pid']}: {p['name']}" for p in matched_processes[:5]]) +
            ("\n..." if len(matched_processes) > 5 else "") +
            "\n\n此操作不可撤销，确定要继续吗？"
        )
        
        if result:
            self.kill_processes(matched_processes)
    
    def kill_processes(self, processes):
        """批量关闭进程"""
        success_count = 0
        error_count = 0
        error_messages = []
        
        self.log_message(f"开始关闭 {len(processes)} 个进程...")
        
        for proc_info in processes:
            pid = proc_info['pid']
            name = proc_info['name']
            
            try:
                proc = psutil.Process(pid)
                proc.terminate()  # 先尝试优雅关闭
                success_count += 1
                self.log_message(f"✅ 成功关闭进程: PID {pid} ({name})")
                
            except psutil.NoSuchProcess:
                self.log_message(f"⚠️ 进程已不存在: PID {pid} ({name})")
            except psutil.AccessDenied:
                error_count += 1
                error_msg = f"权限不足: PID {pid} ({name})"
                error_messages.append(error_msg)
                self.log_message(f"❌ {error_msg}")
            except Exception as e:
                error_count += 1
                error_msg = f"PID {pid} ({name}): {str(e)}"
                error_messages.append(error_msg)
                self.log_message(f"❌ 关闭失败: {error_msg}")
        
        # 等待一下，然后强制关闭仍在运行的进程
        if success_count > 0:
            time.sleep(1)
            self.log_message("检查是否需要强制关闭...")
            
            for proc_info in processes:
                pid = proc_info['pid']
                name = proc_info['name']
                
                try:
                    proc = psutil.Process(pid)
                    if proc.is_running():
                        proc.kill()  # 强制关闭
                        self.log_message(f"🔥 强制关闭进程: PID {pid} ({name})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                    pass
        
        # 显示结果
        result_msg = f"操作完成!\n成功关闭: {success_count} 个进程"
        if error_count > 0:
            result_msg += f"\n关闭失败: {error_count} 个进程"
            if error_messages:
                result_msg += "\n\n错误详情:\n" + "\n".join(error_messages[:3])
                if len(error_messages) > 3:
                    result_msg += "\n..."
        
        messagebox.showinfo("关闭结果", result_msg)
        
        # 刷新进程列表
        self.refresh_processes()

def main():
    root = tk.Tk()
    app = ProcessManager(root)
    root.mainloop()

if __name__ == "__main__":
    main() 