import math
import os
import cv2
import colorsys
from numba import njit


def get_colours():
    colours = []
    for i in range(240):
        if 111 <= i & i < 130:
            continue
        h = i / 360.0
        r, g, b = colorsys.hls_to_rgb(h, 0.5, 1.0)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        colours.append([r, g, b])
        r, g, b = colorsys.hls_to_rgb(h, 0.55, 1.0)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        colours.append([r, g, b])
    return colours


@njit(nopython=True)
def norm(vec):
    return math.sqrt(vec[0]*vec[0] + vec[1]*vec[1] + vec[2]*vec[2])


def get_difference(img1, img2, colours):
    res = img1.copy() - img2
    for x in range(res.shape[0]):
        for y in range(res.shape[1]):
            len = int(norm(res[x][y]))
            res[x][y] = colours[len]
    return res


def crop_image(w, h, img):
    res = img.copy()
    res = res[
          int((res.shape[0] - w) / 2): int((res.shape[0] + w) / 2),
          int((res.shape[1] - h) / 2): int((res.shape[1] + h) / 2)
    ]
    return res


def get_difference_images(img1, img2, colours):
    w, h, _ = img1.shape
    w = min(w, img2.shape[0])
    h = min(h, img2.shape[1])
    crop1 = crop_image(w, h, img1)
    crop2 = crop_image(w, h, img2)
    result = get_difference(crop1, crop2, colours)
    return cv2.addWeighted(crop1, 0, result, 1, 0)


# img1 = cv2.imread("1sd.jpg")
# img2 = cv2.imread("2sd.jpg")
img = []

for root, dirs, files in os.walk("IMG"):
    for file in files:
        if len(img) < 2:        
            if file and file.endswith(".jpg"):
                img.append(os.path.join("IMG", file))


res = get_difference_images(cv2.imread(img[0]), cv2.imread(img[1]), get_colours())
cv2.imwrite(os.path.join("IMG", "Z_color_res.jpg"), res)
cv2.imshow("result", res)
cv2.waitKey(0)

