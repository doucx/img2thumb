# RAW to Thumb
通过watchdog监控nef格式文件，并提取缩略图，将其转换为jpg格式，放在另一个文件夹里

## 配置
使用yaml作为配置文件,格式：
```yaml
-
    from: path # raw文件储存路径
    to: path # 提取的缩略图储存路径
- # 如果有多个文件夹对
    from: path # raw文件储存路径
    to: path # 提取的缩略图储存路径
```

## 运行
设置好`config.yaml`后，运行`main.py`

## TODO
增加对更多种类raw文件的支持
