import math
# from PyQt5 import QtCore, QtGui, QtWidgets
from PySide2 import QtWidgets, QtCore, QtGui


COLORS = {
    'controlpoint.center': 'yellow',
    'controlpoint.centerselected': 'white',
    'controlpoint.tangentlocked': 'orange',
    'controlpoint.autotangent': 'red',
    'background.color': '#222222',
    'background.border': '#222222',
    'background.griddark': '#111111',
    'background.gridlight': '#353535',
    'bezier.border': 'red',
    'bezier.body': 'grey'
}


class BezierEqualizer(QtWidgets.QWidget):
    bezierCurveEdited = QtCore.Signal()
    bezierCurveEditBegin = QtCore.Signal()
    bezierCurveEditEnd = QtCore.Signal()

    Smoothed = 0
    Flatten = 1

    def __init__(self, parent=None):
        super(BezierEqualizer, self).__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(QtCore.QSize(250, 100))

        self.renderhint = QtGui.QPainter.Antialiasing
        self.colors = COLORS.copy()
        self.isclicked = False
        self.gridvisible = True
        self.editabletangents = True
        self.drawbody = False
        self.grid_horizontal_divisions = 5
        self.grid_vertical_divisions = 25
        self.grid_main_disivions_mult = 4
        self.auto_tangent_function = auto_tangent_smoothed
        self.holding = False

        self.picked_center = None
        self.picked_tangent = None
        self.controlpoints = []

    def mouseMoveEvent(self, event):
        if self.isclicked is False:
            return

        if self.editabletangents is True and self.picked_tangent is not None:
            self.picked_tangent.autotangent = False
            self.picked_tangent.move_tangent(event.pos())
            auto_tangent_beziercurve(
                controlpoints=self.controlpoints,
                skip=self.picked_tangent,
                auto_tangent_function=self.auto_tangent_function)
            self.repaint()
            self.bezierCurveEdited.emit()
            return

        if not self.picked_center:
            self.repaint()
            self.bezierCurveEdited.emit()
            return
        rect = self.rect()
        point = event.pos()
        cursor = self.mapFromGlobal(QtGui.QCursor.pos())
        self.picked_center.move(point, rect)
        offset = (rect.width() + rect.height()) / 10
        extended_rect = grow_rect(rect, offset)
        if self.picked_center.isboundary is True:
            self.repaint()
            self.bezierCurveEdited.emit()
            return
        if not extended_rect.contains(cursor) and self.holding is False:
            self.controlpoints.remove(self.picked_center)
            self.holding = True
        elif extended_rect.contains(cursor) and self.holding is True:
            self.controlpoints.append(self.picked_center)
            self.controlpoints = sorted(self.controlpoints)
            self.holding = False
        auto_tangent_beziercurve(
            controlpoints=self.controlpoints,
            auto_tangent_function=self.auto_tangent_function)
        self.repaint()
        self.bezierCurveEdited.emit()

    def mousePressEvent(self, event):
        if not self.controlpoints:
            return

        self.isclicked = True
        point = event.pos()
        controlpoints = self.controlpoints
        self.picked_center = pick_controlpoint_center(controlpoints, point)
        self.picked_tangent = pick_controlpoint_tangent(controlpoints, point)

        if not self.picked_center and not self.picked_tangent:
            controlpoint = insert_controlpoint_in_line(point, controlpoints)
            self.controlpoints.append(controlpoint)
            self.controlpoints = sorted(controlpoints)
            auto_tangent_beziercurve(
                self.controlpoints, self.auto_tangent_function)
            self.picked_center = controlpoint

        if self.picked_center:
            select_controlpoint(self.picked_center, self.controlpoints)

        self.repaint()
        self.bezierCurveEditBegin.emit()

    def mouseReleaseEvent(self, _):
        self.isclicked = False
        self.picked_center = None
        self.picked_tangent = None
        self.holding = False
        self.repaint()
        self.bezierCurveEditEnd.emit()

    def resizeEvent(self, event):
        if self.isVisible() is False:
            return
        for controlpoint in self.controlpoints:
            controlpoint.resize(event.oldSize(), event.size())
        self._check_bonudaries()
        self.repaint()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(self.renderhint)
        rect = self.rect()
        draw_background(painter, rect, self.colors)
        if self.gridvisible is True:
            draw_grid(
                painter, rect,
                vertical_small_graduation=self.grid_vertical_divisions,
                horizontal_small_graduation=self.grid_horizontal_divisions,
                vertical_big_graduation=self.grid_main_disivions_mult,
                horizontal_big_graduation=self.grid_main_disivions_mult,
                colors=None)
        if not self.controlpoints:
            return
        if self.drawbody is True:
            path = create_beziercurve_path(self.controlpoints, self.rect())
            draw_bezierbody(painter, path, self.colors)
        path = create_beziercurve_path(self.controlpoints)
        draw_bezierpath(painter, path, self.colors)
        for controlpoint in self.controlpoints:
            draw_controlpoint(
                painter=painter,
                controlpoint=controlpoint,
                drawtangent=self.editabletangents,
                colors=self.colors)

    def values(self, sample):
        path = create_beziercurve_path(self.controlpoints)
        rect = self.rect()
        return compute_bezier_curve_values(path, rect, sample)

    def selectedControlPoint(self):
        for controlpoint in self.controlpoints:
            if controlpoint.selected is True:
                return controlpoint
        return None

    def setValues(self, values):
        if not values:
            self.controlpoints = []
        if len(values) == 1:
            raise ValueError('At least 2 values has to be provided')
        rect = self.rect()
        self.controlpoints = create_beziercurve(values, rect, linear=True)
        self.controlpoints[0].isboundary = True
        self.controlpoints[-1].isboundary = True
        self.repaint()

    def setColor(self, key, colorname):
        if key not in self.colors:
            raise KeyError('{} is not a valid key'.format(key))
        self.colors[key] = colorname

    def updateColors(self, colors):
        for key in colors:
            if key not in self.colors:
                raise KeyError('{} is not a valid key'.format(key))
        self.colors.update(colors)

    def setRenderHint(self, renderhint):
        self.renderhint = renderhint

    def setGridVisible(self, state):
        self.gridvisible = state

    def setEditableTangents(self, state):
        self.editabletangents = state

    def setBodyVisible(self, state):
        self.drawbody = state

    def setGridHorizontalDivision(self, division):
        self.grid_horizontal_divisions = division

    def setGridVerticalDivision(self, division):
        self.grid_vertical_divisions = division

    def setGridMainDivisionsMult(self, division):
        self.grid_main_disivions_mult = division

    def setAutoTangentMode(self, mode):
        auto_tangent_functions = [
            auto_tangent_smoothed,
            auto_tangent_flatten]
        self.auto_tangent_function = auto_tangent_functions[mode]


