__author__ = "Shane Drabing"
__license__ = "MIT"
__version__ = "0.3.1"
__email__ = "shane.drabing@gmail.com"

import os
import random

import cv2
import numpy as np


# CONSTANTS


IMG_FORMATS = (
    ".bmp", ".dib", ".jp2", ".jpe", ".jpeg", ".jpg", ".pbm",
    ".pgm", ".png", ".ppm", ".ras", ".sr", ".tif", ".tiff",
)


# FUNCTIONS


def prod(itr):
    n = 1
    for x in itr:
        n *= x
    return n


def rint(n):
    return int(round(n))


def sort_closure(prop, row_num):
    def sort_closuref(x):
        return abs(x[0] - row_num * prop)
    return sort_closuref


def endswith_any(string, itr):
    return any(map(string.endswith, itr))


def imread_s(filepath):
    im = cv2.imread(filepath)
    if im is None:
        fmsg = "cannot read from path: '{}'".format
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


def convert_or_load(folder_src, folder_tmp, thumbsize):
    thumbs = list()
    folder = list(filter(
        lambda x: endswith_any(x.lower(), IMG_FORMATS),
        os.listdir(folder_src)
    ))
    len_folder = len(folder)

    # raise error if no usable images
    if (len_folder == 0):
        raise ValueError("folder contains no image files")

    for i, name in enumerate(folder):
        if (i % 100 == 0):
            print(f"{i} / {len_folder}".ljust(30), end="\r")

        path_src = os.path.realpath(os.path.join(folder_src, name))
        path_tmp = os.path.realpath(os.path.join(folder_tmp, name))

        try:
            if os.path.exists(path_tmp):
                im = imread_s(path_tmp)
            else:
                im = imread_s(path_src)
                im = resize_landscape(im, thumbsize)
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
    return thumbs


def build(file_in, folder_src, thumbs, thumbsize,
          rescale, row_num, row_prop, consume):
    cnv = to_bgr(imread_s(file_in))
    cnv = cv2.resize(cnv, (cnv.shape[1] * rescale, cnv.shape[0] * rescale))
    cnvh, cnvw, *_ = cnv.shape

    rowh = cnvh / row_num
    u = np.arange(0, cnvh, rowh)
    v = u + rowh
    slices = enumerate(zip(map(rint, u), map(rint, v)))

    len_slices = len(u)
    len_thumbs = len(thumbs)
    thumbs_copy = thumbs.copy()

    f = sort_closure(row_prop, row_num)
    for rowi, (_, (ha, hb)) in enumerate(sorted(slices, key=f)):
        xa = 0
        row = cnv[ha:hb, :]
        tmp = resize_landscape(row, thumbsize)
        ratio = tmp.shape[1] / row.shape[1]

        while xa < row.shape[1]:
            xx = rint(xa * ratio)

            compare = list()
            for key in thumbs:
                name, im = key
                # sanity checking
                if len(im.shape) != 3 or im.shape[2] != 3:
                    continue
                prt = tmp[:, xx:xx + im.shape[1]]
                metric = sum(cv2.sumElems(abs(prt - im[:, :prt.shape[1]])))
                compare.append((metric, key))

            _, key = min(compare)
            name, im = key
            
            # chance to consume
            if random.random() < consume:
                thumbs.remove(key)

            # cycle thumbnails
            if not thumbs:
                thumbs = thumbs_copy.copy()

            path_src = os.path.join(folder_src, name)

            im = imread_s(path_src)
            im = resize_landscape(im, row.shape[0])

            xb = int(xa + im.shape[1])
            prt = cnv[ha:hb, xa:xb]
            cnv[ha:hb, xa:xb] = im[:, :prt.shape[1]]
            xa = xb

            print(f"{len(thumbs)} / {len_thumbs} images, " +
                  f"{rowi} / {len_slices} rows".ljust(40), end="\r")

    print(f"{len(thumbs)} / {len_thumbs} images".ljust(40))
    return cnv


# SCRIPT


if __name__ == "__main__":
    import argparse

    # setup the parser
    parser = argparse.ArgumentParser()

    # define arguments
    details = (
        ("-f", None, None, str, "Input file name"),
        ("-d", None, None, str, "Input folder name"),
        ("-o", None, None, str, "Output file name"),
        ("-n", None, None, int, "Number of rows"),
        ("-p", "?", 0.5, float, "Proportional center of construction"),
        ("-c", "?", 1.0, float, "Proportional chance of consumption"),
        ("-s", "?", 4, int, "Rescaling factor"),
        ("-t", "?", 16, int, "Pixel height of thumbnails"),
        ("-x", "?", "tmp", str, "Output folder name for thumbnails"),
    )

    # add arguments
    keys = ("nargs", "default", "type", "help")
    for name, *values in details:
        kwargs = dict(zip(keys, values))
        parser.add_argument(name, **kwargs)

    # parse arguments
    args = parser.parse_args()

    # make "tmp" folder if it doesn't exist
    if not os.path.exists(args.x):
        os.makedirs(args.x)

    # check to see if file_in can be loaded at all
    imread_s(args.f)

    # make thumbnails
    print("CONVERTING / LOADING")
    thumbs = convert_or_load(args.d, args.x, args.t)

    # make mosaic
    print("BUILDING".ljust(30))
    cnv = build(
        args.f, args.d, thumbs, args.t, args.s, args.n, args.p, args.c
    )

    # save the canvas
    print("SAVING".ljust(30))
    cv2.imwrite(args.o, cnv)

    # all done
    print("DONE :)".ljust(30))
