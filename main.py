'''
通过watchdog监控raw格式文件，并将其转换为jpg格式的缩略图，放在另一个文件夹里
'''

import os
import signal
from utils import get_processable_img, load_thumb, is_processable_img, is_thumb
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

import queue
import threading

import time

with open("./config.yaml", "r")as f:
    config = yaml.safe_load(f)

def is_big_img(path: Path)-> bool:
    path.stat().st_size
    return path.stat().st_size > 1 * 1024 * 1024

def create_thumb(path: Path, to: Path):
    "在to文件夹里创建raw文件的缩略图"
    to_path = to / (path.name + ".thumb.jpg")
    if to_path.exists() or is_thumb(path):
        return

    if is_processable_img(path) and is_big_img(path):
        img = load_thumb(path)
        img.save(to_path)
        print("Thumb created:", path, to_path)

class ImgCreateHandler(FileSystemEventHandler):
    def __init__(self, from_:Path, to:Path, task_queue:queue.Queue) -> None:
        super().__init__()
        self.from_ = from_
        self.to = to
        self.task_queue = task_queue

    def on_created(self, event):
        path = Path(event.src_path)
        threading.Thread(target=self.wait_and_process, args=(path,)).start()

    def wait_and_process(self, path: Path):
        self.wait_for_complete(path)
        self.task_queue.put({
            "path": path,
            "to": self.to
        })

    def wait_for_complete(self, path: Path):
        "等待文件传输完成"
        previous_size = -1
        while True:
            current_size = path.stat().st_size
            if current_size == previous_size:
                break
            previous_size = current_size
            time.sleep(0.5)

def init_img_proc(from_: Path, to: Path, task_queue: queue.Queue):
    "处理现有的图片"
    imgs_from = set(get_processable_img(from_))
    for path in imgs_from:
        task_queue.put({
            "path": path,
            "to": to
            })

def init_observer(from_: Path, to: Path, task_queue:queue.Queue):
    observer = Observer()
    observer.schedule(ImgCreateHandler(from_, to, task_queue), path=str(from_))
    observer.start()
    return observer

def worker(task_queue: queue.Queue, stop_flag: threading.Event):
    while not stop_flag.is_set():
        try:
            task = task_queue.get(timeout=1)  # 添加超时以避免长时间阻塞
        except queue.Empty:
            continue

        if task == None:
            task_queue.task_done()
            break

        try:
            create_thumb(task["path"], task["to"])
            task_queue.task_done()
        except Exception as e:
            # 这里可以记录日志或采取其他适当的错误处理措施
            print(f"Error processing task {task}: {e}")

def main():
    task_queue = queue.Queue()
    stop_flag = threading.Event()

    t = threading.Thread(target=worker, args=(task_queue, stop_flag), daemon=True)
    t.start()

    observers = []
    for c in config:
        from_, to = map(Path, [c["from"], c["to"]])
        init_img_proc(from_, to, task_queue)
        observers.append(init_observer(from_, to, task_queue))

    def signal_handler(signal, frame):
        print('\nStopping...')
        for o in observers:
            o.stop()
        print("observers stopped")
        for o in observers:
            o.join()
        print("observers joined")
        task_queue.put(None)
        stop_flag.set()
        t.join()
        print("worker joined")
        exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    main()
