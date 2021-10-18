from scipy.ndimage import uniform_filter
from skimage import data, io, filters, feature, color
from skimage.draw import rectangle, rectangle_perimeter, set_color
from skimage.filters.rank import entropy
from skimage.morphology import disk
from skimage.util import img_as_ubyte
import matplotlib.pyplot as plt
import numpy as np

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


class Size:
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def __repr__(self):
        return f"Size({self.w}, {self.h})"
    

class View:
    def __init__(self, point, size):
        self.point = point
        self.size = size
        self.p0 = point
        self.p1 = Point(point.x + size.w, point.y + size.h)

    def __repr__(self):
        return f"View({self.point}, {self.size})"

    def product(v0, v1):
        p0 = Point(max(v0.p0.x, v1.p0.x), max(v0.p0.y, v1.p0.y))
        p1 = Point(min(v0.p1.x, v1.p1.x), min(v0.p1.y, v1.p1.y))
        if not (p0.x < p1.x and p0.y < p1.y):
            return View(Point(0, 0), Size(0, 0))
        else:
            return View(p0, Size(p1.x - p0.x, p1.y - p0.y)) 


class Placer:
    def __init__(self, src, size):
        self.src = src
        self.size = Size(size[0], size[1])
        self.padding = None
        self.image = None
        self.__view = None

    def load(self):
        image = io.imread(self.src)
        if len(image.shape) == 2:
            image = color.gray2rgb(image)

        image_size = Size(*reversed(image.shape[:2]))
        if not self.__view:
            self.view = ((0, 0), tuple(reversed(image.shape[:2])))

        if self.padding:
            padding = self.padding
            padded_view = View(Point(padding, padding), Size(image_size.w - padding * 2, image_size.h - padding * 2))
            self.view = View.product(self.view, padded_view)

        self.image = image

    @property
    def view(self):
        return self.__view

    @view.setter
    def view(self, val):
        if type(val) is View:
            self.__view = val
        else:
            p, s = val
            self.__view = View(Point(p[0], p[1]), Size(s[0], s[1]))

    def get_slice(self, view):
        return (slice(view.p0.y, view.p1.y), slice(view.p0.x, view.p1.x))

    def run(self):
        if not self.image:
            self.load()

        size = self.size
        view = self.view

        gray = color.rgb2gray(self.image)[self.get_slice(self.view)]
        # edge = filters.sobel(gray)
        # edge = gray
        # edge = feature.canny(gray, sigma=2)
        edge = feature.canny(gray)

        entropy = filters.rank.entropy(img_as_ubyte(edge), disk(20))

        avgs = uniform_filter(entropy, size=(size.h, size.w), origin=(1 - size.h // 2, 1 - size.w // 2))
        tmp = avgs[:1 - size.h, :1 - size.w]
        pos = Point(*reversed(np.unravel_index(np.argmin(tmp), tmp.shape)))

        self.edge = edge
        self.entropy = entropy
        self.avgs = avgs

        self.value = avgs[(pos.y, pos.x)]
        self.mean = np.mean(gray[pos.y:(pos.y + size.h), pos.x:(pos.x + size.w)])
        self.pos = Point(pos.x + view.p0.x, pos.y + view.p0.y)

    def analyze(self, dst):
        try:
            self.pos
        except NameError:
            self.run()
        image = self.image
        view = self.view
        pos = self.pos

        rr, cc = rectangle((view.p0.y, view.p0.x), end=(view.p1.y, view.p1.x), shape=image.shape)
        set_color(image, (rr, cc), (20, 100, 200), 0.3)

        rr, cc = rectangle((pos.y, pos.x), extent=(self.size.h, self.size.w), shape=image.shape)
        set_color(image, (rr, cc), (255, 20, 20), 0.3)


        fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(ncols=2, nrows=2, figsize=(12,4))
        img0 = ax0.imshow(image, cmap=plt.cm.gray)
        ax0.set_title("Image")

        img1 = ax1.imshow(self.edge, cmap=plt.cm.gray)
        ax1.set_title("Edge")

        img2 = ax2.imshow(self.entropy, cmap=plt.cm.gray)
        ax2.set_title("Entropy")

        img3 = ax3.imshow(self.avgs, cmap=plt.cm.gray)
        ax3.set_title("Moving avg")

        fig.tight_layout()
        plt.savefig(dst)

