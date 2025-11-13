# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **System Route Configuration Manager** (系统路由配置管理器) - a Python GUI application built with Tkinter that allows users to manage system routing tables on Windows. The application provides a user-friendly interface for adding, deleting, and viewing both IPv4 and IPv6 routes with detailed error handling and debugging capabilities.

## Development Commands

### Running the Application

```bash
# Development run (requires manual admin privileges)
python route_manager.py

# Production run (auto-requests admin privileges, no console window)
route_manager.bat

# Test the application
python route_manager.py
```

### Building for Distribution

```bash
# Primary build method (recommended)
build_exe.bat

# Alternative build methods are documented in DEVELOPER_README.md
```

### Development Workflow

```bash
# Test route functionality
python route_manager.py
# Click "测试命令" (Test Command) button to verify route command functionality

# Build executable after changes
build_exe.bat

# Test the built executable
dist\RouteManager.exe
```

## Architecture Overview

### Core Components

1. **RouteManager Class** (`route_manager.py:59-1190`)
   - Main application class managing the GUI and routing operations
   - Handles both IPv4 and IPv6 route management
   - Implements permission detection and admin elevation
   - Manages network interface detection and caching

2. **EnhancedRouteDialog Class** (`route_manager.py:1275-1506`)
   - Advanced dialog for adding new routes with interface selection
   - Asynchronous interface loading with caching
   - Support for persistent routes and metric configuration

3. **Route Parsing System**
   - `parse_windows_routes()`: Parses Windows IPv4 route table output
   - `parse_windows_routes_ipv6()`: Parses Windows IPv6 route table output
   - Separates active routes from persistent routes in display

### Key Features

- **Dual Protocol Support**: Handles both IPv4 and IPv6 routing
- **Permission Management**: Automatic admin privilege detection and elevation
- **Interface Detection**: Real-time network interface scanning with caching
- **Error Analysis**: Detailed error messages with specific solutions
- **Route Classification**: Separate display for active vs persistent routes
- **Logging**: Real-time debugging log display

## System Dependencies

### Runtime Dependencies
- Python 3.6+
- Tkinter (included with Python)
- Windows OS (primary target), limited Linux/macOS support

### Build Dependencies
- PyInstaller for executable packaging
- Standard library modules only (no external packages required)

### System Permissions
- Administrator/root privileges required for route modifications
- Automatic UAC elevation on Windows

## File Structure

```
routeconf/
├── route_manager.py          # Main application source code
├── route_manager.bat         # Launch script (auto-elevates privileges)
├── build_exe.bat            # Build script for creating executable
├── DEVELOPER_README.md       # Developer documentation
├── README.md                # User documentation (Chinese)
└── GITHUB_RELEASE_GUIDE.md  # GitHub release instructions
```

## Code Patterns and Conventions

### Error Handling
- Comprehensive exception handling with user-friendly messages
- Detailed error analysis in `analyze_route_error()` method
- Logging integration throughout the application

### GUI Architecture
- Tkinter-based with ttk themed widgets
- Responsive layout with proper grid/weight configuration
- Async operations for interface detection to prevent UI blocking

### Route Command Construction
- Platform-specific command building (Windows route command)
- Parameter validation before execution
- Support for both temporary and persistent routes

## Development Notes

### Route Management
- Uses Windows `route` command for IPv4, `route -6` for IPv6
- Supports persistent routes with `-p` flag
- Interface-specific routing with `IF <interface_number>` parameter

### Network Interface Detection
- Parses `route print` output for interface information
- Implements caching to avoid repeated system calls
- Handles both IPv4 and IPv6 interface addressing

### Permission Handling
- Windows-specific admin privilege detection using `ctypes.windll.shell32.IsUserAnAdmin()`
- Automatic UAC elevation via `ShellExecuteW` with "runas" verb
- Graceful fallback when admin privileges unavailable

### Testing Route Functionality
- Built-in test command adds/removes a test route to verify functionality
- Useful for troubleshooting permission and command execution issues

## Important Implementation Details

### Chinese Language Support
- UI text primarily in Chinese for target user base
- Error messages and documentation in Chinese
- Consider internationalization if expanding to other markets

### Security Considerations
- Application modifies system routing tables
- Requires administrator privileges
- Includes input validation for route parameters
- Logs all routing operations for audit trail

### Performance Optimizations
- Network interface information caching (30-second TTL)
- Async operations to prevent UI freezing
- Efficient parsing of system command output