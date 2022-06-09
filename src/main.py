from functools import partial
import argparse
import binascii
import io
import os
import re
import requests
import sys

from placer import Placer
from shell import Shell
from cache import Cache
import imagemagick

HOME = os.getenv("HOME")
VERSION = os.getenv("VERSION")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

parser = argparse.ArgumentParser(prog="wordpaper")
parser.add_argument('--version', action="version", version=VERSION)
parser.add_argument('--output-dir', metavar="DIR", default="output", help="output directory (default: output)")
parser.add_argument('--cache-dir', metavar="DIR", default=f"{HOME}/.cache/wordpaper", help="cache directory (default: $HOME/.cache/%(prog)s)")
parser.add_argument('--analysis-dir', metavar="DIR", help="if given, outputs analysis for each processed image")
parser.add_argument('--geometry', default="2560x1440", help="geometry of output images (default: 2560x1440)")
parser.add_argument('--font', default="Noto-Serif-Italic", help="text font (default: Noto-Sefrif-Italic)")
parser.add_argument('--foreign-size', metavar="SIZE", default="96", help="font size for foreign word (default: 96)")
parser.add_argument('--english-size', metavar="SIZE", default="72", help="font size for english word (default: 72)")
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


font = args.font
foreign_size = args.foreign_size
english_size = args.english_size
geometry = args.geometry
output_size = tuple(map(int, re.match(r"(\d+)x(\d+)", geometry).groups()))
force = args.force

shell = Shell()

cache = Cache(args.cache_dir)
if args.verbose:
    cache.callbacks.on_exist(partial(Shell.say_status, shell, "exist"))
cache.callbacks.on_create(partial(Shell.say_status, shell, "download"))

output = Cache(args.output_dir)
output.callbacks.on_exist(partial(Shell.say_status, shell, "exist"))
output.callbacks.on_create(partial(Shell.say_status, shell, "create"))

if args.analysis_dir:
    analysis = Cache(args.analysis_dir)
    analysis.callbacks.on_create(partial(Shell.say_status, shell, "analyze"))
else:
    analysis = None



def fetch_list(word):
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
    if res.text == "Rate Limit Exceeded":
        raise Exception("Rate Limit Exceeded")
    return res.text

def get_ids(word):
    content = cache.json("lists", word).put(fetch_list, word).load()
    return [r['id'] for r in content['results']]

def fetch_image(id):
    url = f"https://unsplash.com/photos/{id}/download"
    res = requests.get(url)
    return res.content

def add_text(id, eng, frn):
    padding = 100
    src = cache.jpeg("images", id).put(fetch_image, id).file()
    bmp = imagemagick.convert(
        src, "bmp:-",
        gravity="center",
        resize=f"{geometry}^",
        extent=geometry
        )


    texts = [(frn, foreign_size), (eng, english_size)]
    sizes = [cache.json("sizes", f"{text}-{pointsize}").put(get_text_size, text, pointsize).load(quiet=True) for text, pointsize in texts]
    to_views = [
        lambda size: ((padding, 0), (size[0] + padding, output_size[1] * 3 // 4)),
        lambda size: ((output_size[0] - size[0] - padding * 2, 0), (size[0] + padding, output_size[1] * 3 // 4))
    ]
    placers = [find_place(bmp, size, padding, to_view(size)) for size, to_view in zip(sizes, to_views)]
    if analysis:
        for placer, (text, _) in zip(placers, texts):
            key = f"{os.path.splitext(os.path.basename(src))[0]}--{text}"
            analysis.png(key).put(Placer.analyze, placer).file(force=True)

    to_color = lambda placer: 0.5 < placer.mean and "rgba(0, 0, 0, 0.75)" or "rgba(255, 255, 255, 0.75)"
    annotations = [(text, pointsize, placer.pos, to_color(placer)) for (text, pointsize), placer in zip(texts, placers)]
    bmp = annotate(bmp, annotations)

    return imagemagick.convert(("bmp:-", bmp), "jpeg:-")

def get_text_size(text, pointsize):
    return imagemagick.convert(f"label:{text}", "info:", font=font, pointsize=pointsize, format="[%w,%h]").decode()

def find_place(bmp, text_size, padding, view):
    placer = Placer(io.BytesIO(bmp), text_size, padding=padding, view=view)
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
    for id in get_ids(eng):
        hash = binascii.crc32(f"{id}--{eng}--{frn}".encode())
        output.jpeg(f"{hash:08x}-{eng}").put(add_text, id, eng, frn).file(force=force)


while True:
    line = sys.stdin.readline()
    if not line: break
    eng, frn = map(str.strip, line.split(","))
    forge(eng, frn)
