from PIL import Image
import numpy as np
import exifread
import rawpy
import io
from pathlib import Path

import mimetypes

from abc import ABC, abstractmethod

class ImageLoader(ABC):
    @abstractmethod
    def load_image(self, file_path: Path) -> Image.Image:
        pass

class JpegImageLoader(ImageLoader):
    def load_image(self, file_path):
        return Image.open(file_path)

class RawImageLoader(ImageLoader):
    def load_image(self, file_path: Path):
        return self.open_nef_thumb(file_path)

    def open_raw_image_thumb(self, img_path:Path)->Image.Image:
        "打开raw图像的缩略图/预览图像"
        with rawpy.imread(str(img_path)) as raw:
            thumb = raw.extract_thumb()
            if thumb.format == rawpy.ThumbFormat.JPEG:
                img = Image.open(io.BytesIO(thumb.data))
            elif thumb.format == rawpy.ThumbFormat.BITMAP:
                img = Image.fromarray(thumb)
        return img #, exif_data

    def open_nef_thumb(self, img_path:Path)-> Image.Image:
        "打开nef缩略图至指定大小"
        img = self.open_raw_image_thumb(img_path)
        with open(img_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        trans = self.get_image_rotate_from_tags(tags)

        if trans is not None:
            img = img.transpose(trans)
        return img

    def get_image_rotate_from_tags(self, tags:dict):
        trans = None
        if "Image Orientation" in tags.keys():
            orientation = tags["Image Orientation"]
            val = orientation.values
            if 2 in val:
                val += [4, 3]
            if 5 in val:
                val += [4, 6]
            if 7 in val:
                val += [4, 8]
            if 3 in val:
                trans=Image.Transpose.ROTATE_180
            if 4 in val:
                trans=Image.Transpose.FLIP_TOP_BOTTOM
            if 6 in val:
                trans=Image.Transpose.ROTATE_270
            if 8 in val:
                trans=Image.Transpose.ROTATE_90
        return trans

class ImageLoaderFactory:
    @staticmethod
    def get_image_loader(file_path):
        ext = Path(file_path).suffix.lower()
        if ext in {'.jpg', '.jpeg'}:
            return JpegImageLoader()
        elif ext in {'.nef', '.cr2', '.arw'}:
            return RawImageLoader()
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

def img_resize_by_max(img:Image.Image, target_max_side = 512):
    "将最长边长度缩放到一个长度, 基于此缩放图像"
    img.thumbnail((target_max_side, target_max_side))

def load_image(file_path) -> Image.Image:
    loader = ImageLoaderFactory.get_image_loader(file_path)
    return loader.load_image(file_path)

def load_thumb(file_path) -> Image.Image:
    img = load_image(file_path)
    img_resize_by_max(img)
    return img

processable_types = {'.nef', '.cr2', '.arw', '.jpg', '.jpeg', '.png', '.webp'}

def is_processable_img(path: Path) -> bool:
    ext = path.suffix.lower()
    return ext in processable_types and path.exists()

def get_processable_img(path: Path) -> list[Path]:
    if not path.is_dir():
        raise ValueError("Not path")

    path_list = []
    for p in path.iterdir():
        if p.is_file() and is_processable_img(p):
            path_list.append(p)
    return path_list

def is_thumb(path: Path) -> bool:
    return str(path).endswith(".thumb.jpg")
