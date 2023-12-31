import typing as t
import plotly.graph_objects as go
import numpy as np
from math import pi
COLOR_OTHER = "#696969"


def deg_to_rad(degrees: float) -> float:
    """Converts degrees to radians.

    Args:
        degrees (float).

    Returns:
        The converted value.

    Example(s):
        >>> deg_to_rad(90)
        1.5707963267948966
        >>> deg_to_rad(135)
        2.356194490192345
    """
    return degrees * pi / 180


def add_text(figure: go.Figure,
             point: list[float, float],
             text: str,
             size: float,
             color: str = "black",
             family: str = "Roboto") -> None:
    """Adds text to the figure.

    Args:
        figure (go.Figure).
        point (list[float, float]): the anchor of the text.
        text (str).
        size (float).
        color (str). Defaults to black.
        family (str). Defaults to 'Roboto'.
    """
    figure.add_annotation(x=point[0], y=point[1], text=text,
                          showarrow=False, ax=0, ay=0,
                          font=dict(size=size, color=color, family=family))


def add_rectangle(figure: go.Figure,
                  x_coords: list[float],
                  y_coords: list[float],
                  color: str) -> None:
    """Adds a rectangle to the figure.

    Args:
        figure (go.Figure).
        x_coords (list[float]).
        y_coords (list[float]).
        color (str).

    Example(s):
        >>> figure = go.Figure()
        >>> add_rectangle(figure, [0, 0, 20, 20], [0, 30, 30, 0], "blue")
        # Adds a 20*30 blue rectangle.
    """
    x_coords += [x_coords[-1]]
    y_coords += [y_coords[-1]]
    figure.add_trace(go.Scatter(x=x_coords, y=y_coords, fill="toself",
                                fillcolor=color,
                                opacity=1, mode="none"))


def add_line(figure: go.Figure,
             mode: t.Literal["horizontal", "vertical"],
             anchor_line: float,
             boundaries: list[float, float],
             color: str,
             width: float,
             dash_style: str) -> None:
    """Adds a horizontal or a veritcal line to the figure.

    Args:
        figure (go.Figure).
        mode (t.Literal["horizontal", "vertical"]): the mode of the line.
        anchor_line (float): the coordinate of the line. Is 'x' if mode
        is horizontal, 'y' if otherwise.
        boundaries (list[float, float]): the boundaries of the line.
        color (str).
        width (float).
        dash_style (str).

    Raises:
        A ValueError if 'mode' is not 'horizontal or 'vertical'.

    Example(s):
        >>> figure = go.Figure()
        >>> add_line(figure, "horizontal", 50, [10, 40], "red", 3, "dash")
        # Adds a dashed red line with a width of 3 that starts
        # at (50, 10) and ends at (50, 40).
    """
    if mode == "horizontal":
        x = boundaries
        y = [anchor_line, anchor_line]
    elif mode == "vertical":
        x = [anchor_line, anchor_line]
        y = boundaries
    else:
        raise ValueError(f"The mode should be 'horizontal' or 'vertical'",
                         f", not {mode}")
    figure.add_trace(go.Scatter(x=x,
                                y=y,
                                line=dict(color=color,
                                          dash=dash_style,
                                          width=width),
                                showlegend=False,
                                mode="lines"))


