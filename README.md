# wordpaper

**wordpaper** is a command line tool to generate images which help you remembering words.

Generated images are good for your desktop wallpaper.

## Installation

**wordpaper** is a nix native application.

Install nix package manger and run the following command:

```console
$ nix-env -i -f https://github.com/kayhide/wordpaper/archive/main.tar.gz
```

After successful installation the **wordpaper** command is available.

```console
$ wordpaper --version
0.1.0
```

## Preparation

**wordpaper** collects images from [Unsplash](https://unsplash.com/).

To access Unsplash, you need an access key to its api.

Open an account (it is free), create an app and get an access key.

Once you have successfully opened your account, your apps and their access keys are accessible from:

https://unsplash.com/oauth/applications

## Usage

Set the following environment variables:

- UNSPLASH_ACCESS_KEY
- GEOMETRY (optional, default: `2560x1440`)
- OUTPUT_DIR (optional, default: `output`)
- FONT (optional, default: Noto-Serif-Italic)

Then feed words to **wordpaper**.

Here is an example.

`japanese.csv`
```csv
mountain,山
river,川
world,世界
sun,太陽
to see,見る
to say,言う
```

```console
$ cat japanese.csv | FONT=Noto-Sans-CJK-JP-Bold wordpaper
```

And then, you will have images under `output` directory.

Note that the font should include required glyphs.
Since the example is Japanese, `FONT` is explicitly given.

You can check available fonts on your system with:

```console
$ wordpaper list-font
```

