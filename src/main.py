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

def fetch_list(word): 
    dst = list_file(word)
    query = re.sub(r'\bto\s+', '', word)
    if os.path.exists(dst):
        if args.verbose:
            shell.say_status("exist", dst)
        return

    headers = {
        'Authorization': f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    params = {
        ('orientation', 'landscape'),
        ('query', query)
    }
    url = f"https://api.unsplash.com/search/photos"
    res = requests.get(url, headers=headers, params=params)

    os.makedirs(lists_dir, exist_ok=True)
    with open(dst, 'w') as f:
        f.write(res.text)
    shell.say_status("download", dst)

def get_ids(word):
    with open(list_file(word)) as f:
        return [r['id'] for r in json.load(f)['results']]

def get_image(id):
    dst = image_file(id)
    if os.path.exists(dst):
        if args.verbose:
            shell.say_status("exist", dst)
        return

    url = f"https://unsplash.com/photos/{id}/download"
    res = requests.get(url)

    os.makedirs(images_dir, exist_ok=True)
    with open(dst, 'wb') as f:
        f.write(res.content)
    shell.say_status("download", dst)

def add_text(id, eng, frn):
    img = image_file(id)
    dst = f"{output_dir}/{id}-{to_basename(eng)}.jpeg"
    padding = 100

    if os.path.exists(dst):
        shell.say_status("exist", dst)
        return

    os.makedirs(output_dir, exist_ok=True)

    bmp = imagemagick.convert(
        img, "bmp:-",
        gravity="center",
        resize=f"{geometry}^",
        extent=geometry
        )

    if args.analysis_dir:
        os.makedirs(args.analysis_dir, exist_ok=True)
        def on_success(text, placer):
            dst = f"{args.analysis_dir}/{id}-{to_basename(text)}.png"
            placer.analyze(dst)
            shell.say_status("analyze", dst)
    else:
        on_success = None

    to_view = lambda size: ((padding, 0), (size[0] + padding, output_size[1] * 3 // 4))
    bmp = annotate(bmp, frn, 96, padding, to_view=to_view, on_success=on_success)

    to_view = lambda size: ((output_size[0] - size[0] - padding * 2, 0), (size[0] + padding, output_size[1] * 3 // 4))
    bmp = annotate(bmp, eng, 72, padding, to_view=to_view, on_success=on_success)

    res = imagemagick.convert(("bmp:-", bmp), "jpeg:-")
    with open(dst, "wb") as f:
        f.write(res)

    shell.say_status("create", dst)

def annotate(bmp, text, pointsize, padding, to_view=None, on_success=None):
    res = imagemagick.convert(f"label:{text}", "info:", font=font, pointsize=pointsize, format="%wx%h")
    text_size = tuple(map(int, re.match(r"(\d+)x(\d+)", res.decode()).groups()))

    placer = Placer(io.BytesIO(bmp), text_size)
    if to_view:
        placer.view = to_view(text_size)
    placer.padding = padding
    placer.run()
    if on_success:
        on_success(text, placer)

    color = 0.5 < placer.mean and "rgba(0, 0, 0, 0.75)" or "rgba(255, 255, 255, 0.75)"
    return imagemagick.convert(
        ("bmp:-", bmp), "bmp:-",
        fill=color,
        font=font,
        pointsize=pointsize,
        gravity="northwest",
        annotate=(f"+{placer.pos.x}+{placer.pos.y}", text),
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