class ResultCircle:

    def __init__(self,
                 results: list[float],
                 colors: list[str],
                 color_other: str,
                 turnout: float,
                 circle_point: list[float],
                 radii: list[float],
                 turnout_text_size: float,
                 figure: go.Figure,
                 draw_instantly: bool = True) -> None:
        """Initializes an instance of ResultCircle class.

        Args:
            results (list[float]): the candidates' results.
            should not exceed 100.
            colors (list[str]): the candidates' colors. Should be of the same
            length as 'results'.
            color_other (str): the color of all non-named candidates.
            turnout (float): the turnout. Should not exceed 100.
            circle_point (list[float]): the center of the circles.
            radii (list[float]): the radii of the circles.
            Advised to contain four values.
            turnout_text_size (float).
            figure (go.Figure).
            draw_instantly (bool). Whether to draw the circles instantly,
            defaults to True.

        Raises:
            A ValueError if the sum of results exceeds 100.
            A ValueError if the length of results and colors is different.
            A ValueError if the turnout exceeds 100.
        """
        if sum(results) > 100:
            raise ValueError(f"The sum of results should not be greater "
                             f"than 100, {sum(results)} > 100")
        self.results = results
        if len(results) != len(colors):
            raise ValueError(f"The lengths of 'colors' and 'results' should "
                             f"be the same")
        self.colors = colors
        self.color_other = color_other
        if turnout > 100:
            raise ValueError(f"The turnout should not be greater than"
                             f" 100, {turnout} > 100")
        self.turnout = turnout
        self.circle_point = circle_point
        self.radii = radii
        self.turnout_text_size = turnout_text_size
        self.figure = figure
        if draw_instantly:
            self.add_circles()
            self.add_text()

    def _add_circle(self,
                    center: list[float, float],
                    radius: float,
                    start_angle: float,
                    end_angle: float,
                    n: int,
                    is_seg: bool,
                    color: str) -> None:
        """Adds a sector of a circle to the figure.

        Args:
            center (list[float, float]): the central point.
            radius (float): the radius ot the sector.
            start_angle (float): the starting angle.
            end_angle (float): the ending angle.
            n (float): uncertain, presumably the amount of points
            creating the circle. Advised to set to 50 for small-ish circles.
            is_seg (bool): whether a sector is a segment. If set to True,
            adds slices, if set to False, adds sectors.
            color (str): the color of the circle.

        Example(s):
            >>> self._add_circle([2, 2], 2, 0, 90, 50, False, "blue")
            # Adds a blue upper-right sector of a circle with center at
            # (2, 2) and a radius 0f 2.
            >>> self._add_circle([3, -2], 4, 180, 315, False, "green")
            # Adds a green left half without the top eighth part of
            a circle with center at (3, -2) and a radius of 4.
        """
        start_angle = -start_angle
        end_angle = 360 - end_angle
        start = deg_to_rad(start_angle + 90)
        end = deg_to_rad(end_angle + 90 - 360)
        t = np.linspace(start, end, n)
        x = center[0] + radius * np.cos(t)
        y = center[1] + radius * np.sin(t)
        path = f"M {x[0]},{y[0]}"
        for xc, yc in zip(x[1:], y[1:]):
            path += f" L{xc},{yc}"
        if is_seg:
            path += "Z"
        else:
            path += f" L{center[0]},{center[1]} Z"
        self.figure.add_shape(type="path",
                              path=path,
                              fillcolor=color,
                              opacity=1)

    def add_circles(self) -> None:
        """Adds concentric circles."""
        turnout_segment = self.turnout / 100 * 360
        self._add_circle(self.circle_point, self.radii[0],
                         0, turnout_segment, 50, False, self.color_other)
        self._add_circle(self.circle_point, self.radii[1],
                         0, 360, 50, False, "white")
        start_segment = 0
        end_segment = 0
        for result, color in zip(self.results, self.colors):
            end_segment += result / 100 * 360
            self._add_circle(self.circle_point, self.radii[2],
                             start_segment, end_segment, 50, False, color)
            start_segment = end_segment
        self._add_circle(self.circle_point, self.radii[2], end_segment, 360,
                         50, False, self.color_other)
        self._add_circle(self.circle_point, self.radii[3], 0, 360,
                         50, False, "white")

    def add_text(self) -> None:
        """Adds turnout text."""
        add_text(self.figure, self.circle_point,
                 f"{self.turnout}%", self.turnout_text_size)


