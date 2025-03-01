#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Twitter视频下载工具

这个脚本可以下载Twitter/X上的视频，支持通过URL或推文ID下载。
"""

import os
import re
import sys
import json
import time
import argparse
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor

# 常量定义
DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

# 确保下载目录存在
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)


class TwitterVideoDownloader:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.ydl_opts = {
            'format': 'best',
            'quiet': not verbose,
            'no_warnings': not verbose,
            'extract_flat': False
        }
    
    def log(self, message):
        """打印日志信息（如果启用了详细模式）"""
        if self.verbose:
            print(f"[INFO] {message}")
    
    def extract_tweet_id(self, url):
        """从Twitter URL中提取推文ID"""
        if not url:
            return None
            
        # 检查是否已经是推文ID
        if re.match(r'^\d+$', url):
            return url
            
        # 从URL中提取推文ID
        patterns = [
            r'twitter\.com/\w+/status/(\d+)',
            r'x\.com/\w+/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        return None
    
    def process_url(self, url):
        """处理Twitter URL并下载视频"""
        tweet_id = self.extract_tweet_id(url)
        if not tweet_id:
            print(f"无法从 '{url}' 提取推文ID")
            return False
            
        self.log(f"处理推文ID: {tweet_id}")
        
        # 构建完整的Twitter URL
        if re.match(r'^\d+$', url):
            url = f"https://twitter.com/i/status/{url}"
        
        try:
            # 设置下载选项
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['outtmpl'] = os.path.join(DOWNLOADS_DIR, f'%(uploader)s_%(id)s.%(ext)s')
            
            # 使用yt-dlp下载视频
            with YoutubeDL(ydl_opts) as ydl:
                self.log(f"开始下载视频: {url}")
                ydl.download([url])
                return True
        except Exception as e:
            print(f"下载视频失败: {str(e)}")
            return False


def main():
    global DOWNLOADS_DIR
    
    parser = argparse.ArgumentParser(description='Twitter视频下载工具')
    parser.add_argument('urls', nargs='*', help='Twitter视频URL或推文ID列表')
    parser.add_argument('-f', '--file', help='包含Twitter URL的文本文件，每行一个URL')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志信息')
    parser.add_argument('-o', '--output-dir', help=f'视频保存目录 (默认: {DOWNLOADS_DIR})')
    
    args = parser.parse_args()
    
    # 设置输出目录
    if args.output_dir:
        DOWNLOADS_DIR = args.output_dir
        if not os.path.exists(DOWNLOADS_DIR):
            os.makedirs(DOWNLOADS_DIR)
    
    # 收集所有URL
    urls = args.urls[:]
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                urls.extend(file_urls)
        except Exception as e:
            print(f"读取URL文件失败: {str(e)}")
    
    if not urls:
        parser.print_help()
        return
    
    downloader = TwitterVideoDownloader(verbose=args.verbose)
    
    # 使用线程池并行下载多个视频
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(downloader.process_url, urls))
    
    success_count = sum(1 for r in results if r)
    print(f"\n总计: {len(urls)} 个URL, 成功下载: {success_count}, 失败: {len(urls) - success_count}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序出现错误: {str(e)}")