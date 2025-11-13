#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建程序图标的脚本
"""

from PIL import Image, ImageDraw
import os

def create_router_icon():
    """创建路由器图标"""
    # 创建一个32x32像素的图像
    size = 32
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 背景 - 深蓝色圆形
    draw.ellipse([2, 2, size-2, size-2], fill=(0, 120, 215, 255), outline=(0, 90, 180, 255), width=2)

    # 路由器主体 - 中央矩形
    router_width = 16
    router_height = 12
    router_x = (size - router_width) // 2
    router_y = (size - router_height) // 2 - 2
    draw.rectangle([router_x, router_y, router_x + router_width, router_y + router_height],
                   fill=(255, 255, 255, 255), outline=(200, 200, 200, 255))

    # 天线
    # 左天线
    draw.line([router_x + 3, router_y - 2, router_x + 3, router_y - 6], fill=(255, 255, 255, 255), width=2)
    draw.ellipse([router_x + 1, router_y - 8, router_x + 5, router_y - 4], fill=(255, 255, 255, 255))

    # 右天线
    draw.line([router_x + router_width - 3, router_y - 2, router_x + router_width - 3, router_y - 6],
              fill=(255, 255, 255, 255), width=2)
    draw.ellipse([router_x + router_width - 5, router_y - 8, router_x + router_width - 1, router_y - 4],
                 fill=(255, 255, 255, 255))

    # 指示灯
    # 左上角灯（绿色 - 正常）
    draw.ellipse([router_x + 3, router_y + 2, router_x + 5, router_y + 4], fill=(0, 255, 0, 255))

    # 右上角灯（绿色 - 正常）
    draw.ellipse([router_x + router_width - 5, router_y + 2, router_x + router_width - 3, router_y + 4],
                 fill=(0, 255, 0, 255))

    # 左下角灯（黄色 - 活动）
    draw.ellipse([router_x + 3, router_y + router_height - 4, router_x + 5, router_y + router_height - 2],
                 fill=(255, 255, 0, 255))

    # 右下角灯（黄色 - 活动）
    draw.ellipse([router_x + router_width - 5, router_y + router_height - 4, router_x + router_width - 3,
                 router_y + router_height - 2], fill=(255, 255, 0, 255))

    return image

def create_multiple_sizes():
    """创建多种尺寸的图标"""
    sizes = [16, 32, 48, 64, 128, 256]

    for size in sizes:
        # 创建基本图标
        if size == 32:
            image = create_router_icon()
        else:
            # 从32x32缩放其他尺寸
            base_image = create_router_icon()
            image = base_image.resize((size, size), Image.Resampling.LANCZOS)

        # 保存为ICO文件
        if size == 32:
            image.save('route_manager.ico')
            print(f"创建了 {size}x{size} 图标: route_manager.ico")

        # 保存为PNG文件
        image.save(f'icon_{size}x{size}.png')
        print(f"创建了 {size}x{size} PNG图标: icon_{size}x{size}.png")

def create_favicon():
    """创建网站favicon (16x16)"""
    image = create_router_icon()
    favicon = image.resize((16, 16), Image.Resampling.LANCZOS)
    favicon.save('favicon.ico')
    print("创建了 favicon.ico")

if __name__ == "__main__":
    try:
        print("正在创建程序图标...")
        create_multiple_sizes()
        create_favicon()
        print("\n图标创建完成！")
        print("文件列表：")
        print("- route_manager.ico (主程序图标)")
        print("- favicon.ico (网站图标)")
        print("- icon_*.png (各种尺寸的PNG图标)")
    except ImportError:
        print("错误: 需要安装Pillow库")
        print("请运行: pip install Pillow")
    except Exception as e:
        print(f"创建图标时出错: {e}")