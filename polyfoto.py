__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.2.0"
__email__ = "shane.drabing@gmail.com"

import os

import cv2
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


def imread_s(filepath):
    im = cv2.imread(filepath)
    if im is None:
        fmsg = "cannot read from {}".format
        msg = fmsg(os.path.normpath(filepath))
        raise FileNotFoundError(msg)
    return im


def to_bgr(im):
    if len(im.shape) == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    elif im.shape[2] == 4:
        im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
    return im


def resize_landscape(im, h):
    imh, imw, *_ = im.shape
    ratio = h / imh
    w = round(ratio * imw)
    reim = cv2.resize(im, (w, h))
    reim = to_bgr(reim)
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
            try:
                if os.path.exists(path_tmp):
                    im = imread_s(path_tmp)
                else:
                    im = imread_s(path_src)
                    im = resize_landscape(im, THUMBSIZE)
                    try:
                        cv2.imwrite(path_tmp, im)
                    except cv2.error:
                        # add argument for strict writing
                        fmsg = "cannot write to {}".format
                        msg = fmsg(os.path.normpath(path_tmp))
                        if False:
                            raise TypeError(msg)
                        print("polyfoto warning: {}".format(msg))
                        continue

                thumbs.append((name, im.astype(np.int16)))
            except FileNotFoundError as msg:
                print("polyfoto warning: {}".format(msg))
        except ValueError as e:
            print("polyfoto warning: {}".format(e))
            pass
    return thumbs


def build(FILE_IN, RESCALE, ROW_NUM, ROW_PROP, FOLDER_SRC, THUMBSIZE, thumbs):
    cnv = to_bgr(imread_s(FILE_IN))
    cnvh, cnvw, *_ = cnv.shape
    cnv = cv2.resize(cnv, (cnvw * RESCALE, cnvh * RESCALE))
    cnvh, cnvw, *_ = cnv.shape

    rowh = cnvh / ROW_NUM
    u = np.arange(0, cnvh, rowh)
    v = u + rowh
    slices = enumerate(zip(map(round, u), map(round, v)))

    len_slices = len(u)
    len_thumbs = len(thumbs)
    thumbs_copy = thumbs.copy()

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
            
            # cycle thumbnails
            if not thumbs:
                thumbs = thumbs_copy.copy()

            path_src = os.path.join(FOLDER_SRC, name)

            im = imread_s(path_src)
            im = resize_landscape(im, row.shape[0])

            xb = xa + im.shape[1]
            prt = cnv[ha:hb, xa:xb]
            cnv[ha:hb, xa:xb] = im[:, :prt.shape[1]]
            xa = xb

            print(f"{len(thumbs)} / {len_thumbs} images, {rowi} / {len_slices} rows".ljust(40), end="\r")

    print(f"{len(thumbs)} / {len_thumbs} images".ljust(40))
    return cnv


if __name__ == "__main__":
    import argparse
    import time

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

    # check to see if FILE_IN can be loaded at all
    imread_s(FILE_IN)

    # record the start time
    start_time = time.time()

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

    cv2.imwrite(FILE_OUT, cnv)

    # record the end time
    end_time = time.time()

    # calculate elapsed time
    elapsed_time = end_time - start_time

    # format string for time
    format_elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time*100))

    # all done
    print(("DONE in %s seconds :)" % (round(elapsed_time, 1)) ).ljust(30))
