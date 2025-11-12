# 开发者指南

## 🛠️ 开发环境

### 项目结构
```
routeconf/
├── route_manager.py          # 主程序源代码
├── route_manager.bat         # 启动脚本（开发测试用）
├── build_exe.bat            # 打包脚本
├── DEVELOPER_README.md       # 开发者文档（本文件）
├── README.md                # 用户文档
└── dist/                    # 打包输出目录
    ├── RouteManager.exe      # 可执行文件
    └── README.md             # 用户说明
```

## 📦 打包流程

### 打包选项（按推荐顺序）

#### 🥇 方法一：PowerShell脚本（推荐，最可靠）
```powershell
# 右键 → 使用 PowerShell 运行
右键 build.ps1 → 使用 PowerShell 运行

# 或在PowerShell中运行
.\build.ps1
```
**特点**：完整错误处理、详细输出、测试选项

#### 🥈 方法二：批处理脚本（完整版）
```bash
# 双击运行
双击 build_exe.bat

# 命令行运行
build_exe.bat
```
**特点**：自动关闭运行实例、完整清理、测试启动

#### 🥉 方法三：简单批处理（备选）
```bash
# 双击运行
双击 build_simple.bat

# 最基础的打包，无自动清理
```
**特点**：最简单、无干扰

#### 🔧 方法四：手动打包
```bash
# 完全手动控制
pyinstaller --onefile --windowed --name "RouteManager" route_manager.py
```

### 故障排除：文件占用问题

#### 常见错误
```
PermissionError: [WinError 5] Access is denied: 'dist\RouteManager.exe'
```

#### 解决方案
1. **使用PowerShell脚本**：自动处理文件占用
2. **手动关闭进程**：任务管理器结束RouteManager.exe
3. **重启电脑**：彻底清除文件占用
4. **使用简单脚本**：build_simple.bat（无清理操作）

## 🔄 打包参数说明

```bash
pyinstaller \
  --onefile           # 打包成单个文件
  --windowed          # 无控制台窗口（GUI应用）
  --name "RouteManager" # 可执行文件名称
  --icon=NONE         # 无图标（可替换为.ico文件）
  route_manager.py    # 主程序文件
```

## ⚙️ 自定义打包选项

### 添加自定义图标
```bash
# 准备icon文件
# 将icon.ico文件放在项目根目录
pyinstaller --onefile --windowed --name "RouteManager" --icon="icon.ico" route_manager.py
```

### 添加版本信息
创建 `version_info.txt`：
```
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
    StringTable(
      '040904B0',
      [
      StringStruct('CompanyName', 'Your Company'),
      StringStruct('FileDescription', 'Route Manager'),
      StringStruct('FileVersion', '1.0.0'),
      StringStruct('InternalName', 'RouteManager'),
      StringStruct('LegalCopyright', 'Copyright © 2024'),
      StringStruct('OriginalFilename', 'RouteManager.exe'),
      StringStruct('ProductName', 'Route Manager'),
      StringStruct('ProductVersion', '1.0.0')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', 1033, 1200)])
  ]
)
```

使用版本信息：
```bash
pyinstaller --onefile --windowed --name "RouteManager" --version-file="version_info.txt" route_manager.py
```

## 🧪 测试打包结果

### 测试可执行文件
```bash
# 直接运行
dist\RouteManager.exe

# 或从命令行运行，查看输出
start dist\RouteManager.exe
```

### 测试权限功能
1. 以普通用户身份运行
2. 测试添加路由（应显示UAC提示）
3. 验证管理员权限状态显示

### 测试无窗口启动
1. 双击可执行文件
2. 确认只显示GUI界面
3. 没有控制台窗口出现

## 📋 发布准备

### 创建发布包
```bash
# 创建发布目录
mkdir release

# 复制必要文件
copy dist\RouteManager.exe release\
copy dist\README.md release\

# 可选：添加许可证文件
# copy LICENSE release\

# 检查发布包
dir release
```

### 压缩发布包
```bash
# 创建zip文件
powershell -Command "Compress-Archive -Path release -DestinationPath RouteManager_v1.0.zip"
```

## 🔧 常见问题

### 打包失败
1. **PyInstaller版本**：确保使用最新版本
   ```bash
   pip install --upgrade pyinstaller
   ```

2. **依赖问题**：检查是否所有依赖都被正确识别
   ```bash
   # 查看依赖
   pip list
   ```

### 文件过大
- 使用 `--onefile` 会生成较大文件
- 可考虑 `--onedir` 生成目录结构（启动更快，文件更多）

### Windows Defender误报
- 可以为exe文件添加数字签名
- 用户需要添加信任

## 📊 性能优化

### 启动速度优化
```bash
# 使用--onedir模式（启动更快）
pyinstaller --onedir --windowed --name "RouteManager" route_manager.py
```

### 文件大小优化
- 分析包含的模块
- 移除不必要的依赖
```bash
# 查看包含的模块
pyinstaller --log-level DEBUG route_manager.py
```

---

**持续开发建议：**
1. 每次代码更新后重新打包测试
2. 保留build_exe.bat作为打包工具
3. 版本号管理：在文件名或程序中包含版本信息
4. 自动化：可考虑CI/CD自动打包