###############################################################################
############################## CONTROLPOINT ###################################
###############################################################################


class ControlPoint():
    def __init__(self, center, tangentin=None, tangentout=None):
        self.center = QtCore.QPointF(center)
        self.tangentin = QtCore.QPointF(tangentin or center)
        self.tangentout = QtCore.QPointF(tangentout or center)
        self.isboundary = False
        self.autotangent = True
        self.selected = False
        self.linear = False

    def move(self, point, rect=None):
        if self.isboundary is True:
            point.setX(self.center.x())
        if rect is not None:
            clamp_point_in_rect(point, rect)

        delta = self.center - point
        self.center -= delta
        self.tangentin -= delta
        self.tangentout -= delta

    def move_tangent(self, point1, point2=None):
        if point1.x() < self.center.x():
            parent = self.tangentin
            child = self.tangentout
        else:
            parent = self.tangentout
            child = self.tangentin

        parent.setX(point1.x())
        parent.setY(point1.y())
        mirror = point2 or compute_mirror_tangent(self.center, parent, child)
        child.setX(mirror.x())
        child.setY(mirror.y())

    def resize(self, old_size, new_size):
        move_point_from_resized_rect(self.center, old_size, new_size)
        move_point_from_resized_rect(self.tangentin, old_size, new_size)
        move_point_from_resized_rect(self.tangentout, old_size, new_size)

    def __lt__(self, controlpoint):
        return self.center.x() < controlpoint.center.x()


