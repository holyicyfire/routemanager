# GitHub Release 创建指南

## 手动创建 GitHub Release

由于没有 GitHub CLI 或 API 访问权限，请按照以下步骤手动创建 Release：

### 步骤 1：访问 GitHub Releases 页面
1. 打开浏览器，访问：https://github.com/holyicyfire/routemanager/releases
2. 点击 "Create a new release" 按钮

### 步骤 2：填写 Release 信息
1. **Tag**：选择或输入 `v1.0.0`
2. **Title**：输入 `系统路由配置管理器 v1.0.0`
3. **Description**：复制以下内容：

```
# 系统路由配置管理器 v1.0.0

## 🎉 版本发布

**发布日期**: 2024年11月12日
**版本类型**: 稳定版本 (Stable Release)
**发布状态**: ✅ 已发布

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

## 🔧 技术特点
- **独立运行**：无需安装Python环境
- **无窗口模式**：纯图形界面，无控制台窗口
- **自动权限**：智能管理员权限检测和提升
- **单文件部署**：11MB单一可执行文件

## 📋 下载和使用

### 下载文件
- **RouteManager.exe** - 主程序文件 (11.2MB)

### 系统要求
- **操作系统**: Windows 7 / 8 / 10 / 11
- **权限**: 需要管理员权限（用于修改系统路由表）
- **依赖**: 无（完全独立运行）

### 使用方法
1. **下载**：下载 `RouteManager.exe` 程序文件
2. **放置**：将文件放在任意文件夹中
3. **运行**：双击 `RouteManager.exe` 启动程序
4. **权限**：在UAC提示中点击"是"授权管理员权限

## 🐛 已知问题

### 权限相关
- **现象**：添加/删除路由时提示权限不足
- **解决**：以管理员身份运行或自动UAC授权

## 🔗 相关链接

### 项目地址
- **源代码**: https://github.com/holyicyfire/routemanager
- **问题报告**: https://github.com/holyicyfire/routemanager/issues

---

**感谢您使用系统路由配置管理器！** 🎉
```

### 步骤 3：上传可执行文件
1. 在 Release 页面中找到 **Assets** 区域
2. 点击 **Attach files by dragging & dropping here or selecting them**
3. 选择以下文件进行上传：
   - `D:\test\routeconf\releases\v1.0.0\RouteManager.exe`

### 步骤 4：发布 Release
1. 确认所有信息填写正确
2. 点击 **Publish release** 按钮
3. 等待文件上传完成

## 验证 Release 创建成功

Release 创建成功后，你应该能够：
1. 在 https://github.com/holyicyfire/routemanager/releases 看到 v1.0.0 Release
2. 下载 `RouteManager.exe` 文件
3. 其他用户可以访问 https://github.com/holyicyfire/routemanager/releases/latest 直接下载最新版本

## 更新 v1.0.0 标签（如果需要）

如果 v1.0.0 标签已经存在，可能需要：
1. 删除本地标签：`git tag -d v1.0.0`
2. 删除远程标签：`git push origin :refs/tags/v1.0.0`
3. 重新创建标签：`git tag v1.0.0`
4. 推送新标签：`git push origin v1.0.0`

---

完成这些步骤后，用户就可以从 GitHub 直接下载可执行文件了！🎉