class Legend:

    def __init__(self,
                 palettes: list[list[str]],
                 total_x_borders: list[float],
                 total_y_borders: list[float],
                 border_x_margin: float,
                 border_y_margin: float,
                 palette_x_margin: float,
                 palette_y_margin: float,
                 horizontal_text: list[str],
                 horizontal_text_positions: list[list[float]],
                 horizontal_text_size: float,
                 vertical_text: list[str],
                 vertical_text_position: list[float],
                 vertical_text_size: float,
                 figure: go.Figure,
                 draw_instantly: bool = True) -> None:
        """Initializes an instance of Legend class.

        Args:
            palettes (list[list[str]): the list of palettes, each containing
            an equal amount of colors.
            total_x_borders (list[float]): the 'x' borders of the total space
            taken up by the legend.
            total_y_borders (list[float]): same as the above, but for 'y'.
            border_x_margin (float): the 'x' margin between the legend and
            the total space.
            border_y_margin (float): same as the above, but for 'y'.
            palette_x_margin (float): the horizontal margin between the
            palette blocks.
            palette_y_margin (float): the vertical margin between the
            palette blocks.
            horizontal_text (list[str]).
            horizontal_text_positions (list[list[float]]).
            horizontal_text_size (float).
            vertical_text (str).
            vertical_text_position: the sole starting position of the
            vertical text. Additional positions are calculated automatically.
            vertical_text_size (float).
            figure (go.Figure).
            draw_instantly (bool). Whether to draw the legend instantly,
            defaults to True.

        Raises:
            A ValueError if the length of palettes is different.
        """
        if len(set([len(i) for i in palettes])) != 1:
            raise ValueError("The palettes should all be the same length")
        self.palettes = palettes
        self.total_x_borders = total_x_borders
        self.total_y_borders = total_y_borders
        self.border_x_margin = border_x_margin
        self.border_y_margin = border_y_margin
        self.palette_x_margin = palette_x_margin
        self.palette_y_margin = palette_y_margin
        self.horizontal_text = horizontal_text
        self.horizontal_text_positions = horizontal_text_positions
        self.horizontal_text_size = horizontal_text_size
        self.vertical_text = vertical_text
        self.vertical_text_position = vertical_text_position
        self.vertical_text_size = vertical_text_size
        self.figure = figure
        if draw_instantly:
            self.calculate_points()
            self.draw_palette()
            self.add_text()

    def calculate_points(self):
        """Calculates the starting coordinates of palette blocks."""
        point_x = (((self.total_x_borders[2] - self.total_x_borders[0])
                    - 2 * self.border_x_margin
                    - self.palette_x_margin * (len(self.palettes) - 1))
                   / len(self.palettes))
        point_y = (((self.total_y_borders[1] - self.total_y_borders[0])
                    - 2 * self.border_y_margin
                    - self.palette_y_margin * (len(self.palettes[0]) - 1))
                   / len(self.palettes[0]))
        self.x_coordinates = [self.total_x_borders[
                                  0] + self.border_x_margin] * 4
        self.x_coordinates[2] += point_x
        self.x_coordinates[3] += point_x
        self.y_coordinates = [self.total_y_borders[
                                  0] + self.border_y_margin] * 4
        self.y_coordinates[1] += point_y
        self.y_coordinates[2] += point_y
        self.palette_width = self.x_coordinates[2] - self.x_coordinates[0]
        self.palette_height = self.y_coordinates[1] - self.y_coordinates[0]

    def draw_palette(self):
        """Draws the palette."""
        x_coords = self.x_coordinates
        y_coords = self.y_coordinates
        for palette in self.palettes:
            for color in palette[::-1]:
                add_rectangle(self.figure, x_coords, y_coords, color)
                y_coords = [y + self.palette_height + self.palette_y_margin
                            for y in y_coords]
            y_coords = self.y_coordinates
            x_coords = [x + self.palette_width + self.palette_x_margin
                        for x in x_coords]

    def add_text(self):
        """Adds horizontal and vertical text."""
        for position, text in zip(self.horizontal_text_positions,
                                  self.horizontal_text):
            add_text(self.figure, position, text, self.horizontal_text_size)
        position = self.vertical_text_position
        for text in self.vertical_text:
            add_text(self.figure, position, text, self.vertical_text_size)
            position[1] += self.palette_height + self.palette_y_margin



