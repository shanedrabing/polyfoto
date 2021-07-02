# Polyfoto

Create image mosaics.

## Showcase

*"Before and After Science" by Brian Eno*|*"Scott 3" by Scott Walker*
-|-
<img src="docs/bna_science_mosaic.jpg" width="100%" height="auto">|<img src="docs/scott3_mosaic.jpg" width="100%" height="auto">

## Installation

Clone this repository to your local machine with git, then install with
Python.

```bash
git clone https://github.com/shanedrabing/polyfoto.git
cd polyfoto
python setup.py install
```

## Getting Started

Run the program with Python.

```bash
python polyfoto.py -f input.png -d sources -o output.png -n 16
```

### Required arguments

- `-f` : Input file name. This is the target to recreate.
- `-d` : Input folder name. Contains images used to recreate the target.
- `-o` : Output file name. Name of the rendered canvas.
- `-n` : Number of rows. How many rows of images should be used in recreation?

### Optional arguments

- `-p` : Proportional center of construction. 0 being the top of the canvas, 1
  being the bottom.
- `-c` : Proportional chance to consume image. 1 meaning each image will be consumed on upon use, 0 meaning the image will never be consumed
  being the bottom.
- `-s` : Rescaling factor. Normally 4x target size.
- `-t` : Pixel height of thumbnails. Used for the math operations, 16px height
  by default.
- `-x` : Output folder name for thumbnails. "tmp" by default.

## License

[MIT](https://choosealicense.com/licenses/mit/)
