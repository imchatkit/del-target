import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import glob
import json
import fnmatch
import subprocess
import psutil

class FolderCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("文件夹清理工具 by何威")
        self.root.geometry("600x800")
        self.root.resizable(True, True)
        
        # 配置文件路径
        self.config_file = "config.json"
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置
        self.load_config()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 文件夹路径设置
        ttk.Label(main_frame, text="目标文件夹路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        path_frame.columnconfigure(0, weight=1)
        
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_folder)
        self.browse_btn.grid(row=0, column=1)
        
        # 模糊匹配文件夹名字
        ttk.Label(main_frame, text="模糊匹配文件夹名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.pattern_var = tk.StringVar()
        self.pattern_entry = ttk.Entry(main_frame, textvariable=self.pattern_var, width=50)
        self.pattern_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        
        # 搜索深度设置
        depth_frame = ttk.Frame(main_frame)
        depth_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(depth_frame, text="搜索深度:").pack(side=tk.LEFT)
        self.depth_var = tk.StringVar(value="1")
        depth_combo = ttk.Combobox(depth_frame, textvariable=self.depth_var, width=10, state="readonly")
        depth_combo['values'] = ("1", "2", "3", "4", "5", "无限制")
        depth_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(depth_frame, text="(1=仅当前目录, 2=包含子目录, 无限制=递归搜索所有层级)", 
                 foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # 提示文本
        tip_text = "提示: 使用 * 作为通配符，例如 'temp*' 匹配以temp开头的文件夹"
        ttk.Label(main_frame, text=tip_text, foreground="gray").grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # 按钮框架
        button_frame1 = ttk.Frame(main_frame)
        button_frame1.grid(row=4, column=0, columnspan=3, pady=10)
        
        # 查看所有文件夹按钮
        self.list_all_btn = ttk.Button(button_frame1, text="查看目录下所有文件夹", command=self.list_all_folders)
        self.list_all_btn.pack(side=tk.LEFT, padx=5)
        
        # 预览按钮
        self.preview_btn = ttk.Button(button_frame1, text="预览匹配的文件夹", command=self.preview_matches)
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        # 进程管理按钮
        self.process_mgr_btn = ttk.Button(button_frame1, text="进程管理器", command=self.open_process_manager)
        self.process_mgr_btn.pack(side=tk.LEFT, padx=5)
        
        # 预览结果显示区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览结果", padding="5")
        preview_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=10)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 创建文本框和滚动条
        self.preview_text = tk.Text(preview_frame, height=8, width=60)
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 操作按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        # 清空按钮
        self.clean_btn = ttk.Button(button_frame, text="清空匹配的文件夹", 
                                   command=self.clean_folders, style="Accent.TButton")
        self.clean_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存配置按钮
        self.save_btn = ttk.Button(button_frame, text="保存配置", command=self.save_config)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # 退出按钮
        self.exit_btn = ttk.Button(button_frame, text="退出", command=self.root.quit)
        self.exit_btn.pack(side=tk.LEFT, padx=5)
    
    def browse_folder(self):
        """浏览选择文件夹"""
        folder_path = filedialog.askdirectory(title="选择目标文件夹")
        if folder_path:
            self.path_var.set(folder_path)
    
    def get_matching_folders(self):
        """获取匹配的文件夹列表"""
        base_path = self.path_var.get().strip()
        pattern = self.pattern_var.get().strip()
        depth_str = self.depth_var.get()
        
        if not base_path or not pattern:
            return []
        
        if not os.path.exists(base_path):
            return []
        
        # 解析搜索深度
        max_depth = None if depth_str == "无限制" else int(depth_str)
        
        matching_folders = []
        all_folders = []  # 用于调试，记录所有找到的文件夹
        
        try:
            matching_folders = self._search_folders_recursive(base_path, pattern, max_depth, 0)
            
            # 获取当前目录的所有文件夹用于调试
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    all_folders.append(item)
            
            # 如果没有匹配结果，在调试信息中显示调试信息
            if not matching_folders:
                print(f"调试信息：在路径 '{base_path}' 中递归搜索（深度={depth_str}）")
                print(f"顶级目录包含的文件夹：")
                for folder in sorted(all_folders):
                    print(f"  - {folder}")
                print(f"搜索模式：'{pattern}'")
                    
        except PermissionError:
            messagebox.showerror("错误", f"没有权限访问目录: {base_path}")
        except Exception as e:
            messagebox.showerror("错误", f"扫描目录时出错: {str(e)}")
        
        return matching_folders
    
    def _search_folders_recursive(self, current_path, pattern, max_depth, current_depth):
        """递归搜索文件夹"""
        matching_folders = []
        
        # 检查深度限制
        if max_depth is not None and current_depth >= max_depth:
            return matching_folders
        
        try:
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                
                if os.path.isdir(item_path):
                    # 检查当前文件夹是否匹配
                    if fnmatch.fnmatch(item.lower(), pattern.lower()) or fnmatch.fnmatch(item, pattern):
                        matching_folders.append(item_path)
                    
                    # 如果还没达到最大深度，继续递归搜索
                    if max_depth is None or current_depth + 1 < max_depth:
                        try:
                            sub_matches = self._search_folders_recursive(item_path, pattern, max_depth, current_depth + 1)
                            matching_folders.extend(sub_matches)
                        except PermissionError:
                            # 忽略没有权限的目录
                            continue
                        except Exception:
                            # 忽略其他错误，继续搜索其他目录
                            continue
                            
        except PermissionError:
            # 忽略没有权限的目录
            pass
        except Exception:
            # 忽略其他错误
            pass
        
        return matching_folders
    
    def list_all_folders(self):
        """列出目录下所有文件夹"""
        self.preview_text.delete(1.0, tk.END)
        
        base_path = self.path_var.get().strip()
        depth_str = self.depth_var.get()
        
        if not base_path:
            self.preview_text.insert(tk.END, "请先选择目标文件夹路径")
            return
        
        if not os.path.exists(base_path):
            self.preview_text.insert(tk.END, f"路径不存在: {base_path}")
            return
        
        # 解析搜索深度
        max_depth = None if depth_str == "无限制" else int(depth_str)
        
        try:
            # 获取递归文件夹结构
            folder_tree = self._get_folder_tree(base_path, max_depth, 0)
            
            self.preview_text.insert(tk.END, f"📂 目录: {base_path}\n")
            self.preview_text.insert(tk.END, f"🔍 搜索深度: {depth_str}\n")
            self.preview_text.insert(tk.END, "=" * 80 + "\n\n")
            
            if folder_tree:
                self._display_folder_tree(folder_tree, 0)
            else:
                self.preview_text.insert(tk.END, "📁 没有找到文件夹\n\n")
                
        except PermissionError:
            self.preview_text.insert(tk.END, f"错误: 没有权限访问目录 {base_path}")
        except Exception as e:
            self.preview_text.insert(tk.END, f"错误: 扫描目录时出错 - {str(e)}")
    
    def _get_folder_tree(self, current_path, max_depth, current_depth):
        """获取文件夹树结构"""
        if max_depth is not None and current_depth >= max_depth:
            return []
        
        folders = []
        try:
            items = os.listdir(current_path)
            for item in sorted(items):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    folder_info = {
                        'name': item,
                        'path': item_path,
                        'size': self.get_folder_size(item_path),
                        'depth': current_depth,
                        'children': []
                    }
                    
                    # 递归获取子文件夹
                    if max_depth is None or current_depth + 1 < max_depth:
                        try:
                            folder_info['children'] = self._get_folder_tree(item_path, max_depth, current_depth + 1)
                        except (PermissionError, Exception):
                            pass  # 忽略无法访问的目录
                    
                    folders.append(folder_info)
                    
        except (PermissionError, Exception):
            pass
        
        return folders
    
    def _display_folder_tree(self, folders, depth=0):
        """显示文件夹树"""
        total_folders = self._count_total_folders(folders)
        if depth == 0:
            self.preview_text.insert(tk.END, f"📁 总计文件夹: {total_folders} 个\n")
            self.preview_text.insert(tk.END, "-" * 80 + "\n")
        
        for i, folder in enumerate(folders):
            # 缩进和树形符号
            indent = "  " * folder['depth']
            if depth == 0:
                tree_symbol = "📁 "
            else:
                tree_symbol = "├─ " if i < len(folders) - 1 else "└─ "
            
            # 显示文件夹信息
            self.preview_text.insert(tk.END, f"{indent}{tree_symbol}{folder['name']} ({folder['size']})\n")
            
            # 显示子文件夹
            if folder['children']:
                self._display_folder_tree(folder['children'], depth + 1)
    
    def _count_total_folders(self, folders):
        """计算总文件夹数量"""
        count = len(folders)
        for folder in folders:
            count += self._count_total_folders(folder['children'])
        return count
    
    def preview_matches(self):
        """预览匹配的文件夹"""
        self.preview_text.delete(1.0, tk.END)
        
        base_path = self.path_var.get().strip()
        pattern = self.pattern_var.get().strip()
        
        if not base_path:
            self.preview_text.insert(tk.END, "请先选择目标文件夹路径")
            return
        
        if not pattern:
            self.preview_text.insert(tk.END, "请输入模糊匹配文件夹名")
            return
        
        if not os.path.exists(base_path):
            self.preview_text.insert(tk.END, f"路径不存在: {base_path}")
            return
        
        # 获取所有文件夹和匹配的文件夹
        all_folders = []
        try:
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    all_folders.append(item)
        except Exception as e:
            self.preview_text.insert(tk.END, f"扫描目录时出错: {str(e)}")
            return
        
        matching_folders = self.get_matching_folders()
        
        if not matching_folders:
            self.preview_text.insert(tk.END, f"在路径 '{base_path}' 中未找到匹配 '{pattern}' 的文件夹\n\n")
            
            if all_folders:
                self.preview_text.insert(tk.END, f"该目录下共有 {len(all_folders)} 个文件夹:\n")
                self.preview_text.insert(tk.END, "=" * 50 + "\n")
                for i, folder in enumerate(sorted(all_folders), 1):
                    self.preview_text.insert(tk.END, f"{i:2d}. {folder}\n")
                
                self.preview_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                self.preview_text.insert(tk.END, "提示：\n")
                self.preview_text.insert(tk.END, "• 使用 * 匹配任意字符，如 'target*' 匹配以target开头的文件夹\n")
                self.preview_text.insert(tk.END, "• 使用 *target* 匹配包含target的文件夹\n")
                self.preview_text.insert(tk.END, "• 搜索不区分大小写\n")
            else:
                self.preview_text.insert(tk.END, "该目录下没有任何文件夹")
        else:
            self.preview_text.insert(tk.END, f"找到 {len(matching_folders)} 个匹配的文件夹:\n")
            self.preview_text.insert(tk.END, f"搜索深度: {self.depth_var.get()}\n\n")
            
            for i, folder in enumerate(matching_folders, 1):
                folder_name = os.path.basename(folder)
                folder_size = self.get_folder_size(folder)
                
                # 计算相对路径显示
                rel_path = os.path.relpath(folder, base_path)
                depth_level = rel_path.count(os.sep)
                
                self.preview_text.insert(tk.END, f"{i:2d}. 📁 {folder_name}\n")
                self.preview_text.insert(tk.END, f"    完整路径: {folder}\n")
                self.preview_text.insert(tk.END, f"    相对路径: {rel_path}\n")
                self.preview_text.insert(tk.END, f"    目录深度: {depth_level + 1} 层\n")
                self.preview_text.insert(tk.END, f"    文件夹大小: {folder_size}\n\n")
    
    def get_folder_size(self, folder_path):
        """获取文件夹大小"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
            
            # 转换为人类可读的格式
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
        except Exception:
            return "未知大小"
    
    def clean_folders(self):
        """清空匹配的文件夹"""
        base_path = self.path_var.get().strip()
        pattern = self.pattern_var.get().strip()
        
        if not base_path or not pattern:
            messagebox.showwarning("警告", "请填写文件夹路径和模糊匹配名称")
            return
        
        matching_folders = self.get_matching_folders()
        
        if not matching_folders:
            messagebox.showinfo("信息", "没有找到匹配的文件夹")
            return
        
        # 确认对话框
        result = messagebox.askyesno(
            "确认删除",
            f"即将删除 {len(matching_folders)} 个文件夹:\n\n" +
            "\n".join([os.path.basename(f) for f in matching_folders[:5]]) +
            ("\n..." if len(matching_folders) > 5 else "") +
            "\n\n此操作不可撤销，确定要继续吗？"
        )
        
        if not result:
            return
        
        # 执行删除
        success_count = 0
        error_count = 0
        error_messages = []
        
        for folder_path in matching_folders:
            try:
                shutil.rmtree(folder_path)
                success_count += 1
            except Exception as e:
                error_count += 1
                error_messages.append(f"{os.path.basename(folder_path)}: {str(e)}")
        
        # 显示结果
        result_msg = f"删除完成!\n成功删除: {success_count} 个文件夹"
        if error_count > 0:
            result_msg += f"\n删除失败: {error_count} 个文件夹"
            if error_messages:
                result_msg += "\n\n错误详情:\n" + "\n".join(error_messages[:3])
                if len(error_messages) > 3:
                    result_msg += "\n..."
        
        messagebox.showinfo("删除结果", result_msg)
        
        # 刷新预览
        self.preview_matches()
    
    def save_config(self):
        """保存配置到文件"""
        config = {
            "folder_path": self.path_var.get(),
            "pattern": self.pattern_var.get(),
            "search_depth": self.depth_var.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.path_var.set(config.get("folder_path", ""))
                self.pattern_var.set(config.get("pattern", ""))
                self.depth_var.set(config.get("search_depth", "1"))
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
    
    def open_process_manager(self):
        """打开进程管理器"""
        try:
            # 导入进程管理器模块
            from process_manager import ProcessManager
            
            # 创建新窗口
            process_window = tk.Toplevel(self.root)
            ProcessManager(process_window)
            
        except ImportError:
            messagebox.showerror("错误", "找不到进程管理器模块 (process_manager.py)")
        except Exception as e:
            messagebox.showerror("错误", f"启动进程管理器失败: {str(e)}")

def main():
    root = tk.Tk()
    app = FolderCleaner(root)
    root.mainloop()

if __name__ == "__main__":
    main() 