def insert_controlpoint_in_line(point, controlpoints):
    controlpoints = sorted(controlpoints)
    for controlpoint in controlpoints[1:]:
        if controlpoint.center.x() > point.x():
            break
    controlpoint = ControlPoint(point, QtCore.QPoint(), QtCore.QPoint())
    return controlpoint


def pick_controlpoint_center(controlpoints, point, tolerance=8):
    for controlpoint in controlpoints:
        if distance(controlpoint.center, point) < tolerance:
            return controlpoint
    return None


def pick_controlpoint_tangent(controlpoints, point, tolerance=8):
    for controlpoint in controlpoints:
        condition = (
            distance(controlpoint.tangentin, point) < tolerance or
            distance(controlpoint.tangentout, point) < tolerance)
        if condition:
            return controlpoint
    return None


def compute_mirror_tangent(center, tangent, child=None):
    angle = compute_angle(center, tangent) - math.pi
    ray = distance(center, child or tangent)
    return point_on_circle(angle, ray, center)


def auto_tangent_beziercurve(
        controlpoints, skip=None, auto_tangent_function=None):
    """
    This apply the good autotangent function on every controlpoint on a bezier
    curve.
    """
    auto_tangent_function = auto_tangent_function or auto_tangent_smoothed
    controlpoints = sorted(controlpoints)
    for i, controlpoint in enumerate(controlpoints):
        if controlpoint is skip:
            continue
        if controlpoint.autotangent is False:
            continue
        if i == 0:
            auto_tangent_boundary_controlpoint(
                controlpoint, controlpoints[i + 1])
            continue
        if i == len(controlpoints) - 1:
            auto_tangent_boundary_controlpoint(
                controlpoint, controlpoints[i - 1])
            continue
        before = controlpoints[i - 1]
        after = controlpoints[i + 1]
        auto_tangent_function(controlpoint, before, after)


def auto_tangent_boundary_controlpoint(controlpoint, target):
    """ 
    This function compute the auto tangent for the first or the last point of
    an bezier curve
    """
    angle = compute_angle(controlpoint.center, target.center)
    ray = distance(controlpoint.center, target.center) * .3
    tangent = point_on_circle(angle, ray, controlpoint.center)
    controlpoint.move_tangent(tangent)


def auto_tangent_smoothed(controlpoint, before, after):
    """
    This function create an auto smoothed tangent on a given controlpoint.
    To compute the tangent angle, it use the controle point before and after
    the given one on a bezier curve.
    To define a smoothed angle, it calculate the average angle between the
    before out tangent --> control point center and the 
    control point center --> after in tangent.
    """
    angle1 = compute_angle(before.tangentout, controlpoint.center)
    angle2 = compute_angle(controlpoint.center, after.tangentin)
    # clamp the angle to avoid tangent swap
    if abs(angle1 - angle2) > math.pi:
        if angle1 > angle2:
            angle1 -= 2 * math.pi
        else:
            angle2 -= 2 * math.pi

    width = after.center.x() - before.center.x()
    # offset the value to avoid ZeroDivisionError
    if width == 0:
        width += 1e-5
    width_before = controlpoint.center.x() - before.center.x()
    factor = width_before / width
    angle = (angle1 * (1 - factor)) + (angle2 * factor)

    ray_in = distance(before.center, controlpoint.center) * 0.3
    ray_out = distance(controlpoint.center, after.center) * 0.3

    tangent1 = point_on_circle(angle, ray_out, controlpoint.center)
    tangent2 = point_on_circle(angle + math.pi, ray_in, controlpoint.center)
    controlpoint.move_tangent(tangent1, tangent2)


