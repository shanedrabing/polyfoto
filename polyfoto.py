__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.1.1"
__email__ = "shane.drabing@gmail.com"

import os
import sys

import cv2
import imageio
import numpy as np


def srt(prop):
    def srtf(x):
        return abs(x[0] - ROW_NUM * prop)
    return srtf


def prod(itr):
    n = 1
    for x in itr:
        n *= x
    return n


def torgb(im):
    if len(im.shape) == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
    elif im.shape[2] == 4:
        im = cv2.cvtColor(im, cv2.COLOR_RGBA2RGB)
    return im


def resize_landscape(im, h):
    imh, imw, *_ = im.shape
    ratio = h / imh
    w = round(ratio * imw)
    reim = cv2.resize(im, (w, h))
    reim = torgb(reim)
    return reim


def convert_or_load(FOLDER_SRC, THUMBSIZE):
    thumbs = list()
    folder = os.listdir(FOLDER_SRC)
    len_folder = len(folder)
    for i, name in enumerate(folder):
        if (i % 100 == 0):
            print(f"{i} / {len_folder}".ljust(30), end="\r")

        path_src = os.path.realpath(os.path.join(FOLDER_SRC, name))
        path_tmp = os.path.realpath(os.path.join(FOLDER_TMP, name))

        try:
            if os.path.exists(path_tmp):
                im = imageio.imread(path_tmp)
            else:
                im = imageio.imread(path_src)
                im = resize_landscape(im, THUMBSIZE)
                if im.shape[-1] != 3:
                    print(im.shape)
                    sys.exit(0)
                imageio.imwrite(path_tmp, im)

            thumbs.append((name, im.astype(np.int16)))
        except ValueError:
            pass
    return thumbs


def build(FILE_IN, RESCALE, ROW_NUM, ROW_PROP, FOLDER_SRC, THUMBSIZE, thumbs):

    cnv = torgb(imageio.imread(FILE_IN))
    cnvh, cnvw, *_ = cnv.shape
    cnv = cv2.resize(cnv, (cnvw * RESCALE, cnvh * RESCALE))
    cnvh, cnvw, *_ = cnv.shape

    rowh = cnvh / ROW_NUM
    u = np.arange(0, cnvh, rowh)
    v = u + rowh
    slices = enumerate(zip(map(round, u), map(round, v)))

    len_slices = len(u)
    len_thumbs = len(thumbs)

    for rowi, (_, (ha, hb)) in enumerate(sorted(slices, key=srt(ROW_PROP))):
        xa = 0
        row = cnv[ha:hb, :]
        tmp = resize_landscape(row, THUMBSIZE)
        ratio = tmp.shape[1] / row.shape[1]

        while xa < row.shape[1]:
            xx = round(xa * ratio)

            compare = list()
            for key in thumbs:
                name, im = key
                # sanity checking
                if len(im.shape) != 3:
                    continue
                elif im.shape[2] != 3:
                    continue
                prt = tmp[:, xx:xx + im.shape[1]]
                metric = sum(cv2.sumElems(abs(prt - im[:, :prt.shape[1]])))
                compare.append((metric, key))

            _, key = min(compare)
            name, im = key
            thumbs.remove(key)

            path_src = os.path.join(FOLDER_SRC, name)

            im = imageio.imread(path_src)
            im = resize_landscape(im, row.shape[0])

            xb = xa + im.shape[1]
            prt = cnv[ha:hb, xa:xb]
            cnv[ha:hb, xa:xb] = im[:, :prt.shape[1]]
            xa = xb

            print(f"{len(thumbs)} / {len_thumbs} images, {rowi} / {len_slices} rows".ljust(40), end="\r")

        # cv2.imshow("Main", cv2.cvtColor(
        #     resize_landscape(cnv, 720), cv2.COLOR_RGB2BGR))
        # k = cv2.waitKey(1)
        # if k == ord("q"):
        #     sys.exit(1)

    print(f"{len(thumbs)} / {len_thumbs} images".ljust(40))
    return cnv


if __name__ == "__main__":
    import argparse

    # python mosaic_indie.py -f misc\logo.jpg -d src -o render.png -n 8

    # setup the parser
    parser = argparse.ArgumentParser()

    # add arguments
    parser.add_argument(
        "-f", required=True,
        help="Input file name", type=str
    )
    parser.add_argument(
        "-d", required=True,
        help="Input folder name", type=str
    )
    parser.add_argument(
        "-o", required=True,
        help="Output file name", type=str
    )
    parser.add_argument(
        "-n", required=True,
        help="Number of rows", type=int
    )
    parser.add_argument(
        "-p", nargs="?", default=0.5,
        help="Proportional center of construction", type=float
    )
    parser.add_argument(
        "-s", nargs="?", default=4,
        help="Rescaling factor", type=int
    )
    parser.add_argument(
        "-t", nargs="?", default=16,
        help="Pixel height of thumbnails", type=int
    )
    parser.add_argument(
        "-x", nargs="?", default="tmp",
        help="Output folder name for thumbnails", type=str
    )

    # parse arguments
    args = parser.parse_args()

    # set "constants"
    FILE_IN = os.path.realpath(args.f)
    FILE_OUT = os.path.realpath(args.o)
    FOLDER_SRC = os.path.realpath(args.d)
    FOLDER_TMP = os.path.realpath(args.x)
    RESCALE = args.s
    ROW_NUM = args.n
    ROW_PROP = args.p
    THUMBSIZE = args.t

    # make folder if it doesn't exist
    if not os.path.exists(FOLDER_TMP):
        os.makedirs(FOLDER_TMP)

    # make thumbnails
    print("CONVERTING / LOADING")

    thumbs = convert_or_load(FOLDER_SRC, THUMBSIZE)

    # make mosaic
    print("BUILDING".ljust(30))

    cnv = build(
        FILE_IN, RESCALE, ROW_NUM, ROW_PROP, FOLDER_SRC, THUMBSIZE, thumbs
    )

    # save the canvas
    print("SAVING".ljust(30))

    cv2.imwrite(FILE_OUT, cv2.cvtColor(cnv, cv2.COLOR_RGB2BGR))
    # imageio.imwrite(FILE_OUT, cnv)

    # all done
    print("DONE :)".ljust(30))
