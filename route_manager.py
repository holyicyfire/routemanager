#!/usr/bin/env python3
"""
系统路由配置管理器 - 带详细错误提示和日志
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
import sys
import platform
import logging
import ipaddress
import os
import ctypes
import threading
import time

# 隐藏控制台窗口（仅在Windows上运行.py文件时）
if platform.system().lower() == 'windows' and getattr(sys, 'frozen', False) == False:
    try:
        # 获取当前窗口句柄
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            # 隐藏控制台窗口
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except:
        pass

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def restart_as_admin():
    """以管理员身份重启程序"""
    if is_admin():
        return True

    # 获取当前脚本的完整路径
    script_path = os.path.abspath(sys.argv[0])

    # 使用shell32的RunAs函数以管理员身份重启
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script_path}"', None, 1
        )
        return False
    except Exception as e:
        logger.error(f"无法以管理员身份重启: {e}")
        return False

class RouteManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("系统路由配置管理器")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # 设置窗口图标
        self._set_window_icon()

        # 检测操作系统
        self.is_windows = platform.system().lower() == 'windows'
        logger.info(f"操作系统: {platform.system()}")

        # 检测管理员权限
        self.is_admin = is_admin() if self.is_windows else True
        logger.info(f"管理员权限: {self.is_admin}")

        # 添加接口信息缓存
        self._interfaces_cache = None
        self._interfaces_cache_time = 0
        self._interfaces_cache_duration = 30  # 缓存30秒

        # 添加路由数据缓存
        self._routes_cache = None
        self._routes_cache_time = 0
        self._routes_cache_duration = 60  # 缓存60秒

        # 加载状态标志
        self._is_loading_routes = False

        # 如果没有管理员权限，提示用户
        if self.is_windows and not self.is_admin:
            self.show_admin_prompt()
            return

        self.setup_ui()
        # 延迟异步加载路由数据，不阻塞UI启动
        self.root.after(100, self._delayed_refresh_routes)

    def _set_window_icon(self):
        """设置窗口图标"""
        try:
            # 获取图标文件路径
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon", "route_manager.ico")

            # 检查图标文件是否存在
            if os.path.exists(icon_path):
                # 在Windows上设置图标
                try:
                    self.root.iconbitmap(icon_path)
                    logger.info(f"已设置窗口图标: {icon_path}")
                except Exception as e:
                    logger.warning(f"Windows图标设置失败: {e}")

                # 在Linux/macOS上尝试使用PhotoImage
                try:
                    icon_image = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, icon_image)
                    logger.info(f"已设置窗口图标: {icon_path}")
                except Exception as e:
                    logger.warning(f"PhotoImage图标设置失败: {e}")
            else:
                logger.warning(f"图标文件不存在: {icon_path}")
        except Exception as e:
            logger.warning(f"设置窗口图标时出错: {e}")

    def show_admin_prompt(self):
        """显示管理员权限提示"""
        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("权限提示")
        prompt_window.geometry("600x500")
        prompt_window.transient(self.root)
        prompt_window.grab_set()

        # 设置窗口背景色
        prompt_window.configure(bg="#f8f9fa")

        # 居中显示
        prompt_window.update_idletasks()
        x = (prompt_window.winfo_screenwidth() // 2) - (prompt_window.winfo_width() // 2)
        y = (prompt_window.winfo_screenheight() // 2) - (prompt_window.winfo_height() // 2)
        prompt_window.geometry(f"+{x}+{y}")

        # 创建提示内容
        main_frame = ttk.Frame(prompt_window, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 警告图标和标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 25))

        # 标题文字
        warning_text = ttk.Label(title_frame, text="需要管理员权限",
                                font=("Arial", 16), foreground="#dc3545")
        warning_text.pack(anchor=tk.CENTER)

        # 说明文字区域
        info_frame = ttk.LabelFrame(main_frame, text="操作说明", padding="20")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 25))

        info_text = tk.Text(info_frame, wrap=tk.WORD, height=10, font=("Arial", 11))
        info_text.pack(fill=tk.BOTH, expand=True)
        info_text.config(bg="#ffffff", fg="#333333", relief=tk.FLAT, padx=10, pady=10)

        info_content = """修改系统路由表需要管理员权限，因为程序需要执行系统级的网络配置命令。

请按以下步骤以管理员身份重新运行程序：

步骤一：关闭当前程序
   点击下方的"退出程序"按钮

步骤二：以管理员身份运行
   1. 右键点击"命令提示符"或"PowerShell"
   2. 选择"以管理员身份运行"
   3. 在管理员窗口中执行以下命令：
      cd /d "D:\\test\\routeconf"
      python route_manager.py

或者：
   1. 右键点击 route_manager.py 文件
   2. 选择"使用Python" → "以管理员身份运行"