class CandidateBlocks:


    def __init__(self,
                 x_borders: list[float],
                 y_borders: list[float],
                 y_margin: float,
                 colors: list[str],
                 candidate_text: list[str],
                 candidate_text_positions: list[list[float]],
                 candidate_text_size: float,
                 result_text: list[str],
                 result_text_positions: list[list[float]],
                 result_text_size: float,
                 figure: go.Figure,
                 draw_instantly: bool=True) -> None:
        """Initializes an instance of CandidateBlocks class.

        Args:
            x_borders (list[float]).
            y_borders (list[float]).
            y_margin (float): the vertical margin between the blocks.
            colors (list[str]).
            candidate_text (list[str]).
            candidate_text_positions (list[list[float]]).
            candidate_text_size: float.
            result_text (list[str]).
            result_text_positions (list[list[float]]).
            result_text_size (float).
            figure (go.Figure).
            draw_instantly (bool). Whether to draw the blocks instantly,
            defaults to True.
        """
        self.x_borders = x_borders
        self.y_borders = y_borders
        self.y_margin = y_margin
        self.colors = colors
        self.candidate_text = candidate_text
        self.candidate_text_positions = candidate_text_positions
        self.candidate_text_size = candidate_text_size
        self.result_text = result_text
        self.result_text_positions = result_text_positions
        self.result_text_size = result_text_size
        self.figure = figure
        self.block_height = self.y_borders[1]-self.y_borders[0]
        if draw_instantly:
            self.draw_blocks()
            self.add_text()


    def draw_blocks(self):
        """Draws the candidate blocks."""
        x_borders = self.x_borders
        y_borders = self.y_borders
        for color in self.colors:
            add_rectangle(self.figure, x_borders, y_borders, color)
            y_borders = [i+self.block_height+self.y_margin
                         for i in y_borders]

    def add_text(self):
        "Adds text."
        for text, position in zip(self.candidate_text,
                                  self.candidate_text_positions):
            add_text(self.figure, position, text, self.candidate_text_size)
        for text, position in zip(self.result_text,
                                  self.result_text_positions[::-1]):
            add_text(self.figure, position, text, self.result_text_size)

class ResultPlot:


    def __init__(self,
                 x_borders: list[float],
                 y_borders: list[float],
                 y_margin: float,
                 results: list[float],
                 colors: list[str],
                 neutral_color: str,
                 year_text: list[str],
                 year_text_positions: list[list[float]],
                 year_text_size: float,
                 result_text_positions: list[list[float]],
                 result_text_size: float,
                 figure: go.Figure,
                 draw_instantly: bool=True) -> None:
        """Initializes an instance of ResultPlot class.

        Args:
            x_borders (list[float]).
            y_borders (list(float]).
            y_margin (float): the vertical margin between the bars.
            results (list[float]).
            colors (list[str]). The colors of the bars.
            neutral_color (str): the background color for bars.
            year_text (list[str]): the years for the results.
            year_text_positions (list[list[float]]).
            year_text_size (float).
            result_text_positions (list[list[float]]).
            result_text_size (float).
            draw_instantly (bool). Whether to draw the plot instantly,
            defaults to True.
        """
        self.x_borders = x_borders
        self.y_borders = y_borders
        self.y_margin = y_margin
        self.results = results
        self.colors = colors
        self.neutral_color = neutral_color
        self.year_text = year_text
        self.year_text_positions = year_text_positions
        self.year_text_size = year_text_size
        self.result_text_positions = result_text_positions
        self.result_text_size = result_text_size
        self.figure = figure
        self.bar_width = x_borders[2]-x_borders[0]
        self.bar_height = y_borders[1]-y_borders[0]
        if draw_instantly:
            self.draw_bars()
            self.draw_line()
            self.add_text()


    def draw_bars(self):
        """Draws horizontal bars."""
        x_borders = self.x_borders
        y_borders = self.y_borders
        for result, color in zip(self.results, self.colors):
            add_rectangle(self.figure, x_borders, y_borders, self.neutral_color)
            new_x_borders = (x_borders[:2]+
                             [x_borders[0]+self.bar_width*result/100])
            add_rectangle(self.figure, new_x_borders, y_borders, color)
            y_borders = [i+self.bar_height+self.y_margin for i in y_borders]
            if color == self.colors[-1]:
                self.top_y = y_borders[0]-self.y_margin


    def draw_line(self):
        """Draws a line in the middle of the bars."""
        add_line(self.figure, "vertical",
                 (min(self.x_borders)+max(self.x_borders))/2,
                 [self.y_borders[0], self.top_y], COLOR_OTHER, 2, "1px")


    def add_text(self):
        """Adds text."""
        for text, position in zip(self.year_text[::-1],
                                  self.year_text_positions):
            add_text(self.figure, position, text, self.year_text_size)
        for text, position in zip(self.results,
                                  self.result_text_positions):
            add_text(self.figure, position, f"{text}%", self.result_text_size)
