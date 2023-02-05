"""Classes for specific shapes that data can be morphed into."""

from abc import ABC
import itertools

from scipy.spatial import distance


class Shape(ABC):
    """Abstract class for a shape."""

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.__class__.__name__.lower()

    def distance(self, x, y) -> float:
        raise NotImplementedError

    @staticmethod
    def _euclidean_distance(a, b) -> float:
        return distance.euclidean(a, b)


class Circle(Shape):
    """Class representing a hollow circle."""

    def __init__(self, data) -> None:
        self.cx = data.x.mean()
        self.cy = data.y.mean()
        self.r = 30  # TODO: think about how this could be calculated

    def distance(self, x, y) -> float:
        return abs(
            self._euclidean_distance((self.cx, self.cy), (x, y))
            - self.r
        )


class Bullseye(Shape):
    """Class representing a bullseye shape comprising two concentric circles."""

    def __init__(self, data) -> None:
        self.circles = [
            Circle(data.x.mean(), data.y.mean(), r)
            for r in [18, 37] # TODO: think about how this could be calculated
        ]

    def distance(self, x, y) -> float:
        return min(circle.distance(x, y) for circle in self.circles)


class Dots(Shape):
    """Class representing a 3x3 grid of dots."""

    def __init__(self, data) -> None:
        self.dots = list(
            itertools.product(
                data[coord].quantile([0.05, 0.5, 0.95]).tolist()
                for coord in ['x', 'y']
            )
        )

    def distance(self, x, y) -> float:
        return min(
            self._euclidean_distance(dot, (x, y))
            for dot in self.dots
        )


class Lines(Shape):
    """Class representing a shape consisting of multiple lines."""

    def __init__(self, *lines) -> None:
        self.lines = lines

    def distance(self, x, y) -> float:
        return min(
            self.distance_point_to_line(point=(x, y), line=line)
            for line in self.lines
        )

    def distance_point_to_line(self, point, line) -> float:
        """Calculates the minimum distance between a point and a line, used to
        determine if the points are getting closer to the target. Implementation
        based on `this VBA code`_

        .. this VBA code: http://local.wasp.uwa.edu.au/~pbourke/geometry/pointline/source.vba
        """
        start, end = line
        line_mag = self._euclidean_distance(start, end)

        if line_mag < 0.00000001:
            # Arbitrarily large value
            return 9999

        px, py = point
        x1, y1 = start
        x2, y2 = end

        u1 = (((px - x1) * (x2 - x1)) + ((py - y1) * (y2 - y1)))
        u = u1 / (line_mag * line_mag)

        if (u < 0.00001) or (u > 1):
            # closest point does not fall within the line segment, take the shorter
            # distance to an endpoint
            distance = max(
                self._euclidean_distance(point, start),
                self._euclidean_distance(point, end),
            )
        else:
            # Intersecting point is on the line, use the formula
            ix = x1 + u * (x2 - x1)
            iy = y1 + u * (y2 - y1)
            distance = self._euclidean_distance(point, (ix, iy))

        return distance


class XLines(Lines):
    """Class for X shape consisting of two lines."""

    def __init__(self, data) -> None:
        xmin, ymin = data.min()
        xmax, ymax = data.max()

        super().__init__(
            [[xmin, ymin], [xmax, ymax]],
            [[xmin, ymax], [xmax, ymin]]
        )

    def __repr__(self) -> str:
        return 'x'


class HorizontalLines(Lines):
    """Class for the horizontal lines shape."""

    def __init__(self, data) -> None:
        xmin, ymin = data.min()[['x', 'y']]
        xmax, ymax = data.max()[['x', 'y']]

        super().__init__(
            *[[[0, y], [100, y]] for y in [10, 30, 50, 70, 90]]
        ) # TODO: figure out the values based on the data

    def __repr__(self) -> str:
        return 'h_lines'


class VerticalLines(Lines):
    """Class for the vertical lines shape."""

    def __init__(self, data) -> None:
        xmin, ymin = data.min()[['x', 'y']]
        xmax, ymax = data.max()[['x', 'y']]

        super().__init__(
            *[[[x, 0], [x, 100]] for x in [10, 30, 50, 70, 90]]
        ) # TODO: figure out the values based on the data

    def __repr__(self) -> str:
        return 'v_lines'


# class Center(Lines): # TODO: does this even work?
#     """Class for the center shape."""

#     def __init__(self, data) -> None:
#         cx, cy = data.mean()[['x', 'y']]
#         super().__init__([[cx, cy], [cx, cy]])


class ShapeFactory:
    """Generates the desired shape."""

    AVAILABLE_SHAPES = {
        'circle': Circle,
        'bullseye': Bullseye,
        'dots': Dots,
        'x': XLines,
        'h_lines': HorizontalLines,
        'v_lines': VerticalLines,
        # 'center': Center,
    }

    def __init__(self, data) -> None:
        self.data = data

    def generate_shape(self, shape) -> Shape:
        try:
            return self.AVAILABLE_SHAPES[shape](self.data)
        except KeyError:
            raise ValueError(f'No such shape as {shape}.')


#     elif line_shape == 'wide_lines':
#         l1 = [[10, 0], [10, 100]]
#         l2 = [[90, 0], [90, 100]]
#         lines = [l1, l2]
#     elif line_shape == 'high_lines':
#         l1 = [[0, 10], [100, 10]]
#         l2 = [[0, 90], [100, 90]]
#         lines = [l1, l2]
#     elif line_shape == 'slant_up':
#         l1 = [[0, 0], [100, 100]]
#         l2 = [[0, 30], [70, 100]]
#         l3 = [[30, 0], [100, 70]]
#         l4 = [[50, 0], [100, 50]]
#         l5 = [[0, 50], [50, 100]]
#         lines = [l1, l2, l3, l4, l5]
#     elif line_shape == 'slant_down':
#         l1 = [[0, 100], [100, 0]]
#         l2 = [[0, 70], [70, 0]]
#         l3 = [[30, 100], [100, 30]]
#         l4 = [[0, 50], [50, 0]]
#         l5 = [[50, 100], [100, 50]]
#         lines = [l1, l2, l3, l4, l5]
#     elif line_shape == 'star':
#         star_pts = [10, 40, 40, 40, 50, 10, 60, 40, 90, 40, 65, 60, 75, 90, 50, 70, 25, 90, 35, 60]
#         pts = [star_pts[i:i + 2] for i in range(0, len(star_pts), 2)]
#         pts = [[p[0] * 0.8 + 20, 100 - p[1]] for p in pts]
#         pts.append(pts[0])
#         lines = [pts[i:i + 2] for i in range(0, len(pts) - 1, 1)]
#     elif line_shape == 'down_parab':
#         curve = [[x, -((x - 50) / 4)**2 + 90] for x in np.arange(0, 100, 3)]
#         lines = [curve[i:i + 2] for i in range(0, len(curve) - 1, 1)]