def auto_tangent_flatten(controlpoint, before, after):
    condition = (
        controlpoint.center.y() >= before.center.y() and
        controlpoint.center.y() >= after.center.y() or
        controlpoint.center.y() <= before.center.y() and
        controlpoint.center.y() <= after.center.y())
    if condition:
        angle = 0
    else:
        angle1 = compute_angle(before.tangentout, controlpoint.center)
        angle2 = compute_angle(controlpoint.center, after.tangentin)
        if abs(angle1) > abs(angle2):
            angle = angle1
        else:
            angle = angle2

    ray_in = distance(before.center, controlpoint.center) * 0.3
    horizontal = abs(before.center.x() - controlpoint.center.x())
    ray_in = clamp(ray_in, 0, horizontal)
    ray_out = distance(controlpoint.center, after.center) * 0.3
    horizontal = abs(controlpoint.center.x() - after.center.x())
    ray_out = clamp(ray_out, 0, horizontal)

    tangent1 = point_on_circle(angle, ray_out, controlpoint.center)
    tangent2 = point_on_circle(angle + math.pi, ray_in, controlpoint.center)
    controlpoint.move_tangent(tangent1, tangent2)


def compute_bezier_curve_values(path, rect, sample):
    """
    This function compute the values drawn by an horizontal bezier curve as
    QPainterPath. Sample give the number of samples are requested.
    The result is a list of floats. 0.0 is the smallest visible value and
    1.0 is the highest visible value but higher and lower values can be
    returned if the bezier curve is out of rect on sample.
    """
    if sample < 2:
        raise ValueError("At least 2 values can be requested (start and end)")

    # To find an y coordinate on a horizontal bezier curve from a x coordinate
    # given, we create a vertical really thin rectanglular QPainterPath.
    # Use the QPainterPath.intersected() return a QPainterPath which start
    # exactly on the intersection.
    lines = [vertical_path(rect, x) for x in split_value(rect.width(), sample)]
    intersections = [path.intersected(line) for line in lines]
    points = [intersection.pointAtPercent(0) for intersection in intersections]
    return [1 - (point.y() / rect.height()) for point in points]


###############################################################################
############################### TRIGONOMETRY ##################################
###############################################################################


def compute_ray_limit(angle, point1, point2):
    limit_x = abs(point1.x() - point2.x())
    limit_y = abs(point1.y() - point2.y())
    angle = ((angle / (math.pi / 2) - 0.5) * 2)
    limit_x *= 1 - abs(angle) if angle >= 0 else 1
    limit_y *= 1 - abs(angle) if angle <= 0 else 1
    limit_xy = (abs(angle) / 4) + .75
    return (limit_x + limit_y) * limit_xy


def point_on_circle(angle, ray, center):
    x = ray * math.cos(float(angle))
    y = ray * math.sin(float(angle))
    return QtCore.QPointF(center.x() + x, center.y() + y)


def compute_angle(point1, point2):
    point3 = QtCore.QPointF(point2.x(), point1.y())
    return math.radians(compute_absolute_angle_c(point3, point2, point1))


def compute_absolute_angle_c(a, b, c):
    quarter = get_quarter(a, b, c)
    try:
        angle_c = compute_angle_c(a, b, c)
    except ZeroDivisionError:
        return 360 - (90 * quarter)

    if quarter == 0:
        return round(180.0 + angle_c, 1)
    elif quarter == 1:
        return round(270.0 + (90 - angle_c), 1)
    elif quarter == 2:
        return round(angle_c, 1)
    elif quarter == 3:
        return math.fabs(round(90.0 + (90 - angle_c), 1))


def compute_angle_c(a, b, c):
    return math.degrees(math.atan(distance(a, b) / distance(a, c)))


def get_quarter(a, b, c):
    quarter = None
    if b.y() <= a.y() and b.x() < c.x():
        quarter = 0
    elif b.y() < a.y() and b.x() >= c.x():
        quarter = 1
    elif b.y() >= a.y() and b.x() > c.x():
        quarter = 2
    elif b.y() >= a.y() and b.x() <= c.x():
        quarter = 3
    return quarter


def distance(a, b):
    """ compute distance between two points """
    x = (b.x() - a.x())**2
    y = (b.y() - a.y())**2
    return math.sqrt(abs(x + y))


def select_controlpoint(selected_controlpoint, controlpoints):
    for controlpoint in controlpoints:
        controlpoint.selected = False
    selected_controlpoint.selected = True


