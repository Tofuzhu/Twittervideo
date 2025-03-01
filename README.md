# Twitter视频下载工具

这是一个简单易用的Twitter/X视频下载工具，可以通过命令行快速下载Twitter上的视频内容。

## 功能特点

- 支持通过URL或推文ID下载视频
- 自动选择最高质量的视频版本
- 支持批量下载多个视频
- 支持从文本文件批量导入URL
- 显示下载进度条
- 多线程并行下载，提高效率

## 使用方法

### 基本用法

```bash
# 下载单个视频
python twitter_video_downloader.py https://twitter.com/username/status/1234567890

# 下载多个视频
python twitter_video_downloader.py https://twitter.com/username/status/1234567890 https://twitter.com/username/status/0987654321

# 使用推文ID下载
python twitter_video_downloader.py 1234567890
```

### 高级选项

```bash
# 从文件批量下载
python twitter_video_downloader.py -f urls.txt

# 指定下载目录
python twitter_video_downloader.py -o D:\Videos https://twitter.com/username/status/1234567890

# 显示详细日志
python twitter_video_downloader.py -v https://twitter.com/username/status/1234567890
```

## 参数说明

- `urls`: Twitter视频URL或推文ID列表
- `-f, --file`: 包含Twitter URL的文本文件，每行一个URL
- `-v, --verbose`: 显示详细日志信息
- `-o, --output-dir`: 视频保存目录 (默认: ./downloads)

## 注意事项

- 该工具仅用于个人学习和研究目的
- 请尊重内容创作者的版权，不要分发下载的视频
- Twitter API可能会有变化，如果工具无法正常工作，请检查更新

## 依赖库

- requests
- argparse

安装依赖：

```bash
pip install requests
```

## 许可证

MIT License