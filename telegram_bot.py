#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Twitter视频下载Telegram机器人

这个脚本创建一个Telegram机器人，用于下载Twitter/X上的视频。
用户只需发送Twitter视频链接，机器人就会下载并发送视频文件。
"""

import os
import logging
import tempfile
import datetime
import time
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 导入Twitter视频下载器
from twitter_video_downloader import TwitterVideoDownloader, DOWNLOADS_DIR

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 请在此处设置您的Telegram机器人令牌
TELEGRAM_BOT_TOKEN = "7535424250:AAEd_6syjxVUuAaEocnvqB-vXP1dVXSNwjM"

# 视频文件保存天数，超过这个天数的视频将被自动清理
VIDEO_RETENTION_DAYS = 7

# 确保下载目录存在
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理/start命令
    """
    await update.message.reply_text(
        "👋 欢迎使用Twitter视频下载机器人！\n\n"
        "只需发送Twitter/X视频链接，我就会下载并发送给你。\n\n"
        "支持的格式:\n"
        "- https://twitter.com/username/status/123456789\n"
        "- https://x.com/username/status/123456789\n"
        "- 直接发送推文ID: 123456789\n\n"
        "使用 /clean 命令可以清理所有已下载的视频文件"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理/help命令
    """
    await update.message.reply_text(
        "📖 使用帮助:\n\n"
        "1. 发送Twitter/X视频链接给我\n"
        "2. 等待我下载视频 (这可能需要几秒钟)\n"
        "3. 我会将视频发送给你\n\n"
        "如果遇到问题，请确保:\n"
        "- 链接格式正确\n"
        "- 推文确实包含视频\n"
        "- 视频未被删除或设为私有\n\n"
        "其他命令:\n"
        "- /clean - 清理所有已下载的视频文件\n"
        f"注意: 视频文件会在{VIDEO_RETENTION_DAYS}天后自动清理"
    )


async def clean_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理/clean命令，清理所有已下载的视频文件
    """
    message = await update.message.reply_text("🧹 正在清理视频文件...")
    
    try:
        # 获取下载目录中的所有文件
        files = os.listdir(DOWNLOADS_DIR)
        video_files = [f for f in files if f.endswith(('.mp4', '.webm', '.mkv'))]
        
        # 删除所有视频文件
        count = 0
        for file in video_files:
            file_path = os.path.join(DOWNLOADS_DIR, file)
            try:
                os.remove(file_path)
                count += 1
            except Exception as e:
                logger.error(f"删除文件失败 {file}: {str(e)}")
        
        await message.edit_text(f"✅ 清理完成！已删除 {count} 个视频文件。")
    except Exception as e:
        logger.error(f"清理视频文件时出错: {str(e)}")
        await message.edit_text(f"❌ 清理视频文件时出错: {str(e)}")


def auto_clean_videos():
    """
    自动清理超过保存期限的视频文件
    """
    while True:
        try:
            logger.info("开始自动清理过期视频文件...")
            now = datetime.datetime.now()
            count = 0
            
            # 获取下载目录中的所有文件
            for file in os.listdir(DOWNLOADS_DIR):
                if file.endswith(('.mp4', '.webm', '.mkv')):
                    file_path = os.path.join(DOWNLOADS_DIR, file)
                    
                    # 获取文件的修改时间
                    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    file_age = (now - file_time).days
                    
                    # 如果文件超过保存期限，则删除
                    if file_age >= VIDEO_RETENTION_DAYS:
                        try:
                            os.remove(file_path)
                            count += 1
                            logger.info(f"已删除过期视频文件: {file}")
                        except Exception as e:
                            logger.error(f"删除过期文件失败 {file}: {str(e)}")
            
            logger.info(f"自动清理完成，已删除 {count} 个过期视频文件")
            
            # 每24小时执行一次清理
            time.sleep(86400)  # 24小时 = 86400秒
        except Exception as e:
            logger.error(f"自动清理过程中出错: {str(e)}")
            time.sleep(3600)  # 出错后等待1小时再试


async def download_twitter_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理用户发送的Twitter链接
    """
    import re
    import tempfile
    url = update.message.text.strip()
    
    # 发送处理中的消息
    processing_message = await update.message.reply_text("🔄 正在处理您的请求，请稍候...")
    
    # 创建下载器实例
    downloader = TwitterVideoDownloader(verbose=True)
    
    # 提取推文ID
    tweet_id = downloader.extract_tweet_id(url)
    if not tweet_id:
        await processing_message.edit_text(f"❌ 无法从链接中提取推文ID: {url}")
        return
    
    # 构建完整的Twitter URL
    if re.match(r'^\d+$', url):
        url = f"https://twitter.com/i/status/{tweet_id}"
    
    # 设置下载选项和文件名
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, f"twitter_{tweet_id}.mp4")
    
    # 下载视频
    await processing_message.edit_text("⬇️ 正在下载视频...")
    
    try:
        # 使用yt-dlp下载视频
        ydl_opts = {
            'format': 'best',
            'quiet': False,
            'no_warnings': False,
            'outtmpl': temp_file
        }
        
        from yt_dlp import YoutubeDL
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            username = info.get('uploader', 'unknown').replace('@', '')
            filename = f"{username}_{tweet_id}.mp4"
            output_path = os.path.join(DOWNLOADS_DIR, filename)
            
            # 如果下载的文件不是mp4格式，复制到正确的输出路径
            if os.path.exists(temp_file):
                import shutil
                shutil.copy2(temp_file, output_path)
            else:
                # 查找下载的文件
                for file in os.listdir(temp_dir):
                    if file.startswith(f"twitter_{tweet_id}"):
                        shutil.copy2(os.path.join(temp_dir, file), output_path)
                        break
        
        success = os.path.exists(output_path)
    except Exception as e:
        logger.error(f"下载视频失败: {str(e)}")
        await processing_message.edit_text(f"❌ 下载视频失败: {str(e)}")
        return
    
    if not success:
        await processing_message.edit_text("❌ 下载视频失败，请稍后重试")
        return
    
    # 发送视频文件
    await processing_message.edit_text("📤 正在发送视频...")
    try:
        with open(output_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                filename=filename,
                caption=f"来自 @{username} 的视频"
            )
        await processing_message.edit_text("✅ 视频已发送！")
    except Exception as e:
        logger.error(f"发送视频时出错: {str(e)}")
        # 如果视频太大，尝试作为文档发送
        try:
            with open(output_path, 'rb') as video_file:
                await update.message.reply_document(
                    document=video_file,
                    filename=filename,
                    caption=f"来自 @{username} 的视频 (由于大小限制，作为文件发送)"
                )
            await processing_message.edit_text("✅ 视频已作为文件发送！")
        except Exception as e2:
            logger.error(f"作为文档发送视频时出错: {str(e2)}")
            await processing_message.edit_text("❌ 发送视频失败，可能是文件太大。视频已保存到服务器。")
    
    # 清理临时目录
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass


def main() -> None:
    """
    启动机器人
    """
    # 创建应用实例
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 添加处理程序
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clean", clean_videos))
    
    # 处理Twitter链接
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        download_twitter_video
    ))

    # 启动自动清理线程
    auto_clean_thread = threading.Thread(target=auto_clean_videos, daemon=True)
    auto_clean_thread.start()
    logger.info(f"已启动自动清理线程，将每24小时清理超过{VIDEO_RETENTION_DAYS}天的视频文件")

    # 启动机器人
    print("启动Telegram机器人...")
    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"机器人运行出错: {str(e)}")