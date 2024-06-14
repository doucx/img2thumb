# Img to Thumb
通过watchdog监控图片，并对大小大于1m的图片提取出jpg格式的缩略图

## 配置
使用yaml作为配置文件,格式：
```yaml
-
    from: path # raw文件储存路径
    to: path # 提取的缩略图储存路径, 可以与from相同
- # 如果有多个文件夹对
    from: path # raw文件储存路径
    to: path # 提取的缩略图储存路径
```

## 运行
设置好`config.yaml`后，运行`main.py`

## TODO
- 增加更多设置
