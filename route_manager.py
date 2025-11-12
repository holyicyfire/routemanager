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
        self.root.geometry("1000x700")

        # 检测操作系统
        self.is_windows = platform.system().lower() == 'windows'
        logger.info(f"操作系统: {platform.system()}")

        # 检测管理员权限
        self.is_admin = is_admin() if self.is_windows else True
        logger.info(f"管理员权限: {self.is_admin}")

        # 如果没有管理员权限，提示用户
        if self.is_windows and not self.is_admin:
            self.show_admin_prompt()
            return

        self.setup_ui()
        self.refresh_routes()

    def show_admin_prompt(self):
        """显示管理员权限提示"""
        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("权限提示")
        prompt_window.geometry("500x300")
        prompt_window.transient(self.root)
        prompt_window.grab_set()

        # 居中显示
        prompt_window.update_idletasks()
        x = (prompt_window.winfo_screenwidth() // 2) - (prompt_window.winfo_width() // 2)
        y = (prompt_window.winfo_screenheight() // 2) - (prompt_window.winfo_height() // 2)
        prompt_window.geometry(f"+{x}+{y}")

        # 创建提示内容
        main_frame = ttk.Frame(prompt_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 警告图标和标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        # 大号警告文字
        warning_label = ttk.Label(title_frame, text="⚠️ 需要管理员权限",
                                font=("Arial", 14, "bold"))
        warning_label.pack()

        # 说明文字
        info_text = """修改系统路由表需要管理员权限。

您可以选择以下方式继续：

1. 🔙 手动以管理员身份运行：
   • 右键点击命令提示符
   • 选择"以管理员身份运行"
   • 执行此程序

2. 🚀 一键自动重启：
   • 点击下方按钮
   • 程序将自动以管理员身份重启"""

        info_label = ttk.Label(main_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # 重启为管理员按钮
        restart_btn = ttk.Button(button_frame, text="🚀 以管理员身份重启",
                               command=self.restart_with_admin,
                               style="Accent.TButton")
        restart_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 退出按钮
        exit_btn = ttk.Button(button_frame, text="❌ 退出",
                            command=prompt_window.destroy)
        exit_btn.pack(side=tk.LEFT)

        # 隐藏主窗口
        self.root.withdraw()

        # 当提示窗口关闭时，关闭主程序
        prompt_window.protocol("WM_DELETE_WINDOW", lambda: self.quit_program())

    def restart_with_admin(self):
        """以管理员身份重启程序"""
        if restart_as_admin():
            self.quit_program()
        else:
            messagebox.showerror("错误", "无法以管理员身份重启程序")

    def quit_program(self):
        """退出程序"""
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(button_frame, text="刷新", command=self.refresh_routes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="添加路由", command=self.add_route).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="删除路由", command=self.delete_route).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="测试命令", command=self.test_route_command).pack(side=tk.LEFT, padx=(0, 5))

        # IPv版本选择
        version_frame = ttk.Frame(main_frame)
        version_frame.grid(row=0, column=0, sticky=(tk.E, tk.N), pady=(0, 10))

        self.version_var = tk.StringVar(value="IPv4")
        ttk.Radiobutton(version_frame, text="IPv4", variable=self.version_var, value="IPv4", command=self.refresh_routes).pack(side=tk.LEFT)
        ttk.Radiobutton(version_frame, text="IPv6", variable=self.version_var, value="IPv6", command=self.refresh_routes).pack(side=tk.LEFT)

        # 创建路由显示区域 - 使用上下两个独立区域
        routes_container = ttk.Frame(main_frame)
        routes_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        routes_container.columnconfigure(0, weight=1)
        routes_container.rowconfigure(0, weight=1)
        routes_container.rowconfigure(1, weight=1)

        # 活动路由区域
        active_label_frame = ttk.LabelFrame(routes_container, text="📡 活动路由 (系统重启后丢失)", padding="5")
        active_label_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))

        # 持久路由区域
        persistent_label_frame = ttk.LabelFrame(routes_container, text="💾 持久路由 (系统重启后保留)", padding="5")
        persistent_label_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))

        # 活动路由表格
        active_columns = ("目标网络", "子网掩码/前缀长度", "网关", "接口", "跃点数")
        self.active_tree = ttk.Treeview(active_label_frame, columns=active_columns, show='headings', height=8)

        # 设置活动路由列标题
        for col in active_columns:
            self.active_tree.heading(col, text=col)
            if col == "目标网络" or col == "网关":
                self.active_tree.column(col, width=180)
            else:
                self.active_tree.column(col, width=120)

        # 活动路由滚动条
        active_scrollbar = ttk.Scrollbar(active_label_frame, orient=tk.VERTICAL, command=self.active_tree.yview)
        self.active_tree.configure(yscrollcommand=active_scrollbar.set)

        self.active_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        active_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        active_label_frame.columnconfigure(0, weight=1)
        active_label_frame.rowconfigure(0, weight=1)

        # 持久路由表格
        self.persistent_columns_ipv4 = ("目标网络", "子网掩码", "网关地址", "跃点数")
        self.persistent_columns_ipv6 = ("目标网络", "前缀长度", "网关地址", "跃点数")
        self.persistent_tree = ttk.Treeview(persistent_label_frame, columns=self.persistent_columns_ipv4, show='headings', height=6)

        # 设置持久路由列标题
        self._update_persistent_columns_headers("IPv4")

        # 持久路由滚动条
        persistent_scrollbar = ttk.Scrollbar(persistent_label_frame, orient=tk.VERTICAL, command=self.persistent_tree.yview)
        self.persistent_tree.configure(yscrollcommand=persistent_scrollbar.set)

        self.persistent_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        persistent_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        persistent_label_frame.columnconfigure(0, weight=1)
        persistent_label_frame.rowconfigure(0, weight=1)

        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="调试日志", padding="5")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

    def _update_persistent_columns_headers(self, version):
        """更新持久路由表格的列标题"""
        if version == "IPv4":
            columns = self.persistent_columns_ipv4
        else:
            columns = self.persistent_columns_ipv6

        # 重新配置表格列
        self.persistent_tree['columns'] = columns

        # 设置列标题
        for col in columns:
            self.persistent_tree.heading(col, text=col)
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

                if in_persistent_routes:
                    # 持久路由的格式可能不同
                    if len(parts) >= 4:
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
                    if len(parts) >= 5:
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

    def refresh_routes(self):
        """刷新路由表显示"""
        self.status_var.set("正在获取路由信息...")
        self.root.update()

        # 清除现有条目
        for item in self.active_tree.get_children():
            self.active_tree.delete(item)
        for item in self.persistent_tree.get_children():
            self.persistent_tree.delete(item)

        # 更新持久路由列标题
        version = self.version_var.get()
        self._update_persistent_columns_headers(version)

        # 获取路由数据
        routes = self.get_routes()

        # 分离活动路由和持久路由
        active_routes = []
        persistent_routes = []

        for route in routes:
            if route.get('persistent', False):
                persistent_routes.append(route)
            else:
                active_routes.append(route)

        # 填充活动路由表格
        for route in active_routes:
            version = self.version_var.get()
            if version == "IPv6":
                # IPv6路由格式
                self.active_tree.insert('', tk.END, values=(
                    route['destination'],
                    route['netmask'],  # IPv6中这是前缀长度
                    route['gateway'],
                    route['interface'],
                    route['metric']
                ))
            else:
                # IPv4路由格式
                self.active_tree.insert('', tk.END, values=(
                    route['destination'],
                    route['netmask'],
                    route['gateway'],
                    route['interface'],
                    route['metric']
                ))

        # 填充持久路由表格
        for route in persistent_routes:
            version = self.version_var.get()
            if version == "IPv6":
                # IPv6持久路由格式
                self.persistent_tree.insert('', tk.END, values=(
                    route['destination'],
                    route['netmask'],  # IPv6中这是前缀长度
                    route['gateway'],
                    route['metric']
                ))
            else:
                # IPv4持久路由格式
                self.persistent_tree.insert('', tk.END, values=(
                    route['destination'],
                    route['netmask'],
                    route['gateway'],
                    route['metric']
                ))

        # 更新状态信息
        total_routes = len(active_routes) + len(persistent_routes)

        # 创建状态信息，包含详细的统计和权限状态
        status_parts = []
        status_parts.append(f"📡 活动路由: {len(active_routes)} 条")
        if len(persistent_routes) > 0:
            status_parts.append(f"💾 持久路由: {len(persistent_routes)} 条")
        status_parts.append(f"📊 总计: {total_routes} 条")

        # 添加权限状态
        if self.is_windows:
            if hasattr(self, 'is_admin') and self.is_admin:
                status_parts.append("🔑 管理员权限: ✅")
            else:
                status_parts.append("🔑 管理员权限: ❌")

        status_msg = " | ".join(status_parts)
        self.status_var.set(status_msg)

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

    def get_network_interfaces(self):
        """获取系统网络接口列表"""
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

            self.log(f"获取到 {len(interfaces)} 个网络接口")

        except Exception as e:
            self.log(f"获取网络接口失败: {e}")

        return interfaces

    def _get_windows_interfaces(self):
        """获取Windows系统的网络接口信息（带编码处理）"""
        interfaces = []

        try:
            # 使用route print获取接口编号和基本信息
            route_result = subprocess.run(['route', 'print'],
                                       capture_output=True,
                                       text=True,
                                       shell=True,
                                       timeout=10,
                                       encoding='utf-8',
                                       errors='ignore')  # 忽略编码错误

            if route_result.returncode == 0:
                lines = route_result.stdout.split('\n')
                in_interface_list = False

                for line in lines:
                    line = line.strip()
                    if 'Interface List' in line:
                        in_interface_list = True
                        continue
                    elif in_interface_list and ('================================================================' in line or 'IPv4 Route Table' in line or 'IPv6 Route Table' in line):
                        break

                    if in_interface_list and line and ('....' in line or '...' in line):
                        # 解析接口信息
                        if '....' in line:
                            parts = line.split('....')
                        else:
                            parts = line.split('...')

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

                            # 移除可能的MAC地址部分
                            mac_pattern = r'([0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2}[-\s][0-9A-Fa-f]{2})'
                            interface_name = re.sub(mac_pattern, '', interface_name).strip()

                            # 尝试获取IP地址（简化版本）
                            ips = []
                            try:
                                # 使用netsh获取接口IP信息，也使用编码错误处理
                                netsh_result = subprocess.run(['netsh', 'interface', 'ip', 'show', 'address', interface_num],
                                                           capture_output=True,
                                                           text=True,
                                                           shell=True,
                                                           timeout=10,
                                                           encoding='utf-8',
                                                           errors='ignore')
                                if netsh_result.returncode == 0:
                                    for netsh_line in netsh_result.stdout.split('\n'):
                                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', netsh_line)
                                        if ip_match:
                                            ip = ip_match.group(1)
                                            if ip not in ['127.0.0.1', '0.0.0.0']:
                                                ips.append(ip)
                            except:
                                pass

                            # 构建显示名称
                            if interface_name:
                                display_name = interface_name
                            else:
                                display_name = f"接口 {interface_num}"

                            if ips:
                                display_name += f" ({', '.join(ips[:2])})"  # 显示前2个IP

                            interfaces.append({
                                'number': interface_num,
                                'name': interface_name if interface_name else f"接口 {interface_num}",
                                'display': f"{interface_num} - {display_name}",
                                'ips': ips,
                                'mac': None
                            })

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

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 调试信息
        debug_frame = ttk.LabelFrame(self.dialog, text="使用说明", padding="10")
        debug_frame.pack(fill=tk.X, padx=10, pady=10)

        debug_text = tk.Text(debug_frame, height=4, wrap=tk.WORD)
        debug_text.pack(fill=tk.X)

        if version == "IPv4":
            debug_text.insert(tk.END, "IPv4路由添加:\n")
            debug_text.insert(tk.END, "• 目标网络: 如 192.168.100.0\n")
            debug_text.insert(tk.END, "• 子网掩码: 如 255.255.255.0\n")
            debug_text.insert(tk.END, "• 网关: IP地址或 'On-link'\n")
            debug_text.insert(tk.END, "• 接口: 可选，指定路由使用的网络接口\n")
            debug_text.insert(tk.END, "• 持久路由: 可选，勾选后系统重启后路由仍然保留\n")
        else:
            debug_text.insert(tk.END, "IPv6路由添加:\n")
            debug_text.insert(tk.END, "• 目标网络: 如 2001:db8::\n")
            debug_text.insert(tk.END, "• 前缀长度: 如 32, 64, 128\n")
            debug_text.insert(tk.END, "• 网关: IPv6地址或 'On-link'\n")
            debug_text.insert(tk.END, "• 接口: 可选，指定路由使用的网络接口\n")
            debug_text.insert(tk.END, "• 持久路由: 可选，勾选后系统重启后路由仍然保留\n")

        debug_text.config(state=tk.DISABLED)

        # 输入字段
        input_frame = ttk.LabelFrame(self.dialog, text="路由参数", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if version == "IPv4":
            fields = [
                ("目标网络:", "destination", "192.168.100.0"),
                ("子网掩码:", "netmask", "255.255.255.0"),
                ("网关:", "gateway", "On-link"),
                ("接口:", "interface", ""),
                ("跃点数:", "metric", ""),
                ("持久路由:", "persistent", None)  # 特殊处理持久路由选项
            ]
        else:  # IPv6
            fields = [
                ("目标网络:", "destination", "2001:db8::"),
                ("前缀长度:", "prefix_length", "32"),
                ("网关:", "gateway", "fe80::1"),
                ("接口:", "interface", ""),
                ("跃点数:", "metric", ""),
                ("持久路由:", "persistent", None)  # 特殊处理持久路由选项
            ]

        self.entries = {}
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)

            if key == "interface":
                # 接口字段使用下拉框
                interface_frame = ttk.Frame(input_frame)
                interface_frame.grid(row=i, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)

                self.interface_var = tk.StringVar()
                interface_combo = ttk.Combobox(interface_frame, textvariable=self.interface_var, width=30)
                interface_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # 添加"自动选择"选项
                interfaces = [("自动选择", "")]

                # 获取系统接口
                try:
                    system_interfaces = self.manager.get_network_interfaces()
                    for interface in system_interfaces:
                        display_name = interface['display']
                        interface_num = interface['number']
                        interfaces.append((display_name, interface_num))
                except Exception as e:
                    print(f"获取接口失败: {e}")

                # 设置下拉框选项
                interface_combo['values'] = [interface[0] for interface in interfaces]
                interface_combo.set("自动选择")

                # 保存接口映射
                self.interface_mapping = {interface[0]: interface[1] for interface in interfaces}

                self.entries[key] = interface_combo
            elif key == "persistent":
                # 持久路由使用复选框
                persistent_var = tk.BooleanVar()
                persistent_check = ttk.Checkbutton(input_frame, text="添加为持久路由（重启后保留）", variable=persistent_var)
                persistent_check.grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
                self.entries[key] = persistent_var
            else:
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

if __name__ == "__main__":
    print("启动系统路由配置管理器...")
    print("程序包含详细的错误提示和调试日志")
    print()

    app = RouteManager()
    app.run()