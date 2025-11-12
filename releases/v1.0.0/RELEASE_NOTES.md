# 系统路由配置管理器 v1.0.0 发布说明

## 🎉 版本发布

**发布日期**: 2024年11月12日
**版本类型**: 稳定版本 (Stable Release)
**发布状态**: ✅ 已发布

## 📋 下载和安装

### 下载方式
- **GitHub Releases**: https://github.com/holyicyfire/routemanager/releases
- **直接下载**: [RouteManager.exe](https://github.com/holyicyfire/routemanager/releases/download/v1.0.0/RouteManager.exe)

### 系统要求
- **操作系统**: Windows 7 / 8 / 10 / 11
- **权限**: 需要管理员权限（用于修改系统路由表）
- **依赖**: 无（完全独立运行）

### 安装步骤
1. **下载**：下载 `RouteManager.exe` 程序文件
2. **放置**：将文件放在任意文件夹中
3. **运行**：双击 `RouteManager.exe` 启动程序
4. **权限**：在UAC提示中点击"是"授权管理员权限

## ✨ 主要功能

### 🌐 路由管理
- **添加路由**：支持IPv4和IPv6路由添加
- **删除路由**：安全删除不需要的路由
- **查看路由**：清晰显示所有系统路由
- **持久路由**：支持永久保存的路由

### 🎨 界面特性
- **分离显示**：活动路由和持久路由独立区域
- **实时状态**：显示权限状态和路由统计
- **接口选择**：自动检测系统网络接口
- **协议切换**：支持IPv4/IPv6协议切换
- **图形界面**：直观易用的Tkinter GUI

### 🔧 技术特点
- **独立运行**：无需安装Python环境
- **无窗口模式**：纯图形界面，无控制台窗口
- **自动权限**：智能管理员权限检测和提升
- **单文件部署**：11MB单一可执行文件

## 🆕 更新内容

### v1.0.0 (2024-11-12) - 首次发布
- ✨ 完整的路由管理功能
- ✨ IPv4/IPv6双协议支持
- ✨ 活动路由和持久路由分离显示
- ✨ 网络接口自动检测和选择
- ✨ 管理员权限自动处理
- ✅ 完整的错误处理和用户引导
- ✨ 独立可执行文件打包
- ✅ 详细的使用文档和技术文档

## 📋 文件清单

### 发布包包含
- `RouteManager.exe` - 主程序文件 (11.2MB)
- `README.md` - 用户使用说明
- `CHANGELOG.md` - 更新日志

### 文件信息
- **总大小**: 约 11.3MB
- **主程序**: 11.2MB
- **文档**: 约5KB

## 🛠️ 技术规格

### 开发环境
- **编程语言**: Python 3.13+
- **GUI框架**: Tkinter
- **打包工具**: PyInstaller 6.13.0
- **版本控制**: Git

### 程序信息
- **类型**: Windows可执行文件
- **架构**: 单文件独立运行
- **权限**: Windows管理员权限
- **界面**: 图形用户界面

## 🔍 测试说明

### 测试环境
- ✅ Windows 11 专业版
- ✅ Python 3.13.2 环境
- ✅ 管理员权限测试
- ✅ 路由操作测试

### 兼容性
- ✅ Windows 7/8/10/11
- ✅ 32位/64位系统
- ✅ 标准用户权限/管理员权限

## 🐛 已知问题

### 权限相关
- **现象**：添加/删除路由时提示权限不足
- **解决**：以管理员身份运行或自动UAC授权

### 兼容性
- **现象**：部分Windows系统可能需要.NET Framework
- **说明**：Tkinter是Python标准库，无需额外依赖

## 🔗 相关链接

### 项目地址
- **源代码**: https://github.com/holyicyfire/routemanager
- **问题报告**: https://github.com/holyicyfire/routemanager/issues
- **下载页面**: https://github.com/holyicyfire/routemanager/releases

### 文档
- **用户文档**: [README.md](README.md)
- **开发者文档**: [DEVELOPER_README.md](../DEVELOPER_README.md)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

## 📞 支持与反馈

### 获取帮助
- **文档查阅**：查看本README和CHANGELOG
- **问题报告**：通过GitHub Issues提交问题
- **功能建议**：欢迎提交功能请求

### 贡献指南
- **源代码贡献**：欢迎提交Pull Request
- **测试报告**：欢迎测试反馈问题
- **文档改进**：欢迎完善使用文档

---

**感谢您使用系统路由配置管理器！** 🎉

**v1.0.0 - 稳定可靠的系统路由管理工具**