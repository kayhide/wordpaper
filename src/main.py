from functools import partial
import argparse
import io
import json
import os
import re
import requests
import sys

from placer import Placer
from shell import Shell
import imagemagick

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

parser = argparse.ArgumentParser(prog="wordpaper")
parser.add_argument('--version', action="version", version=os.getenv("VERSION"))
parser.add_argument('--output-dir', metavar="DIR", default="output", help="output directory (default: output)")
parser.add_argument('--cache-dir', metavar="DIR", help="cache directory (default: $HOME/.cache/%(prog)s)")
parser.add_argument('--analysis-dir', metavar="DIR", help="if given, outputs analysis for each processed image")
parser.add_argument('--geometry', default="2560x1440", help="geometry of output images (default: 2560x1440)")
parser.add_argument('--font', default="Noto-Serif-Italic", help="text font (default: Noto-Sefrif-Italic)")
parser.add_argument('--verbose', action="store_true")
parser.add_argument('--force', action="store_true", help="overwrite generated images if existing")
parser.add_argument('--list-font', action="store_true", help="show available fonts and exit")
args = parser.parse_args()

if args.list_font:
    lines = imagemagick.list("font")
    for line in lines.decode().splitlines():
        if "Font:" in line:
            print(line.split(r":", 2)[1].lstrip())
    exit()


home_dir = os.getenv("HOME")
cache_dir = args.cache_dir or f"{home_dir}/.cache/wordpaper"
lists_dir = f"{cache_dir}/lists"
images_dir = f"{cache_dir}/images"
output_dir = args.output_dir
font = args.font
geometry = args.geometry
output_size = tuple(map(int, re.match(r"(\d+)x(\d+)", geometry).groups()))


shell = Shell()

def to_basename(word):
    return word.replace(' ', '_')

def list_file(word):
    return f"{lists_dir}/{to_basename(word)}.json"

def image_file(id):
    return f"{images_dir}/{id}.jpeg"

def caching(path, on_exist=None, on_create=None):
    if os.path.exists(path):
        on_exist and on_exist(path)
        return

    def save(body):
        try:
            body = body.encode()
        except (AttributeError):
            pass

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(body)

    yield save
    on_create and on_create(path)


def fetch_list(word): 
    dst = list_file(word)
    on_exist = args.verbose and partial(Shell.say_status, shell, "exist") or None
    on_create = partial(Shell.say_status, shell, "download")
    for save in caching(dst, on_exist=on_exist, on_create=on_create):
        query = re.sub(r'\bto\s+', '', word)
        headers = {
            'Authorization': f"Client-ID {UNSPLASH_ACCESS_KEY}"
        }
        params = {
            ('orientation', 'landscape'),
            ('query', query)
        }
        url = f"https://api.unsplash.com/search/photos"
        res = requests.get(url, headers=headers, params=params)
        save(res.text)

def get_ids(word):
    with open(list_file(word)) as f:
        return [r['id'] for r in json.load(f)['results']]

def get_image(id):
    dst = image_file(id)
    on_exist = args.verbose and partial(Shell.say_status, shell, "exist") or None
    on_create = partial(Shell.say_status, shell, "download")
    for save in caching(dst, on_exist=on_exist, on_create=on_create):
        url = f"https://unsplash.com/photos/{id}/download"
        res = requests.get(url)
        save(res.content)


def add_text(id, eng, frn):
    dst = f"{output_dir}/{id}-{to_basename(eng)}.jpeg"
    if args.force and os.path.exists(dst):
        os.remove(dst)

    on_exist = partial(Shell.say_status, shell, "exist")
    on_create = partial(Shell.say_status, shell, "create")
    for save in caching(dst, on_exist=on_exist, on_create=on_create):
        padding = 100
        bmp = imagemagick.convert(
            image_file(id), "bmp:-",
            gravity="center",
            resize=f"{geometry}^",
            extent=geometry
            )


        texts = [(frn, 96), (eng, 72)]
        sizes = [get_text_size(text, pointsize) for text, pointsize in texts]
        to_views = [
            lambda size: ((padding, 0), (size[0] + padding, output_size[1] * 3 // 4)),
            lambda size: ((output_size[0] - size[0] - padding * 2, 0), (size[0] + padding, output_size[1] * 3 // 4))
        ]
        placers = [find_place(bmp, size, padding, to_view(size)) for size, to_view in zip(sizes, to_views)]
        if args.analysis_dir:
            os.makedirs(args.analysis_dir, exist_ok=True)
            for placer, (text, _) in zip(placers, texts):
                dst = f"{args.analysis_dir}/{id}-{to_basename(text)}.png"
                placer.analyze(dst)
                shell.say_status("analyze", dst)

        to_color = lambda placer: 0.5 < placer.mean and "rgba(0, 0, 0, 0.75)" or "rgba(255, 255, 255, 0.75)"
        annotations = [(text, pointsize, placer.pos, to_color(placer)) for (text, pointsize), placer in zip(texts, placers)]
        bmp = annotate(bmp, annotations)

        res = imagemagick.convert(("bmp:-", bmp), "jpeg:-")
        save(res)

def get_text_size(text, pointsize):
    res = imagemagick.convert(f"label:{text}", "info:", font=font, pointsize=pointsize, format="%wx%h")
    return tuple(map(int, re.match(r"(\d+)x(\d+)", res.decode()).groups()))

def find_place(bmp, text_size, padding, view):
    placer = Placer(io.BytesIO(bmp), text_size)
    placer.view = view
    placer.padding = padding
    placer.run()
    return placer

def annotate(bmp, annotations):
    return imagemagick.convert(
        ("bmp:-", bmp), "bmp:-",
        "-font", font,
        "-gravity", "northwest",
        *[ [
            "-pointsize", pointsize,
            "-fill", color,
            "-annotate", f"+{pos.x}+{pos.y}", text,
            ] for text, pointsize, pos, color in annotations ],
        alpha="off"
        )

def forge(eng, frn):
    shell.say_status("forge", f"{frn}: {eng}")
    fetch_list(eng)
    for id in get_ids(eng):
        get_image(id)
        add_text(id, eng, frn)


while True:
    line = sys.stdin.readline()
    if not line: break
    eng, frn = map(str.strip, line.split(","))
    forge(eng, frn)