注意：只有在具有管理员权限的情况下，程序才能正常添加、删除或修改系统路由表。"""

        info_text.insert(tk.END, info_content)
        info_text.config(state=tk.DISABLED)

        # 提示信息
        tip_frame = ttk.Frame(main_frame)
        tip_frame.pack(fill=tk.X, pady=(0, 20))

        tip_label = ttk.Label(tip_frame,
                             text="💡 提示：如果您不确定如何操作，建议联系系统管理员协助",
                             font=("Arial", 10), foreground="#6c757d")
        tip_label.pack()

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        # 按钮样式
        button_style = ttk.Style()
        button_style.configure("Admin.TButton", font=("Arial", 11), padding=(20, 10))

        # 退出按钮
        exit_btn = ttk.Button(button_frame, text="退出程序",
                            command=self.quit_program,
                            style="Admin.TButton")
        exit_btn.pack(side=tk.RIGHT)

        # 显示提示窗口但不隐藏主窗口
        # self.root.withdraw()  # 注释掉隐藏主窗口

        # 当提示窗口关闭时，关闭主程序
        prompt_window.protocol("WM_DELETE_WINDOW", lambda: self.quit_program())

        # 等待提示窗口关闭
        prompt_window.wait_window()  # 使用prompt_window的wait_window

    
    def quit_program(self):
        """退出程序"""
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重 - 为路由表区域分配更多空间
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=3)  # 给路由表区域更多权重

        # 顶部控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(1, weight=1)

        # 左侧按钮组
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky=tk.W)

        # 创建按钮样式
        style = ttk.Style()
        style.configure("Action.TButton", padding=(10, 5))

        ttk.Button(button_frame, text="刷新", command=lambda: self.refresh_routes(force_refresh=True), style="Action.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(button_frame, text="添加路由", command=self.add_route, style="Action.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(button_frame, text="删除路由", command=self.delete_route, style="Action.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(button_frame, text="设备IP信息", command=self.show_ip_info, style="Action.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(button_frame, text="测试命令", command=self.test_route_command, style="Action.TButton").pack(side=tk.LEFT)

        # 右侧IPv版本选择
        version_frame = ttk.Frame(control_frame)
        version_frame.grid(row=0, column=2, sticky=tk.E)

        ttk.Label(version_frame, text="协议版本：").pack(side=tk.LEFT, padx=(0, 8))

        self.version_var = tk.StringVar(value="IPv4")

        ttk.Radiobutton(version_frame, text="IPv4", variable=self.version_var, value="IPv4",
                       command=lambda: self.refresh_routes(force_refresh=True)).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(version_frame, text="IPv6", variable=self.version_var, value="IPv6",
                       command=lambda: self.refresh_routes(force_refresh=True)).pack(side=tk.LEFT)

        # 创建路由显示区域 - 使用上下两个独立区域
        routes_container = ttk.Frame(main_frame)
        routes_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        routes_container.columnconfigure(0, weight=1)
        routes_container.rowconfigure(0, weight=1)
        routes_container.rowconfigure(1, weight=1)

        # 创建表格样式
        tree_style = ttk.Style()
        tree_style.configure("Treeview", font=("Arial", 10), rowheight=22)
        tree_style.configure("Treeview.Heading", font=("Arial", 10), padding=(8, 5))
        tree_style.map("Treeview", background=[('selected', '#0078d4')], foreground=[('selected', 'white')])

        # 活动路由区域
        active_label_frame = ttk.LabelFrame(routes_container, text="活动路由 (系统重启后丢失)", padding="12")
        active_label_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))

        # 持久路由区域
        persistent_label_frame = ttk.LabelFrame(routes_container, text="持久路由 (系统重启后保留)", padding="12")
        persistent_label_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(8, 0))

        # 活动路由表格
        active_columns = ("目标网络", "子网掩码/前缀长度", "网关", "接口", "跃点数")
        self.active_tree = ttk.Treeview(active_label_frame, columns=active_columns, show='headings', height=12)

        # 设置活动路由列标题和宽度
        column_widths = {"目标网络": 220, "子网掩码/前缀长度": 150, "网关": 200, "接口": 120, "跃点数": 80}
        for col in active_columns:
            self.active_tree.heading(col, text=col, anchor=tk.W)
            self.active_tree.column(col, width=column_widths.get(col, 120), minwidth=60)

        # 活动路由滚动条
        active_scrollbar = ttk.Scrollbar(active_label_frame, orient=tk.VERTICAL, command=self.active_tree.yview)
        self.active_tree.configure(yscrollcommand=active_scrollbar.set)

        self.active_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        active_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(5, 0))

        active_label_frame.columnconfigure(0, weight=1)
        active_label_frame.rowconfigure(0, weight=1)

        # 创建活动路由右键菜单
        self.active_context_menu = tk.Menu(self.root, tearoff=0)
        self.active_context_menu.add_command(label="删除路由", command=self.delete_route_from_context)

        # 绑定右键事件
        self.active_tree.bind("<Button-3>", self.show_active_context_menu)

        # 持久路由表格
        self.persistent_columns_ipv4 = ("目标网络", "子网掩码", "网关地址", "跃点数")
        self.persistent_columns_ipv6 = ("目标网络", "前缀长度", "网关地址", "跃点数")
        self.persistent_tree = ttk.Treeview(persistent_label_frame, columns=self.persistent_columns_ipv4, show='headings', height=6)

        # 设置持久路由列标题和宽度
        persistent_widths = {"目标网络": 240, "子网掩码": 130, "前缀长度": 100, "网关地址": 220, "跃点数": 80}
        self._update_persistent_columns_headers("IPv4", persistent_widths)

        # 持久路由滚动条
        persistent_scrollbar = ttk.Scrollbar(persistent_label_frame, orient=tk.VERTICAL, command=self.persistent_tree.yview)
        self.persistent_tree.configure(yscrollcommand=persistent_scrollbar.set)

        self.persistent_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        persistent_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(5, 0))

        persistent_label_frame.columnconfigure(0, weight=1)
        persistent_label_frame.rowconfigure(0, weight=1)

        # 创建持久路由右键菜单
        self.persistent_context_menu = tk.Menu(self.root, tearoff=0)
        self.persistent_context_menu.add_command(label="删除路由", command=self.delete_route_from_context)

        # 绑定右键事件
        self.persistent_tree.bind("<Button-3>", self.show_persistent_context_menu)

        # 日志显示区域 - 减小高度
        log_frame = ttk.LabelFrame(main_frame, text="调试日志", padding="8")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        log_frame.columnconfigure(0, weight=1)

        # 创建日志文本样式
        log_text_style = tk.Text(log_frame, height=4, wrap=tk.WORD, font=("Arial", 9))
        log_text_style.config(bg="#f8f9fa", fg="#333333", insertbackground="#0078d4")

        self.log_text = log_text_style
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=(5, 0))

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")

        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 0))

        # 创建状态栏样式
        style = ttk.Style()
        style.configure("Status.TLabel", font=("Arial", 9), padding=(8, 4))

        status_bar = ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel", relief=tk.SOLID, background="#e9ecef")
        status_bar.pack(fill=tk.X)

    def _update_persistent_columns_headers(self, version, widths=None):
        """更新持久路由表格的列标题"""
        if version == "IPv4":
            columns = self.persistent_columns_ipv4
        else:
            columns = self.persistent_columns_ipv6

        # 重新配置表格列
        self.persistent_tree['columns'] = columns

        # 设置列标题和宽度
        for col in columns:
            self.persistent_tree.heading(col, text=col, anchor=tk.W)
            if widths and col in widths:
                self.persistent_tree.column(col, width=widths[col], minwidth=60)
            else:
                # 默认宽度
                if col == "目标网络" or col == "网关地址":
                    self.persistent_tree.column(col, width=180)
                else:
                    self.persistent_tree.column(col, width=100)

    def log(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        logger.info(message)

    def get_routes(self):
        """获取系统路由表"""
        self.log("正在获取路由表...")
        try:
            version = self.version_var.get()

            if self.is_windows:
                if version == "IPv4":
                    self.log("执行命令: route print")
                    result = subprocess.run(['route', 'print'],
                                         capture_output=True,
                                         text=True,
                                         shell=True,
                                         timeout=10,
                                         encoding='utf-8',
                                         errors='ignore')
                    if result.returncode != 0:
                        raise Exception(f"执行route命令失败: {result.stderr}")
                    routes = self.parse_windows_routes(result.stdout)
                else:
                    self.log("执行命令: route print (获取IPv6)")
                    result = subprocess.run(['route', 'print'],
                                         capture_output=True,
                                         text=True,
                                         shell=True,
                                         timeout=10,
                                         encoding='utf-8',
                                         errors='ignore')
                    if result.returncode != 0:
                        raise Exception(f"执行route命令失败: {result.stderr}")
                    routes = self.parse_windows_routes_ipv6(result.stdout)
            else:
                # Linux/Mac支持
                pass

            self.log(f"获取到 {len(routes)} 条路由")
            return routes

        except Exception as e:
            self.log(f"错误: {str(e)}")
            messagebox.showerror("错误", f"获取路由表失败: {str(e)}")
            return []

    def parse_windows_routes(self, output):
        """解析Windows路由表输出，包括持久路由"""
        routes = []
        lines = output.split('\n')
        in_active_routes = False
        in_persistent_routes = False

        for line in lines:
            line = line.strip()
            if line.startswith("Active Routes:"):
                in_active_routes = True
                in_persistent_routes = False
                continue
            elif line.startswith("Persistent Routes:"):
                in_active_routes = False
                in_persistent_routes = True
                continue
            elif (line.startswith("Interface List") and in_active_routes):
                # 只有在路由解析过程中遇到Interface List才退出
                in_active_routes = False
                in_persistent_routes = False
                break

            # 处理活动路由和持久路由
            if (in_active_routes or in_persistent_routes) and line and not line.startswith("Network") and not line.startswith("Network Address"):
                parts = re.split(r'\s+', line)

                # 添加更严格的验证，确保这是有效的路由条目
                if in_persistent_routes:
                    # 持久路由的格式可能不同
                    if len(parts) >= 4 and self._is_valid_ip_address(parts[0]) and parts[0] != "Network":
                        destination = parts[0]
                        netmask = parts[1]
                        gateway = parts[2]
                        metric = parts[3]
                        # 持久路由可能没有interface信息，设为空
                        interface = ""

                        routes.append({
                            'destination': destination,
                            'netmask': netmask,
                            'gateway': gateway,
                            'interface': interface,
                            'metric': metric,
                            'persistent': True
                        })
                else:
                    # 活动路由的标准格式
                    if len(parts) >= 5 and self._is_valid_ip_address(parts[0]) and parts[0] != "Network":
                        destination = parts[0]
                        netmask = parts[1]
                        gateway = parts[2]
                        interface = parts[3]
                        metric = parts[4]

                        routes.append({
                            'destination': destination,
                            'netmask': netmask,
                            'gateway': gateway,
                            'interface': interface,
                            'metric': metric,
                            'persistent': False
                        })

        return routes

    def _is_valid_ip_address(self, address):
        """验证是否为有效的IP地址或网络地址"""
        try:
            # 检查是否为On-link（这是有效的网关值）
            if address == "On-link":
                return True

            # 检查是否为有效的IPv4地址或网络
            if '.' in address:
                # IPv4地址验证
                parts = address.split('.')
                if len(parts) == 4:
                    for part in parts:
                        if not part.isdigit() or int(part) < 0 or int(part) > 255:
                            return False
                    return True
                elif len(parts) <= 4:  # 可能是简化的网络地址
                    for part in parts:
                        if not part.isdigit() or int(part) < 0 or int(part) > 255:
                            return False
                    return True

            return False
        except:
            return False

    def parse_windows_routes_ipv6(self, output):
        """解析Windows IPv6路由表输出，包括持久路由"""
        routes = []
        lines = output.split('\n')
        in_ipv6_active = False
        in_ipv6_persistent = False

        for line in lines:
            line = line.strip()
            if 'IPv6 Route Table' in line:
                in_ipv6_active = True
                in_ipv6_persistent = False
                continue
            elif in_ipv6_active and ('Persistent Routes:' in line):
                in_ipv6_active = False
                in_ipv6_persistent = True
                continue
            elif (in_ipv6_active or in_ipv6_persistent) and (line.startswith('Interface List') or line.startswith('IPv4 Route Table')):
                break

            if (in_ipv6_active or in_ipv6_persistent) and line and not line.startswith('If') and not line.startswith('Network Destination'):
                parts = [part for part in re.split(r'\s+', line) if part]

                if len(parts) >= 3:
                    interface_num = parts[0] if parts[0] else ''

                    metric = ''
                    for i, part in enumerate(parts[1:], 1):
                        if part.isdigit():
                            metric = part
                            network_parts = parts[i+1:]
                            break
                    else:
                        network_parts = parts[1:]
                        metric = ''

                    if network_parts:
                        destination = network_parts[0]
                        gateway = network_parts[1] if len(network_parts) > 1 else 'On-link'
                    else:
                        destination = ''
                        gateway = 'On-link'

                    prefix_length = ''
                    if '/' in destination:
                        try:
                            prefix_length = destination.split('/')[1]
                        except:
                            prefix_length = ''

                    if destination:
                        routes.append({
                            'destination': destination,
                            'netmask': prefix_length,
                            'gateway': gateway,
                            'interface': interface_num,
                            'metric': metric,
                            'persistent': in_ipv6_persistent
                        })

        return routes

    def _delayed_refresh_routes(self):
        """延迟异步刷新路由表，不阻塞UI启动"""
        if self._is_loading_routes:
            return  # 避免重复加载

        self._is_loading_routes = True
        self.status_var.set("正在加载路由信息...")
        self.log("开始异步加载路由数据...")

        # 启动后台线程加载路由
        threading.Thread(target=self._load_routes_async, daemon=True).start()

    def _load_routes_async(self):
        """异步加载路由数据"""
        try:
            # 检查缓存是否有效
            current_time = time.time()
            if (self._routes_cache is not None and
                current_time - self._routes_cache_time < self._routes_cache_duration):
                self.log("使用缓存的路由数据")
                self.root.after(0, self._update_routes_display, self._routes_cache)
                return

            # 更新状态显示加载进度
            self.root.after(0, lambda: self.status_var.set("正在获取系统路由信息..."))

            # 获取路由数据
            routes = self.get_routes()

            # 更新状态显示解析进度
            self.root.after(0, lambda: self.status_var.set("正在解析路由数据..."))

            # 更新缓存
            self._routes_cache = routes
            self._routes_cache_time = current_time

            # 在主线程中更新UI
            self.root.after(0, self._update_routes_display, routes)

        except Exception as e:
            logger.error(f"异步加载路由失败: {e}")
            self.root.after(0, self._show_load_error, str(e))

    def _update_routes_display(self, routes):
        """更新路由显示（主线程中执行）"""
        try:
            self._is_loading_routes = False
            self.status_var.set("就绪")
            self.log(f"路由数据加载完成，共 {len(routes)} 条路由")

            # 清除现有条目
            for item in self.active_tree.get_children():
                self.active_tree.delete(item)
            for item in self.persistent_tree.get_children():
                self.persistent_tree.delete(item)

            # 更新持久路由列标题
            version = self.version_var.get()
            self._update_persistent_columns_headers(version)

            # 分离活动路由和持久路由
            active_routes = []
            persistent_routes = []

            for route in routes:
                if route.get('persistent', False):
                    persistent_routes.append(route)
                else:
                    active_routes.append(route)

            # 显示活动路由
            for route in active_routes:
                if version == "IPv4":
                    values = (
                        route.get('destination', ''),
                        route.get('netmask', ''),
                        route.get('gateway', ''),
                        route.get('interface', ''),
                        route.get('metric', '')
                    )
                else:  # IPv6
                    values = (
                        route.get('destination', ''),
                        route.get('netmask', ''),
                        route.get('gateway', ''),
                        route.get('interface', ''),
                        route.get('metric', '')
                    )
                self.active_tree.insert('', tk.END, values=values)

            # 显示持久路由
            for route in persistent_routes:
                if version == "IPv4":
                    values = (
                        route.get('destination', ''),
                        route.get('netmask', ''),
                        route.get('gateway', ''),
                        route.get('interface', ''),
                        route.get('metric', '')
                    )
                else:  # IPv6
                    values = (
                        route.get('destination', ''),
                        route.get('netmask', ''),
                        route.get('gateway', ''),
                        route.get('interface', ''),
                        route.get('metric', '')
                    )
                self.persistent_tree.insert('', tk.END, values=values)

            self.log(f"显示 {len(active_routes)} 条活动路由，{len(persistent_routes)} 条持久路由")

        except Exception as e:
            self.log(f"更新路由显示失败: {str(e)}")
            self.status_var.set("更新路由显示失败")

    def _show_load_error(self, error_message):
        """显示加载错误（主线程中执行）"""
        self._is_loading_routes = False
        self.status_var.set("路由加载失败")
        self.log(f"路由加载失败: {error_message}")
        messagebox.showerror("加载错误", f"加载路由信息失败：{error_message}")

    def refresh_routes(self, force_refresh=False):
        """刷新路由表显示"""
        if self._is_loading_routes and not force_refresh:
            self.log("路由正在加载中，请稍候...")
            return

        # 如果是强制刷新，清除缓存
        if force_refresh:
            self._routes_cache = None
            self._routes_cache_time = 0
            self.log("强制刷新路由数据，清除缓存")

        # 使用异步加载
        self._delayed_refresh_routes()

    def test_route_command(self):
        """测试route命令"""
        self.log("=== 测试Route命令 ===")

        # 测试一个简单的路由添加和删除
        test_dest = "169.254.200.0"
        test_mask = "255.255.255.0"
        test_gateway = "169.254.1.1"

        add_cmd = f'route -4 add {test_dest} mask {test_mask} {test_gateway}'
        delete_cmd = f'route -4 delete {test_dest}'

        self.log(f"执行添加命令: {add_cmd}")
        try:
            result = subprocess.run(add_cmd,
                                  capture_output=True,
                                  text=True,
                                  shell=True,
                                  timeout=10,
                                  encoding='utf-8',
                                  errors='ignore')
            if result.returncode == 0:
                self.log("添加成功!")
                self.log(f"输出: {result.stdout}")

                # 立即删除
                self.log(f"执行删除命令: {delete_cmd}")
                result = subprocess.run(delete_cmd,
                                      capture_output=True,
                                      text=True,
                                      shell=True,
                                      timeout=10,
                                      encoding='utf-8',
                                      errors='ignore')
                if result.returncode == 0:
                    self.log("删除成功!")
                else:
                    self.log(f"删除失败: {result.stderr}")
            else:
                self.log(f"添加失败: {result.stderr}")
                self.log(f"返回码: {result.returncode}")
        except Exception as e:
            self.log(f"命令执行异常: {str(e)}")

    def get_network_interfaces(self, force_refresh=False):
        """获取系统网络接口列表（带缓存）"""
        current_time = time.time()

        # 检查缓存是否有效
        if (not force_refresh and
            self._interfaces_cache is not None and
            current_time - self._interfaces_cache_time < self._interfaces_cache_duration):
            self.log(f"使用缓存的接口信息 ({len(self._interfaces_cache)} 个接口)")
            return self._interfaces_cache.copy()

        # 缓存失效或强制刷新，重新获取
        interfaces = []
        try:
            if self.is_windows:
                # 获取详细接口信息
                interfaces = self._get_windows_interfaces()
            else:
                # Linux/Mac系统
                interfaces = self._get_unix_interfaces()

            # 按接口编号排序
            interfaces.sort(key=lambda x: x['number'])

            # 更新缓存
            self._interfaces_cache = interfaces.copy()
            self._interfaces_cache_time = current_time

            self.log(f"获取到 {len(interfaces)} 个网络接口")

        except Exception as e:
            self.log(f"获取网络接口失败: {e}")
            # 如果获取失败但有过期缓存，返回过期缓存
            if self._interfaces_cache is not None:
                self.log("使用过期的缓存接口信息")
                return self._interfaces_cache.copy()

        return interfaces

    def _get_windows_interfaces(self):
        """获取Windows系统的网络接口信息（优化版）"""
        interfaces = []

        try:
            # 使用route print获取接口编号和基本信息
            route_result = subprocess.run(['route', 'print'],
                                       capture_output=True,
                                       text=True,
                                       shell=True,
                                       timeout=5,  # 减少超时时间
                                       encoding='utf-8',
                                       errors='ignore')

            if route_result.returncode == 0:
                lines = route_result.stdout.split('\n')
                in_interface_list = False

                # 预编译正则表达式提高性能
                mac_pattern = re.compile(r'([0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2})')
                ip_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')

                for line in lines:
                    line = line.strip()
                    if 'Interface List' in line:
                        in_interface_list = True
                        continue
                    elif in_interface_list and ('================================================================' in line or 'IPv4 Route Table' in line or 'IPv6 Route Table' in line):
                        break

                    if in_interface_list and line and ('....' in line or '...' in line):
                        # 优化接口信息解析
                        if '....' in line:
                            parts = line.split('....', 1)  # 只分割第一个
                        else:
                            parts = line.split('...', 1)

                        if len(parts) >= 2:
                            interface_num = parts[0].strip()
                            rest_part = parts[1].strip()

                            # 提取真正的接口编号（去除MAC地址前缀）
                            if '....' in interface_num:
                                interface_num = interface_num.split('....')[0].strip()
                            elif '...' in interface_num:
                                interface_num = interface_num.split('...')[0].strip()

                            # 提取接口名称
                            interface_name = ''
                            if '......' in rest_part:
                                interface_name = rest_part.split('......')[-1].strip()
                            else:
                                interface_name = rest_part.strip()

                            # 清理接口名称，移除MAC地址和其他特殊字符
                            interface_name = interface_name.lstrip('.:').strip()
                            interface_name = mac_pattern.sub('', interface_name).strip()

                            # 简化IP地址获取 - 只从route print输出中提取
                            ips = []
                            for ip_line in lines:
                                if interface_num in ip_line:
                                    ip_match = ip_pattern.search(ip_line)
                                    if ip_match:
                                        ip = ip_match.group(1)
                                        if ip not in ['127.0.0.1', '0.0.0.0', '255.255.255.255'] and ip not in ips:
                                            ips.append(ip)
                                            if len(ips) >= 2:  # 只取前2个IP
                                                break

                            # 构建显示名称
                            if interface_name:
                                display_name = interface_name
                            else:
                                display_name = f"接口 {interface_num}"

                            if ips:
                                display_name += f" ({', '.join(ips)})"

                            interfaces.append({
                                'number': interface_num,
                                'name': interface_name if interface_name else f"接口 {interface_num}",
                                'display': f"{interface_num} - {display_name}",
                                'ips': ips,
                                'mac': None
                            })

        except subprocess.TimeoutExpired:
            self.log("获取接口信息超时")
        except Exception as e:
            self.log(f"获取Windows接口信息失败: {e}")

        return interfaces

  
    def _get_unix_interfaces(self):
        """获取Unix/Linux系统的网络接口信息"""
        interfaces = []
        try:
            # 获取接口信息
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_interface = None

                for line in lines:
                    line = line.strip()
                    if line and ':' in line and not line.startswith(' '):
                        # 接口行: 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
                        parts = line.split(':', 2)
                        if len(parts) >= 2:
                            interface_num = parts[0].strip()
                            interface_name = parts[1].strip()
                            current_interface = {
                                'number': interface_num,
                                'name': interface_name,
                                'ips': []
                            }
                            interfaces.append(current_interface)

                    elif current_interface and 'inet ' in line:
                        # IP地址行: inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
                        ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            current_interface['ips'].append(ip_match.group(1))

        except Exception as e:
            self.log(f"获取Unix接口信息失败: {e}")

        # 转换为统一格式
        formatted_interfaces = []
        for interface in interfaces:
            display_name = interface['name']
            if interface['ips']:
                display_name += f" ({', '.join(interface['ips'][:2])})"

            formatted_interfaces.append({
                'number': interface['number'],
                'name': interface['name'],
                'display': f"{interface['number']} - {display_name}",
                'ips': interface['ips'],
                'mac': None
            })

        return formatted_interfaces

    def add_route(self):
        """添加新路由 - 修复版"""
        version = self.version_var.get()
        self.log(f"=== 开始添加{version}路由 ===")

        # 创建路由对话框
        dialog = EnhancedRouteDialog(self.root, f"添加{version}路由", version, self)
        self.log("路由对话框已创建")

        # 等待对话框关闭
        self.root.wait_window(dialog.dialog)
        self.log(f"对话框已关闭")

        # 检查是否获取到了结果
        if not dialog.result:
            self.log("用户取消了操作")
            messagebox.showinfo("提示", "操作已取消")
            return

        route_data = dialog.result
        self.log(f"获取到路由数据: {route_data}")

        # 验证输入数据
        error_msg = self.validate_route_data(route_data, version)
        if error_msg:
            self.log(f"输入验证失败: {error_msg}")
            messagebox.showerror("输入错误", error_msg)
            return

        # 构建命令
        try:
            if self.is_windows:
                if version == "IPv4":
                    cmd = f'route -4 add {route_data["destination"]} mask {route_data["netmask"]} {route_data["gateway"]}'
                    # 添加持久路由参数
                    if route_data.get('persistent', False):
                        cmd += ' -p'
                    # 添加接口参数
                    if route_data.get('interface'):
                        cmd += f' IF {route_data["interface"]}'
                    if route_data.get('metric'):
                        cmd += f' metric {route_data["metric"]}'
                else:
                    prefix_len = route_data.get("prefix_length", "64")
                    if route_data.get('gateway') and route_data['gateway'] != 'On-link':
                        cmd = f'route -6 add {route_data["destination"]}/{prefix_len} {route_data["gateway"]}'
                    else:
                        cmd = f'route -6 add {route_data["destination"]}/{prefix_len}'
                    # 添加持久路由参数
                    if route_data.get('persistent', False):
                        cmd += ' -p'
                    # 添加接口参数
                    if route_data.get('interface'):
                        cmd += f' IF {route_data["interface"]}'
                    if route_data.get('metric'):
                        cmd += f' metric {route_data["metric"]}'

                self.log(f"准备执行命令: {cmd}")

                # 显示操作确认
                if not messagebox.askyesno("确认操作", f"确定要添加以下路由吗？\n\n{cmd}"):
                    self.log("用户确认取消")
                    return

                # 执行命令
                result = subprocess.run(cmd,
                                      capture_output=True,
                                      text=True,
                                      shell=True,
                                      timeout=10,
                                      encoding='utf-8',
                                      errors='ignore')

                if result.returncode == 0:
                    self.log("命令执行成功!")
                    self.log(f"输出: {result.stdout}")
                    messagebox.showinfo("成功", "路由添加成功")
                    self.refresh_routes()
                else:
                    self.log(f"命令执行失败! 返回码: {result.returncode}")
                    self.log(f"错误输出: {result.stderr}")

                    # 提供详细的错误分析和解决建议
                    error_details = self.analyze_route_error(result.stderr, cmd, version)
                    messagebox.showerror("添加路由失败", error_details)

        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时:\n\n"
            error_msg += f"命令: {cmd}\n\n"
            error_msg += "可能的原因:\n"
            error_msg += "1. 网络连接问题\n"
            error_msg += "2. 系统响应缓慢\n"
            error_msg += "3. 权限问题\n\n"
            error_msg += "建议: 请稍后重试或检查网络连接"

            self.log(f"命令执行超时: {cmd}")
            messagebox.showerror("错误", error_msg)

        except subprocess.CalledProcessError as e:
            self.log(f"命令执行异常: {str(e)}")
            error_msg = f"路由添加过程中发生错误:\n\n"
            error_msg += f"错误信息: {str(e)}\n"
            error_msg += f"命令: {cmd if 'cmd' in locals() else '未知'}\n\n"
            error_msg += "建议:\n"
            error_msg += "1. 确保以管理员身份运行程序\n"
            error_msg += "2. 检查网络连接状态\n"
            error_msg += "3. 验证输入的路由参数是否正确"

            messagebox.showerror("错误", error_msg)

        except Exception as e:
            self.log(f"其他异常: {str(e)}")
            messagebox.showerror("错误", f"添加路由失败: {str(e)}")

    def validate_route_data(self, route_data, version):
        """验证路由数据的有效性"""
        if version == "IPv4":
            try:
                # 验证目标网络
                dest = route_data.get("destination", "").strip()
                if not dest:
                    return "请输入目标网络地址"

                # 验证子网掩码
                mask = route_data.get("netmask", "").strip()
                if not mask:
                    return "请输入子网掩码"

                try:
                    ipaddress.ip_network(f"{dest}/{mask}", strict=False)
                except ValueError as e:
                    return f"目标网络或子网掩码格式不正确:\n{str(e)}"

                # 验证网关地址
                gateway = route_data.get("gateway", "").strip()
                if gateway and gateway != "On-link":
                    try:
                        ipaddress.ip_address(gateway)
                    except ValueError as e:
                        return f"网关地址格式不正确:\n{str(e)}"

                # 验证接口
                interface = route_data.get("interface", "").strip()
                if interface:
                    if not interface.isdigit() or int(interface) < 1:
                        return "接口编号必须是正整数"

                # 验证跃点数
                metric = route_data.get("metric", "").strip()
                if metric:
                    if not metric.isdigit() or int(metric) < 0:
                        return "跃点数必须是非负整数"

            except Exception as e:
                return f"数据验证过程中发生错误: {str(e)}"

        else:  # IPv6
            try:
                # 验证目标网络
                dest = route_data.get("destination", "").strip()
                if not dest:
                    return "请输入目标网络地址"

                # 验证前缀长度
                prefix_len = route_data.get("prefix_length", "").strip()
                if not prefix_len:
                    return "请输入前缀长度"

                if not prefix_len.isdigit() or not (0 <= int(prefix_len) <= 128):
                    return "前缀长度必须是0-128之间的整数"

                try:
                    ipaddress.ip_network(f"{dest}/{prefix_len}", strict=False)
                except ValueError as e:
                    return f"目标网络或前缀长度格式不正确:\n{str(e)}"

                # 验证网关地址
                gateway = route_data.get("gateway", "").strip()
                if gateway and gateway != "On-link":
                    try:
                        ipaddress.ip_address(gateway)
                    except ValueError as e:
                        return f"网关地址格式不正确:\n{str(e)}"

                # 验证接口
                interface = route_data.get("interface", "").strip()
                if interface:
                    if not interface.isdigit() or int(interface) < 1:
                        return "接口编号必须是正整数"

                # 验证跃点数
                metric = route_data.get("metric", "").strip()
                if metric:
                    if not metric.isdigit() or int(metric) < 0:
                        return "跃点数必须是非负整数"

            except Exception as e:
                return f"数据验证过程中发生错误: {str(e)}"

        return None  # 验证通过

    def analyze_route_error(self, stderr, cmd, version):
        """分析路由错误并提供详细建议"""
        error_msg = f"路由添加失败:\n\n"
        error_msg += f"执行的命令: {cmd}\n"
        error_msg += f"错误信息: {stderr}\n\n"
        error_msg += "可能的原因及解决方案:\n\n"

        if "Element not found" in stderr:
            error_msg += "❌ 网关地址不存在或不可达\n"
            error_msg += "   解决方案:\n"
            error_msg += "   1. 使用 'On-link' 作为网关\n"
            error_msg += "   2. 点击'测试命令'检测可用网关\n"
            error_msg += "   3. 使用系统中已存在的网关地址\n\n"

        elif "access is denied" in stderr.lower() or "拒绝访问" in stderr:
            error_msg += "❌ 权限不足\n"
            error_msg += "   解决方案:\n"
            error_msg += "   1. 右键点击命令提示符，选择'以管理员身份运行'\n"
            error_msg += "   2. 在管理员命令提示符中运行程序\n\n"

        elif "invalid parameter" in stderr.lower() or "参数无效" in stderr:
            error_msg += "❌ 参数格式错误\n"
            error_msg += "   解决方案:\n"
            error_msg += "   1. 检查IP地址格式是否正确\n"
            error_msg += "   2. 检查子网掩码或前缀长度\n"
            error_msg += "   3. 确保所有参数都有值\n\n"

        elif "already exists" in stderr.lower() or "已存在" in stderr:
            error_msg += "❌ 路由已存在\n"
            error_msg += "   解决方案:\n"
            error_msg += "   1. 该路由已经存在，无需重复添加\n"
            error_msg += "   2. 如需修改，请先删除现有路由\n\n"

        else:
            error_msg += "❌ 未知错误\n"
            error_msg += "   通用解决方案:\n"
            error_msg += "   1. 确保网络连接正常\n"
            error_msg += "   2. 检查防火墙设置\n"
            error_msg += "   3. 重启网络适配器\n\n"

        if version == "IPv4":
            error_msg += "💡 IPv4路由建议:\n"
            error_msg += "   - 目标网络: 如 192.168.100.0\n"
            error_msg += "   - 子网掩码: 如 255.255.255.0\n"
            error_msg += "   - 网关: IP地址或 'On-link'\n\n"
        else:
            error_msg += "💡 IPv6路由建议:\n"
            error_msg += "   - 目标网络: 如 2001:db8::\n"
            error_msg += "   - 前缀长度: 如 32, 64, 128\n"
            error_msg += "   - 网关: IPv6地址或 'On-link'\n\n"

        error_msg += "🔧 调试步骤:\n"
        error_msg += "   1. 点击'测试命令'按钮测试基础功能\n"
        error_msg += "   2. 查看日志区域的详细错误信息\n"
        error_msg += "   3. 尝试在命令提示符中手动执行命令"

        return error_msg

    def show_ip_info(self):
        """显示设备IP信息"""
        try:
            self.log("正在打开设备IP信息窗口...")
            ip_dialog = IPInfoDialog(self.root, self)
            self.root.wait_window(ip_dialog.dialog)
            self.log("设备IP信息窗口已关闭")
        except Exception as e:
            self.log(f"打开IP信息窗口失败: {str(e)}")
            messagebox.showerror("错误", f"打开IP信息窗口失败: {str(e)}")

    def show_active_context_menu(self, event):
        """显示活动路由右键菜单"""
        # 确保右键点击的项目被选中
        item = self.active_tree.identify_row(event.y)
        if item:
            self.active_tree.selection_set(item)
            self.active_context_menu.post(event.x_root, event.y_root)

    def show_persistent_context_menu(self, event):
        """显示持久路由右键菜单"""
        # 确保右键点击的项目被选中
        item = self.persistent_tree.identify_row(event.y)
        if item:
            self.persistent_tree.selection_set(item)
            self.persistent_context_menu.post(event.x_root, event.y_root)

    def delete_route_from_context(self):
        """从右键菜单删除路由"""
        # 直接调用现有的删除路由方法
        self.delete_route()

    def delete_route(self):
        """删除选中路由"""
        # 确定当前选中的是哪个表格
        current_tab = None

        # 尝试从活动路由表格获取选择
        selection = self.active_tree.selection()
        if selection:
            current_tab = "active"
            tree = self.active_tree
        else:
            # 尝试从持久路由表格获取选择
            selection = self.persistent_tree.selection()
            if selection:
                current_tab = "persistent"
                tree = self.persistent_tree

        if not selection or not current_tab:
            messagebox.showwarning("警告", "请先选择要删除的路由")
            return

        if messagebox.askyesno("确认", "确定要删除选中的路由吗？"):
            item = selection[0]
            values = tree.item(item, 'values')
            version = self.version_var.get()

            # 根据表格类型调整索引
            if current_tab == "active":
                # 活动路由表格: 0-目标网络, 1-子网掩码/前缀长度, 2-网关, 3-接口, 4-跃点数
                destination = values[0]
                netmask_or_prefix = values[1]
            else:
                # 持久路由表格: 0-目标网络, 1-子网掩码, 2-网关地址, 3-跃点数
                destination = values[0]
                netmask_or_prefix = values[1]

            self.log(f"删除路由: {destination}")

            try:
                if self.is_windows:
                    if version == "IPv4":
                        cmd = f'route -4 delete {destination}'
                    else:
                        if netmask_or_prefix:
                            cmd = f'route -6 delete {destination}/{netmask_or_prefix}'
                        else:
                            cmd = f'route -6 delete {destination}'

                    self.log(f"执行删除命令: {cmd}")
                    result = subprocess.run(cmd,
                                          capture_output=True,
                                          text=True,
                                          shell=True,
                                          timeout=10,
                                          encoding='utf-8',
                                          errors='ignore')

                    if result.returncode == 0:
                        self.log("删除成功")
                        messagebox.showinfo("成功", "路由删除成功")
                        self.refresh_routes()
                    else:
                        self.log(f"删除失败: {result.stderr}")
                        messagebox.showerror("错误", f"删除路由失败: {result.stderr}")

            except Exception as e:
                self.log(f"删除异常: {str(e)}")
                messagebox.showerror("错误", f"删除路由失败: {str(e)}")

    def run(self):
        """运行应用程序"""
        self.root.mainloop()

class RouteDialog:
    def __init__(self, parent, title, version="IPv4"):
        self.result = None
        self.version = version

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 调试信息
        debug_frame = ttk.LabelFrame(self.dialog, text="调试信息", padding="10")
        debug_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        debug_text = tk.Text(debug_frame, height=6, wrap=tk.WORD)
        debug_text.pack(fill=tk.BOTH, expand=True)

        debug_text.insert(tk.END, f"版本: {version}\n")
        debug_text.insert(tk.END, f"操作系统: {platform.system()}\n")
        debug_text.insert(tk.END, f"管理员权限: {'需要' if platform.system() == 'Windows' else '可能需要'}\n\n")

        if version == "IPv4":
            debug_text.insert(tk.END, "IPv4路由示例:\n")
            debug_text.insert(tk.END, "目标: 192.168.100.0\n")
            debug_text.insert(tk.END, "子网掩码: 255.255.255.0\n")
            debug_text.insert(tk.END, "网关: 192.168.1.1\n")
        else:
            debug_text.insert(tk.END, "IPv6路由示例:\n")
            debug_text.insert(tk.END, "目标: 2001:db8::\n")
            debug_text.insert(tk.END, "前缀长度: 32\n")
            debug_text.insert(tk.END, "网关: fe80::1\n")

        debug_text.config(state=tk.DISABLED)

        # 输入字段
        input_frame = ttk.LabelFrame(self.dialog, text="路由信息", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        if version == "IPv4":
            fields = [
                ("目标网络:", "destination", "192.168.100.0"),
                ("子网掩码:", "netmask", "255.255.255.0"),
                ("网关:", "gateway", "192.168.1.1"),
                ("跃点数:", "metric", "")
            ]
        else:  # IPv6
            fields = [
                ("目标网络:", "destination", "2001:db8::"),
                ("前缀长度:", "prefix_length", "32"),
                ("网关:", "gateway", "fe80::1"),
                ("跃点数:", "metric", "")
            ]

        self.entries = {}
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            entry = ttk.Entry(input_frame, width=40)
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky=(tk.W, tk.E))
            self.entries[key] = entry

        input_frame.columnconfigure(1, weight=1)

        # 按钮
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def ok_clicked(self):
        self.result = {key: entry.get() for key, entry in self.entries.items()}
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()

class EnhancedRouteDialog:
    """增强的路由对话框，包含接口选择功能"""
    def __init__(self, parent, title, version, manager):
        self.result = None
        self.version = version
        self.manager = manager
        self.interface_combo = None
        self.interface_mapping = {}

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("700x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 设置对话框样式
        self.dialog.configure(bg="#f0f0f0")

        # 标题区域
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        title_label = ttk.Label(title_frame, text=f"添加{version}路由",
                               font=("Arial", 14))
        title_label.pack(side=tk.LEFT)

        # 使用说明区域
        help_frame = ttk.LabelFrame(self.dialog, text="使用说明", padding="12")
        help_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        if version == "IPv4":
            help_content = """IPv4路由参数说明：