def create_beziercurve(values, rect, linear=False):
    """ TODO: docstring """
    x_pos = split_value(rect.width(), len(values))
    y_pos = [rect.height() * (1 - value) for value in values]
    breakpoints_indices = get_break_indices(values)
    controlpoints = []
    for i, (x, y) in enumerate(zip(x_pos, y_pos)):
        if i not in breakpoints_indices:
            continue
        controlpoint = ControlPoint(QtCore.QPointF(x, y))
        controlpoint.linear = linear
        controlpoints.append(controlpoint)
    if linear is False:
        auto_tangent_beziercurve(controlpoints)
    # some offset can appear after resizing the widget which cause some
    # issues on the limits control point. This ensure that the first
    # and the last point has the right x value
    controlpoints[0].center.setX(0)
    controlpoints[-1].center.setX(rect.right())
    return controlpoints


def move_point_from_resized_rect(point, old_size, new_size):
    """
    This function move a point with a reference size and a new size.
    """
    x = (point.x() / old_size.width()) * new_size.width()
    y = (point.y() / old_size.height()) * new_size.height()
    point.setX(x)
    point.setY(y)


###############################################################################
########################### RECT AND PAINTERPATH ##############################
###############################################################################


def vertical_path(rect, x):
    """
    This function create a super tiny vertical rectangle on the x coordinate.
    This is use to find a Y coordinate with X coordinate given on a bezier
    curve.
    """
    point1 = QtCore.QPointF(x, rect.top() - 1e10)
    point2 = QtCore.QPointF(x, rect.bottom() + 1e10)
    point3 = QtCore.QPointF(x + 1e-5, rect.bottom() + 1e10)
    point4 = QtCore.QPointF(x + 1e-5, rect.top() - 1e10)
    path = QtGui.QPainterPath(point1)
    path.lineTo(point2)
    path.lineTo(point3)
    path.lineTo(point4)
    return path


def create_rect_from_point(center, segment_lenght=8):
    rectangle = QtCore.QRectF(0, 0, segment_lenght, segment_lenght)
    rectangle.moveCenter(center)
    return rectangle


def clamp_point_in_rect(point, rect):
    if point.x() < rect.left():
        point.setX(rect.left())
    if point.x() > rect.right():
        point.setX(rect.right())
    if point.y() < rect.top():
        point.setY(rect.top())
    if point.y() > rect.bottom():
        point.setY(rect.bottom())


def create_beziercurve_path(controlpoints, rect=None):
    controlpoints = sorted(controlpoints)
    center = controlpoints[0].center
    out = controlpoints[0].tangentout
    path = QtGui.QPainterPath(center)
    for controlpoint in controlpoints:
        if controlpoint.linear is True:
            path.cubicTo(*[controlpoint.center] * 3)
            out = controlpoint.center
            continue
        path.cubicTo(out, controlpoint.tangentin, controlpoint.center)
        out = controlpoint.tangentout
    if rect is None:
        return path
    path.lineTo(rect.bottomRight())
    path.lineTo(rect.bottomLeft())
    path.lineTo(controlpoints[0].center)
    return path


def grow_rect(rect, value):
    return QtCore.QRect(
        rect.left() - value,
        rect.top() - value,
        rect.width() + (value * 2),
        rect.height() + (value * 2))


###############################################################################
################################ ARRAY UTILS ##################################
###############################################################################


def clamp(value, minimum, maximum):
    if value > maximum:
        return maximum
    if value < minimum:
        return minimum
    return value


def get_break_indices(array):
    """
    This function parse a list of numerical values (int, long, float).
    It return the indice in the list where the value is not an linear
    interpolation of the adjacent values. The 0 and the last index are
    everytime returned.
    e.g.
    |                 .     .
    |           .            .
    |      .                  .
    |  .                       .
    ___________________________________
    This will return the indices 0, 3, 4 and 7
    """
    break_indexes = []
    for i, value in enumerate(array):
        if i == 0:
            previous_value = value
            break_indexes.append(i)
            continue
        if i == len(array) - 1:
            break_indexes.append(i)
            break
        next_value = array[i + 1]
        boundarie_average = (next_value + previous_value) / 2.0
        if abs(value - boundarie_average) > 1e-3:
            break_indexes.append(i)
        previous_value = value
    return break_indexes