• 目标网络：要访问的网络地址，例如 192.168.100.0
• 子网掩码：网络子网掩码，例如 255.255.255.0
• 网关地址：路由网关IP地址，或使用 On-link
• 网络接口：可选，留空则自动选择
• 跃点数：可选，数值越小优先级越高
• 持久路由：勾选后系统重启仍保留此路由"""
        else:
            help_content = """IPv6路由参数说明：
• 目标网络：要访问的IPv6网络地址，例如 2001:db8::
• 前缀长度：网络前缀长度，例如 32、64、128
• 网关地址：IPv6网关地址，或使用 On-link
• 网络接口：可选，留空则自动选择
• 跃点数：可选，数值越小优先级越高
• 持久路由：勾选后系统重启仍保留此路由"""

        help_text = tk.Text(help_frame, height=7, wrap=tk.WORD, font=("Arial", 9))
        help_text.pack(fill=tk.X)
        help_text.config(bg="#f8f9fa", fg="#495057", relief=tk.FLAT)
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

        # 输入字段区域
        input_frame = ttk.LabelFrame(self.dialog, text="路由参数配置", padding="15")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        if version == "IPv4":
            fields = [
                ("目标网络:", "destination", "192.168.100.0", "例如：192.168.100.0"),
                ("子网掩码:", "netmask", "255.255.255.0", "例如：255.255.255.0"),
                ("网关地址:", "gateway", "On-link", "IP地址或 On-link"),
                ("网络接口:", "interface", "", "可选，留空自动选择"),
                ("跃点数:", "metric", "", "可选，数值越小优先级越高")
            ]
        else:  # IPv6
            fields = [
                ("目标网络:", "destination", "2001:db8::", "例如：2001:db8::"),
                ("前缀长度:", "prefix_length", "32", "例如：32, 64, 128"),
                ("网关地址:", "gateway", "fe80::1", "IPv6地址或 On-link"),
                ("网络接口:", "interface", "", "可选，留空自动选择"),
                ("跃点数:", "metric", "", "可选，数值越小优先级越高")
            ]

        self.entries = {}
        for i, (label, key, default, hint) in enumerate(fields):
            # 标签
            label_widget = ttk.Label(input_frame, text=label, font=("Arial", 10))
            label_widget.grid(row=i, column=0, sticky=tk.W, padx=(0, 15), pady=(10, 5))

            if key == "interface":
                # 接口字段使用下拉框
                interface_container = ttk.Frame(input_frame)
                interface_container.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
                interface_container.columnconfigure(0, weight=1)

                self.interface_var = tk.StringVar()
                self.interface_combo = ttk.Combobox(interface_container, textvariable=self.interface_var,
                                                 font=("Arial", 10), height=8)
                self.interface_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))

                # 加载状态指示器
                self.loading_label = ttk.Label(interface_container, text="加载中...",
                                            font=("Arial", 9), foreground="#6c757d")
                self.loading_label.grid(row=0, column=1, padx=(10, 0))

                self.interface_combo['values'] = ["正在加载接口信息..."]
                self.interface_combo.set("正在加载接口信息...")
                self.interface_combo.config(state='readonly')

                # 启动后台线程加载接口信息
                threading.Thread(target=self._load_interfaces_async, daemon=True).start()

                self.entries[key] = self.interface_combo
            else:
                # 输入框容器
                entry_container = ttk.Frame(input_frame)
                entry_container.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
                entry_container.columnconfigure(0, weight=1)

                entry = ttk.Entry(entry_container, font=("Arial", 11))
                entry.insert(0, default)
                entry.grid(row=0, column=0, sticky=(tk.W, tk.E))

                # 添加提示文本
                hint_label = ttk.Label(entry_container, text=hint, font=("Arial", 8),
                                    foreground="#6c757d")
                hint_label.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))

                self.entries[key] = entry

        input_frame.columnconfigure(1, weight=1)

        # 持久路由选项（单独一行）
        persistent_frame = ttk.Frame(input_frame)
        persistent_frame.grid(row=len(fields), column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))

        self.persistent_var = tk.BooleanVar()
        persistent_check = ttk.Checkbutton(persistent_frame,
                                        text="添加为持久路由（系统重启后保留）",
                                        variable=self.persistent_var)
        persistent_check.pack(side=tk.LEFT)
        self.entries["persistent"] = self.persistent_var

        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        # 按钮样式
        button_style = ttk.Style()
        button_style.configure("Dialog.TButton", font=("Arial", 10), padding=(20, 8))

        ttk.Button(button_frame, text="确定添加", command=self.ok_clicked,
                  style="Dialog.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked,
                  style="Dialog.TButton").pack(side=tk.RIGHT)

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _load_interfaces_async(self):
        """异步加载网络接口信息"""
        try:
            # 获取系统接口
            interfaces = [("自动选择", "")]

            try:
                system_interfaces = self.manager.get_network_interfaces()
                for interface in system_interfaces:
                    display_name = interface['display']
                    interface_num = interface['number']
                    interfaces.append((display_name, interface_num))
            except Exception as e:
                print(f"获取接口失败: {e}")

            # 在主线程中更新UI
            self.dialog.after(0, self._update_interface_combo, interfaces)

        except Exception as e:
            print(f"异步加载接口失败: {e}")
            # 在主线程中更新UI显示错误
            self.dialog.after(0, self._update_interface_combo_error)

    def _update_interface_combo(self, interfaces):
        """在主线程中更新接口下拉框"""
        try:
            if self.interface_combo and self.interface_combo.winfo_exists():
                # 设置下拉框选项
                self.interface_combo['values'] = [interface[0] for interface in interfaces]
                self.interface_combo.set("自动选择")
                self.interface_combo.config(state='normal')

                # 保存接口映射
                self.interface_mapping = {interface[0]: interface[1] for interface in interfaces}

                # 隐藏加载标签
                if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
                    self.loading_label.config(text="加载完成", foreground="green")
                    self.dialog.after(1500, lambda: self.loading_label.destroy())
        except:
            pass

    def _update_interface_combo_error(self):
        """在主线程中更新接口下拉框显示错误"""
        try:
            if self.interface_combo and self.interface_combo.winfo_exists():
                self.interface_combo['values'] = ["自动选择", "获取接口信息失败"]
                self.interface_combo.set("自动选择")
                self.interface_combo.config(state='normal')
                self.interface_mapping = {"自动选择": "", "获取接口信息失败": ""}

                # 更新加载标签显示错误
                if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
                    self.loading_label.config(text="加载失败", foreground="red")
                    self.dialog.after(3000, lambda: self.loading_label.destroy())
        except:
            pass

    def ok_clicked(self):
        # 收集所有输入数据
        route_data = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ttk.Combobox):
                # 接口下拉框
                selected_text = widget.get()
                mapped_value = self.interface_mapping.get(selected_text, "")
                route_data[key] = mapped_value
            elif isinstance(widget, tk.BooleanVar):
                # 持久路由复选框
                route_data[key] = widget.get()
            else:
                # 普通输入框
                route_data[key] = widget.get().strip()

        self.result = route_data
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()

class IPInfoDialog:
    """设备IP信息对话框 - 优化版"""
    def __init__(self, parent, manager):
        self.manager = manager
        self.interfaces_data = []
        self.selected_interface = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("设备IP信息")
        # 调整窗口大小以适应屏幕
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        width = min(1200, int(screen_width * 0.9))
        height = min(800, int(screen_height * 0.85))
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 设置对话框样式
        self.dialog.configure(bg="#f8f9fa")

        # 设置统一的Arial字体样式
        self.setup_fonts()

        # 创建主要布局
        self.setup_layout()

        # 居中显示
        self.dialog.update_idletasks()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # 初始化显示
        self.refresh_interfaces()

    def setup_fonts(self):
        """设置统一的Arial字体样式"""
        # 创建样式对象
        self.style = ttk.Style()

        # 设置通用字体
        self.font_large = ("Arial", 12, "bold")
        self.font_medium = ("Arial", 11, "bold")
        self.font_normal = ("Arial", 10)
        self.font_small = ("Arial", 9)

        # 配置Treeview样式（只保留必要的）
        self.style.configure("IPInfo.Treeview",
                           font=self.font_normal,
                           rowheight=25)
        self.style.configure("IPInfo.Treeview.Heading",
                           font=self.font_medium,
                           padding=(8, 5))

    def setup_layout(self):
        """设置界面布局"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.dialog)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        # 标题
        title_label = ttk.Label(toolbar, text="网络接口IP信息", font=self.font_large)
        title_label.pack(side=tk.LEFT, padx=(10, 20))

        # 创建按钮样式
        button_style = ttk.Style()
        button_style.configure("Tool.TButton", font=self.font_normal, padding=(8, 4))

        # 刷新按钮
        refresh_btn = ttk.Button(toolbar, text="🔄 刷新", command=self.refresh_interfaces,
                               style="Tool.TButton")
        refresh_btn.pack(side=tk.RIGHT, padx=(5, 10))

        # 导出按钮
        export_btn = ttk.Button(toolbar, text="📄 导出", command=self.export_info,
                               style="Tool.TButton")
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 创建主分割区域
        main_paned = ttk.PanedWindow(self.dialog, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧接口列表
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # 接口列表标题
        list_title = ttk.Label(left_frame, text="网络接口列表", font=self.font_medium)
        list_title.pack(pady=(10, 5))

        # 接口列表框架
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=(10, 5), pady=(0, 10))

        # 创建接口列表Treeview
        columns = ("status", "ipv4", "ipv6")
        self.interface_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings",
                                       height=15, style="IPInfo.Treeview")

        # 设置列标题
        self.interface_tree.heading("#0", text="接口名称", anchor=tk.W)
        self.interface_tree.heading("status", text="状态", anchor=tk.CENTER)
        self.interface_tree.heading("ipv4", text="IPv4地址", anchor=tk.W)
        self.interface_tree.heading("ipv6", text="IPv6地址", anchor=tk.W)

        # 设置列宽
        self.interface_tree.column("#0", width=200, minwidth=150)
        self.interface_tree.column("status", width=80, minwidth=60)
        self.interface_tree.column("ipv4", width=140, minwidth=100)
        self.interface_tree.column("ipv6", width=200, minwidth=150)

        # 添加滚动条
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.interface_tree.yview)
        self.interface_tree.configure(yscrollcommand=list_scrollbar.set)

        self.interface_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件
        self.interface_tree.bind("<<TreeviewSelect>>", self.on_interface_select)

        # 右侧详细信息
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        # 详细信息标题
        detail_title = ttk.Label(right_frame, text="详细信息", font=self.font_medium)
        detail_title.pack(pady=(10, 5))

        # 详细信息框架
        self.detail_frame = ttk.Frame(right_frame)
        self.detail_frame.pack(fill=tk.BOTH, expand=True, padx=(5, 10), pady=(0, 10))

        # 创建详细信息显示区域
        self.setup_detail_area()

        # 底部状态栏
        status_frame = ttk.Frame(self.dialog)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(5, 10))

        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X)

    def setup_detail_area(self):
        """设置详细信息显示区域"""
        # 创建单一的详细信息显示区域
        self.detail_text = tk.Text(self.detail_frame, wrap=tk.WORD, font=self.font_normal,
                                  bg="white", fg="black", padx=15, pady=15,
                                  relief=tk.FLAT, borderwidth=0)
        detail_scrollbar = ttk.Scrollbar(self.detail_frame, orient=tk.VERTICAL,
                                         command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)

        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 初始显示选择提示
        self.show_selection_hint()

    def show_selection_hint(self):
        """显示选择提示"""
        # 清空详细信息文本控件
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)

        # 添加选择提示
        hint_text = """请从左侧列表中选择一个网络接口
查看详细信息

操作提示：
• 点击左侧接口名称查看详细信息
• 使用 Ctrl+C 复制选中的文本
• 点击"🔄 刷新"更新网络信息
• 点击"📄 导出"保存完整报告"""

        self.detail_text.insert(tk.END, hint_text)
        self.detail_text.config(state=tk.DISABLED)

    def on_interface_select(self, event):
        """处理接口选择事件"""
        selection = self.interface_tree.selection()
        if not selection:
            return

        item = selection[0]
        interface_name = self.interface_tree.item(item, "text")

        # 查找接口详细信息
        selected_interface = None
        for interface in self.interfaces_data:
            if interface.get('name') == interface_name:
                selected_interface = interface
                break

        if selected_interface:
            self.display_interface_detail(selected_interface)
            self.status_var.set(f"已选择: {interface_name}")

    def display_interface_detail(self, interface):
        """显示接口详细信息"""
        self.selected_interface = interface

        # 显示完整的接口详细信息
        self.display_complete_interface_info(interface)

    def display_complete_interface_info(self, interface):
        """显示完整的接口信息，不做任何过滤"""
        # 清空并设置详细信息文本
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)

        # 格式化完整信息 - 简洁清晰
        info_lines = []

        # 基本信息
        info_lines.append(f"接口名称：{interface.get('name', '未知')}")
        info_lines.append(f"接口描述：{interface.get('description', '未知')}")
        info_lines.append(f"连接状态：{interface.get('status', '未知')}")
        info_lines.append("")

        # 硬件信息
        info_lines.append("【硬件信息】")
        mac = interface.get('mac_address', '未获取').strip()
        if mac:
            info_lines.append(f"MAC地址：{mac}")
        else:
            info_lines.append("MAC地址：未获取")
        info_lines.append("")

        # IPv4地址
        info_lines.append("【IPv4地址配置】")
        if interface.get('ipv4_addresses'):
            for i, ip in enumerate(interface['ipv4_addresses'], 1):
                info_lines.append(f"IPv4地址 {i}：{ip}")
        else:
            info_lines.append("IPv4地址：无")
        info_lines.append("")

        # IPv6地址
        info_lines.append("【IPv6地址配置】")
        if interface.get('ipv6_addresses'):
            for i, ipv6 in enumerate(interface['ipv6_addresses'], 1):
                info_lines.append(f"IPv6地址 {i}：{ipv6}")
        else:
            info_lines.append("IPv6地址：无")
        info_lines.append("")

        # 网络配置
        info_lines.append("【网络配置】")

        # 默认网关
        gateway = interface.get('default_gateway', '').strip()
        info_lines.append(f"默认网关：{gateway if gateway else '未配置'}")

        # DNS服务器
        dns_servers = interface.get('dns_servers', [])
        if dns_servers:
            info_lines.append("DNS服务器：")
            for dns in dns_servers:
                info_lines.append(f"  • {dns}")
        else:
            info_lines.append("DNS服务器：未配置")

        # DHCP配置
        dhcp_enabled = interface.get('dhcp_enabled', False)
        info_lines.append(f"DHCP配置：{'已启用' if dhcp_enabled else '未启用或静态配置'}")
        if dhcp_enabled:
            dhcp_server = interface.get('dhcp_server', '').strip()
            if dhcp_server:
                info_lines.append(f"DHCP服务器：{dhcp_server}")

        info_lines.append("")

        # 原始配置数据
        info_lines.append("【原始配置数据】")

        # 显示所有接口属性（排除已显示的主要字段）
        excluded_keys = {'name', 'description', 'status', 'mac_address', 'ipv4_addresses',
                        'ipv6_addresses', 'default_gateway', 'dns_servers', 'dhcp_enabled', 'dhcp_server'}

        has_extra_data = False
        for key, value in interface.items():
            if key not in excluded_keys and value:
                has_extra_data = True
                if isinstance(value, list) and value:
                    info_lines.append(f"{key}：")
                    for item in value[:3]:  # 最多显示前3个，避免过长
                        info_lines.append(f"  • {item}")
                    if len(value) > 3:
                        info_lines.append(f"  ... (还有{len(value)-3}个)")
                elif value:
                    info_lines.append(f"{key}：{value}")

        if not has_extra_data:
            info_lines.append("（无额外配置数据）")

        info_lines.append("")
        info_lines.append(f"生成时间：{self.get_current_time()}")

        # 插入文本
        self.detail_text.insert(tk.END, '\n'.join(info_lines))
        self.detail_text.config(state=tk.DISABLED)

    def refresh_interfaces(self):
        """刷新接口信息"""
        # 清除现有内容
        for item in self.interface_tree.get_children():
            self.interface_tree.delete(item)

        # 获取接口信息
        try:
            self.interfaces_data = self.get_detailed_interfaces()
            self.display_interface_list()
            self.status_var.set(f"已获取 {len(self.interfaces_data)} 个网络接口")
        except Exception as e:
            self.show_error(f"获取接口信息失败: {str(e)}")
            self.status_var.set("获取接口信息失败")

    def display_interface_list(self):
        """显示接口列表"""
        if not self.interfaces_data:
            self.interface_tree.insert("", "end", text="未找到网络接口", values=("", "", ""))
            return

        # 按连接状态排序：已连接的在前
        sorted_interfaces = sorted(self.interfaces_data,
                                 key=lambda x: (0 if x.get('status') == '已连接' else 1, x.get('name', '')))

        for interface in sorted_interfaces:
            # 准备显示值
            status = interface.get('status', '未知')
            if status == '已连接':
                status_display = "🟢 已连接"
            elif status == '断开连接':
                status_display = "🔴 断开"
            else:
                status_display = "⚪ 未知"

            # IP地址显示（简化版本）
            ipv4_display = ""
            if interface.get('ipv4_addresses'):
                ipv4_display = interface['ipv4_addresses'][0]
                if len(interface['ipv4_addresses']) > 1:
                    ipv4_display += f" (+{len(interface['ipv4_addresses'])-1})"

            ipv6_display = ""
            if interface.get('ipv6_addresses'):
                # 只显示第一个IPv6地址，并简化长地址
                first_ipv6 = interface['ipv6_addresses'][0]
                if len(first_ipv6) > 20:
                    ipv6_display = first_ipv6[:18] + "..."
                else:
                    ipv6_display = first_ipv6
                if len(interface['ipv6_addresses']) > 1:
                    ipv6_display += f" (+{len(interface['ipv6_addresses'])-1})"

            # 插入到树形控件
            self.interface_tree.insert("", "end",
                                     text=interface.get('name', '未知接口'),
                                     values=(status_display, ipv4_display, ipv6_display))

        # 自动选择第一个已连接的接口
        for i, interface in enumerate(sorted_interfaces):
            if interface.get('status') == '已连接':
                items = self.interface_tree.get_children()
                if items and i < len(items):
                    self.interface_tree.selection_set(items[i])
                    self.interface_tree.see(items[i])
                    self.on_interface_select(None)
                    break

    def export_info(self):
        """导出网络接口信息"""
        if not self.interfaces_data:
            messagebox.showwarning("提示", "没有可导出的接口信息")
            return

        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="导出网络接口信息",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 50 + "\n")
                    f.write("网络接口信息报告\n")
                    f.write(f"生成时间: {self.get_current_time()}\n")
                    f.write("=" * 50 + "\n\n")

                    for interface in self.interfaces_data:
                        f.write(f"接口名称: {interface.get('name', '未知')}\n")
                        f.write(f"连接状态: {interface.get('status', '未知')}\n")
                        f.write(f"MAC地址: {interface.get('mac_address', '未获取')}\n")

                        if interface.get('ipv4_addresses'):
                            f.write("IPv4地址:\n")
                            for ip in interface['ipv4_addresses']:
                                f.write(f"  - {ip}\n")

                        if interface.get('ipv6_addresses'):
                            f.write("IPv6地址:\n")
                            for ipv6 in interface['ipv6_addresses']:
                                f.write(f"  - {ipv6}\n")

                        if interface.get('default_gateway'):
                            f.write(f"默认网关: {interface['default_gateway']}\n")

                        if interface.get('dns_servers'):
                            f.write("DNS服务器:\n")
                            for dns in interface['dns_servers']:
                                f.write(f"  - {dns}\n")

                        if interface.get('dhcp_enabled'):
                            f.write(f"DHCP: 已启用 (服务器: {interface.get('dhcp_server', '未知')})\n")
                        else:
                            f.write("DHCP: 未启用或静态配置\n")

                        f.write("-" * 50 + "\n\n")

                messagebox.showinfo("成功", f"网络接口信息已导出到:\n{filename}")
                self.status_var.set(f"已导出到: {filename}")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
            self.status_var.set("导出失败")

    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def show_error(self, error_message):
        """显示错误信息"""
        messagebox.showerror("错误", error_message)

    def close_dialog(self):
        """关闭对话框"""
        self.dialog.destroy()

    def get_detailed_interfaces(self):
        """获取详细的网络接口信息"""
        interfaces = []

        try:
            if self.manager.is_windows:
                interfaces = self._get_windows_detailed_interfaces()
            else:
                interfaces = self._get_unix_detailed_interfaces()
        except Exception as e:
            self.manager.log(f"获取详细接口信息失败: {e}")

        return interfaces

    def _get_windows_detailed_interfaces(self):
        """获取Windows系统的详细网络接口信息"""
        interfaces = []

        try:
            # 获取IP配置信息
            ipconfig_result = subprocess.run(['ipconfig', '/all'],
                                           capture_output=True,
                                           text=True,
                                           shell=True,
                                           timeout=10,
                                           encoding='gbk',
                                           errors='ignore')

            if ipconfig_result.returncode == 0:
                interfaces = self._parse_ipconfig_output(ipconfig_result.stdout)

        except subprocess.TimeoutExpired:
            self.manager.log("获取IP配置信息超时")
        except Exception as e:
            self.manager.log(f"获取Windows详细接口信息失败: {e}")

        return interfaces

    def _parse_ipconfig_output(self, output):
        """解析ipconfig输出"""
        interfaces = []
        lines = output.split('\n')
        current_interface = None

        for line in lines:
            line = line.strip()

            # 检测新的适配器（扩展匹配范围）
            if (line.startswith('以太网适配器') or line.startswith('无线') or
                line.startswith('Ethernet adapter') or line.startswith('Wireless') or
                line.startswith('Mobile Broadband') or 'adapter' in line.lower() or
                'Unknown adapter' in line or 'Description' in line and 'Adapter' in line):

                if current_interface:
                    # 如果有IP地址且状态不是明确的断开连接，则设为已连接
                    if (current_interface['status'] == '未知' and
                        (current_interface['ipv4_addresses'] or current_interface['ipv6_addresses'])):
                        current_interface['status'] = '已连接'
                    interfaces.append(current_interface)

                # 提取适配器名称
                adapter_name = line
                if ':' in line:
                    adapter_name = line.split(':', 1)[0].strip()
                elif '.' in line and 'Description' in line:
                    # 处理以Description开头的行
                    adapter_name = line.replace('Description . . . . . . . . . . . :', '').strip()
                    if 'Adapter' in adapter_name:
                        adapter_name = adapter_name.replace('Adapter', '适配器').strip()

                current_interface = {
                    'name': adapter_name,
                    'description': adapter_name,
                    'status': '未知',
                    'mac_address': '',
                    'ipv4_addresses': [],
                    'ipv6_addresses': [],
                    'default_gateway': '',
                    'dns_servers': [],
                    'dhcp_enabled': False,
                    'dhcp_server': ''
                }

            elif current_interface:
                # 解析各种信息 - 改进状态检测

                # 媒体状态检测（明确的断开连接状态）
                if ('Media disconnected' in line or
                    '媒体已断开连接' in line or
                    ('Media State' in line and 'Media disconnected' in line)):
                    current_interface['status'] = '断开连接'

                # MAC地址
                elif ('物理地址' in line or 'Physical Address' in line):
                    mac = line.split(':', 1)[1].strip() if ':' in line else ''
                    current_interface['mac_address'] = mac

                # IPv4地址
                elif ('IPv4 地址' in line or 'IPv4 Address' in line):
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        current_interface['ipv4_addresses'].append(ip_match.group(1))
                        # 如果状态未知但有IP地址，设为已连接
                        if current_interface['status'] == '未知':
                            current_interface['status'] = '已连接'

                # IPv6地址
                elif ('IPv6 地址' in line or 'IPv6 Address' in line or 'Link-local IPv6 Address' in line):
                    # 提取IPv6地址（改进解析）
                    ipv6_match = re.search(r'([0-9a-fA-F:]+%?\d*)\s*\(', line)
                    if not ipv6_match:
                        ipv6_match = re.search(r'([0-9a-fA-F:]+)', line)
                    if ipv6_match:
                        ipv6_addr = ipv6_match.group(1)
                        # 排除本地链路地址（除非是唯一地址）
                        if not ipv6_addr.startswith('fe80::') or len(current_interface['ipv6_addresses']) == 0:
                            current_interface['ipv6_addresses'].append(ipv6_addr)
                            # 如果状态未知但有IP地址，设为已连接
                            if current_interface['status'] == '未知':
                                current_interface['status'] = '已连接'

                # 默认网关
                elif '默认网关' in line or 'Default Gateway' in line:
                    gateway = line.split(':', 1)[1].strip() if ':' in line else ''
                    if gateway:
                        current_interface['default_gateway'] = gateway

                # DNS服务器
                elif 'DNS 服务器' in line or 'DNS Servers' in line:
                    dns = line.split(':', 1)[1].strip() if ':' in line else ''
                    if dns:
                        current_interface['dns_servers'].append(dns)

                # DHCP
                elif 'DHCP 已启用' in line or 'DHCP Enabled' in line:
                    if '是' in line or 'Yes' in line:
                        current_interface['dhcp_enabled'] = True
                elif 'DHCP 服务器' in line or 'DHCP Server' in line:
                    dhcp_server = line.split(':', 1)[1].strip() if ':' in line else ''
                    current_interface['dhcp_server'] = dhcp_server

        # 添加最后一个接口
        if current_interface:
            # 最终状态判断：如果有IP地址且状态不是明确的断开连接，则设为已连接
            if (current_interface['status'] == '未知' and
                (current_interface['ipv4_addresses'] or current_interface['ipv6_addresses'])):
                current_interface['status'] = '已连接'
            interfaces.append(current_interface)

        return interfaces

    def _get_unix_detailed_interfaces(self):
        """获取Unix/Linux系统的详细网络接口信息"""
        interfaces = []

        try:
            # 获取基本接口信息
            ip_result = subprocess.run(['ip', 'addr', 'show'],
                                     capture_output=True,
                                     text=True,
                                     shell=True,
                                     timeout=10)

            if ip_result.returncode == 0:
                interfaces = self._parse_ip_addr_output(ip_result.stdout)

        except Exception as e:
            self.manager.log(f"获取Unix详细接口信息失败: {e}")

        return interfaces

    def _parse_ip_addr_output(self, output):
        """解析ip addr show输出"""
        interfaces = []
        lines = output.split('\n')
        current_interface = None

        for line in lines:
            line = line.strip()

            if line and ':' in line and not line.startswith(' '):
                # 接口行
                parts = line.split(':', 2)
                if len(parts) >= 2:
                    interface_name = parts[1].strip()

                    current_interface = {
                        'name': interface_name,
                        'description': interface_name,
                        'status': '未知',
                        'mac_address': '',
                        'ipv4_addresses': [],
                        'ipv6_addresses': [],
                        'default_gateway': '',
                        'dns_servers': [],
                        'dhcp_enabled': False,
                        'dhcp_server': ''
                    }

                    # 检查状态
                    if 'UP' in line:
                        current_interface['status'] = '已连接'
                    elif 'DOWN' in line:
                        current_interface['status'] = '断开连接'

                    interfaces.append(current_interface)

            elif current_interface and 'link/ether' in line:
                # MAC地址
                mac_match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', line)
                if mac_match:
                    current_interface['mac_address'] = mac_match.group(1)

            elif current_interface and 'inet ' in line:
                # IPv4地址
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+/\d+)', line)
                if ip_match:
                    current_interface['ipv4_addresses'].append(ip_match.group(1))

            elif current_interface and 'inet6 ' in line:
                # IPv6地址
                ipv6_match = re.search(r'inet6\s+([0-9a-fA-F:]+/\d+)', line)
                if ipv6_match:
                    ipv6_addr = ipv6_match.group(1)
                    if not ipv6_addr.startswith('fe80::'):
                        current_interface['ipv6_addresses'].append(ipv6_addr)

        return interfaces

    def display_interfaces(self, interfaces):
        """显示接口信息"""
        if not interfaces:
            no_data_label = ttk.Label(self.scrollable_frame,
                                    text="未找到网络接口信息",
                                    font=("Arial", 12))
            no_data_label.pack(pady=50)
            return

        for i, interface in enumerate(interfaces):
            # 接口卡片
            interface_frame = ttk.LabelFrame(self.scrollable_frame,
                                           text=interface.get('name', '未知接口'),
                                           padding="15")
            interface_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

            # 状态指示器
            status_color = "green" if interface.get('status') == '已连接' else "red"
            status_text = interface.get('status', '未知')

            status_frame = ttk.Frame(interface_frame)
            status_frame.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(status_frame, text="状态:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
            status_label = ttk.Label(status_frame, text=status_text,
                                    font=("Arial", 10), foreground=status_color)
            status_label.pack(side=tk.LEFT, padx=(5, 0))

            # 网格布局显示信息
            info_frame = ttk.Frame(interface_frame)
            info_frame.pack(fill=tk.X)

            row = 0

            # MAC地址
            if interface.get('mac_address'):
                self._add_info_row(info_frame, "MAC地址:", interface['mac_address'], row)
                row += 1

            # IPv4地址
            if interface.get('ipv4_addresses'):
                self._add_info_row(info_frame, "IPv4地址:", ', '.join(interface['ipv4_addresses']), row)
                row += 1

            # IPv6地址
            if interface.get('ipv6_addresses'):
                self._add_info_row(info_frame, "IPv6地址:", ', '.join(interface['ipv6_addresses']), row)
                row += 1

            # 默认网关
            if interface.get('default_gateway'):
                self._add_info_row(info_frame, "默认网关:", interface['default_gateway'], row)
                row += 1

            # DNS服务器
            if interface.get('dns_servers'):
                self._add_info_row(info_frame, "DNS服务器:", ', '.join(interface['dns_servers']), row)
                row += 1

            # DHCP信息
            if interface.get('dhcp_enabled'):
                dhcp_text = f"已启用 (服务器: {interface.get('dhcp_server', '未知')})"
                self._add_info_row(info_frame, "DHCP:", dhcp_text, row)

    def _add_info_row(self, parent, label_text, value_text, row):
        """添加信息行"""
        label = ttk.Label(parent, text=label_text, font=("Arial", 10, "bold"))
        label.grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2)

        value = ttk.Label(parent, text=value_text, font=("Arial", 10))
        value.grid(row=row, column=1, sticky=tk.W, pady=2)

    def show_error(self, error_message):
        """显示错误信息"""
        error_label = ttk.Label(self.scrollable_frame,
                              text=f"错误: {error_message}",
                              font=("Arial", 12), foreground="red")
        error_label.pack(pady=50)

    def close_dialog(self):
        """关闭对话框"""
        self.dialog.destroy()

if __name__ == "__main__":
    print("启动系统路由配置管理器...")
    print("程序包含详细的错误提示和调试日志")
    print()

    app = RouteManager()
    app.run()