def split_value(value, sample):
    """
    This array utils split a float in list of sample from 0 to the given value.
    e.g. split_value(100, 10) will return a list of 10 sample from 0 to 100
    with an equal difference :
    [0.0, 11.11, 22.22, 33.33, 44.44, 55.55, 66.66, 77.77, 88.88, 100.0]
    """
    increment = value / (sample - 1)
    return [increment * i for i in range(sample)]


###############################################################################
############################## DRAWS FUNCTION #################################
###############################################################################


def draw_background(painter, rect, colors=None):
    colors = colors or COLORS.copy()
    pen = QtGui.QPen(QtGui.QColor(colors['background.griddark']))
    pen.setStyle(QtCore.Qt.SolidLine)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor(colors['background.color']))
    painter.drawRect(rect)


def draw_grid(
        painter, rect,
        vertical_small_graduation=25,
        horizontal_small_graduation=4,
        vertical_big_graduation=4,
        horizontal_big_graduation=-1,
        colors=None):
    colors = colors or COLORS.copy()

    pen = QtGui.QPen(QtGui.QColor(colors['background.griddark']))
    pen.setWidth(2)
    painter.setPen(pen)
    lefts = split_value(rect.width(), vertical_small_graduation)
    for left in lefts:
        painter.drawLine(
            QtCore.QPoint(left, 0),
            QtCore.QPoint(left, rect.bottom()))
    tops = split_value(rect.height(), horizontal_small_graduation)
    for top in tops:
        painter.drawLine(
            QtCore.QPoint(0, top),
            QtCore.QPoint(rect.right(), top))

    pen = QtGui.QPen(QtGui.QColor(colors['background.gridlight']))
    pen.setWidth(5)
    painter.setPen(pen)
    lefts = split_value(rect.width(), vertical_big_graduation)
    for left in lefts:
        painter.drawLine(
            QtCore.QPoint(left, 0),
            QtCore.QPoint(left, rect.bottom()))
    tops = split_value(rect.height(), horizontal_big_graduation)
    for top in tops:
        painter.drawLine(
            QtCore.QPoint(0, top),
            QtCore.QPoint(rect.right(), top))


def draw_controlpoint(painter, controlpoint, drawtangent=True, colors=None):
    colors = colors or COLORS.copy()
    selected = 'controlpoint.centerselected'
    colorkey = selected if controlpoint.selected else 'controlpoint.center'
    painter.setBrush(QtGui.QColor(colors[colorkey]))
    painter.setPen(QtGui.QColor(colors[colorkey]))
    center_rect = create_rect_from_point(controlpoint.center)
    painter.drawRect(center_rect)

    if drawtangent is False or controlpoint.linear is True:
        return

    painter.setBrush(QtGui.QColor(0, 0, 0, 0))
    if controlpoint.autotangent is True:
        color = colors['controlpoint.autotangent']
    else:
        color = colors['controlpoint.tangentlocked']
    painter.setPen(QtGui.QColor(color))

    tin_rect = create_rect_from_point(controlpoint.tangentin)
    painter.drawRect(tin_rect)
    line = QtCore.QLine(
        controlpoint.tangentin.toPoint(),
        controlpoint.center.toPoint())
    painter.drawLine(line)

    tout_rect = create_rect_from_point(controlpoint.tangentout)
    painter.drawRect(tout_rect)
    line = QtCore.QLine(
        controlpoint.center.toPoint(),
        controlpoint.tangentout.toPoint())
    painter.drawLine(line)


def draw_bezierpath(painter, path, colors=None):
    colors = colors or COLORS.copy()
    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
    painter.setBrush(brush)
    painter.setPen(QtGui.QColor(colors['bezier.border']))
    painter.drawPath(path)


def draw_bezierbody(painter, path, colors=None):
    colors = colors or COLORS.copy()
    brush = QtGui.QBrush(QtGui.QColor(colors['bezier.body']))
    painter.setBrush(brush)
    painter.setPen(QtGui.QColor(0, 0, 0, 0))
    painter.drawPath(path)


# if __name__ == "__main__":
#     app = QtWidgets.QApplication([])
#     wid = BezierEqualizer()
#     wid.setValues([0, .5, 1])
#     wid.setAutoTangentMode(BezierEqualizer.Limited)
#     wid.show()
#     app.exec_()
