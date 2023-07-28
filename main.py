import typing as t
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
from decimal import Decimal
from math import pi

COLORS_D_PRES = ["#B9D7FF", "#86B6F2", "#4389E3",
                 "#1666CB", "#0645B4", "#002B84"]
COLORS_R_PRES = ["#F2B3BE", "#E27F90", "#CC2F4A",
                 "#D40000", "#AA0000", "#800000"]
COLORS_D_DOWN = ["#A5B0FF", "#7996E2", "#6674DE",
                 "#584CDE", "#3933E5", "#0D0596"]
COLORS_I_DOWN = ["#D9D9D9", "#BDBDBD", "#969696",
                 "#737373", "#555555", "#555555"]
COLORS_R_DOWN = ["#FFB2B2", "#E27F7F", "#D75D5D",
                 "#D72F30", "#C21B18", "#A80000"]
COLOR_OTHER = "#696969"
THRESH_MARGIN = [40, 50, 60, 70, 80, 90, 100]
POINT = t.Tuple[float, float]
WHITE = "#FFFFFF"


def line_between_points(point1: POINT,
                        point2: POINT) -> t.Tuple[Decimal, Decimal]:
    """Determines the slope and the intercept of a line between two points.

    Args:
        point1 (POINT).
        point2 (POINT).

    Returns:
        A tuple of the slope and the intercept, represented as Decimals.

    Examples:
        line_between_points((1, 0), (2, 3))
        >>> (Decimal('3'), Decimal('-3'))

        line_between_points((3.5, 2.5), (-5.5, 7.5))
        >>> (Decimal('-0.5...56'),
             Decimal('4.4...'))

    """
    m = Decimal(point2[1] - point1[1]) / Decimal(point2[0] - point1[0])
    c = (Decimal(point2[1]) - (m * Decimal(point2[0])))
    return m, c


def edit_viewbox(path: str,
                 new_viewbox: str) -> None:
    """Edits the viewbox of an .svg file.

    Args:
        path (str): the path to the .svg file.
        new_viewbox (str): the viewbox to replace the old one.

    Raises:
        A ValueError exception in case the file is not .svg. 
    """
    name, extension = os.path.splitext(path)
    if extension != ".svg":
        raise ValueError(f"The file has to be an .svg, not a .{extension}")
    with open(path) as file:
        data = file.read()
        viewbox = [i for i in data.split('"')[1::2]
                   if i.count(" ") == 3][0]
        data = data.replace(viewbox, new_viewbox, 1)
    with open(path, "w") as file:
        file.write(data)


def read_data(path: str,
              data_dtype: dict[str, type]) -> pd.DataFrame:
    """Reads the data from an .xlsx or a .csv file.

    Args:
        path (str): the path to the file.
        data_dtype (dict[str, type]): the dtype for the data.

    Returns:
        A pd.DataFrame.

    Raises:
        A ValueError in case the file is neither an .xlsx nor an .svg.
    """
    name, extension = os.path.splitext(path)
    if extension == ".xlsx":
        df = pd.read_excel(path, header=0,
                           index_col=0, dtype=data_dtype)
    elif extension == ".csv":
        df = pd.read_csv(path, header=0,
                         index_col=0, dtype=data_dtype)
    else:
        error = f"The file has to be an .xlsx or a .csv, not a .{extension}"
        raise ValueError(error)
    return df


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


class ChoroplethMap:

    def __init__(self,
                 data: str,
                 geojson: str,
                 projection: str,
                 colors_up: list[str],
                 colors_down: list[str],
                 name: str,
                 boundaries: str,
                 draw_instantly: bool = True) -> None:
        """Initializes an instance of ChoroplethMap class.

        Args:
            data (str): the path to the data.
            Data consists of the following columns:
                county (str): optional.
                result (float, from -100 to 100): required.
                id (str, five digits): required.
            geojson (str): the path to the file with GEOJSON data.
            projection (str): the projection of the map.
            'transverse mercator' advised.
            colors_up (list[str]): the colors used for positive values.
            colors_down (list[str]): the colors used for negative values.
            name (str): the name of the image. '<name>.svg' strongly advised.
            boundaries (str): the boundaries of the image. Should consist of
            four integers divided by spaces: for example, '130 130 440 240'.
            draw_instantly (bool): whether to draw the map when initialized.
            Defaults to True."""

        self.data = read_data(data, {"id": str})
        with open(geojson) as file:
            self.geojson = json.load(file)
        self.projection = projection
        self.colors_up = colors_up
        self.colors_down = colors_down
        self.name = name
        self.boundaries = boundaries
        self.add_ids()
        self.add_colors()
        self.add_colorscale()
        if draw_instantly:
            self.draw_standard_map()

    def add_ids(self):
        """Adds plotly-readable ids to the features of the GEOJSON."""
        features = self.geojson["features"]
        for feature in features:
            feature["id"] = feature["properties"]["GEOID"]
        self.geojson["features"] = features

    def get_color(self,
                  value: float) -> str:
        """Transforms the value into the corresponding color.

        Args:
            value (float): the value to be transformed.

        Returns:
            The color from self.colors_up or self.colors_down."""
        if value > 0:
            colors = self.colors_up
        else:
            colors = self.colors_down
        for i, (left, right) in enumerate(zip(THRESH_MARGIN,
                                              THRESH_MARGIN[1:])):
            if left < abs(value) <= right:
                return colors[i]

    def add_colors(self) -> None:
        """Adds colors to the data according to the result."""
        color = self.data["result"].apply(lambda x: self.get_color(x))
        self.data["color"] = color

    def add_colorscale(self) -> None:
        """Adds a colorscale used to plot the data."""
        m, c = line_between_points((min(self.data["result"]), 0),
                                   (max(self.data["result"]), 1))
        values = []
        colors = self.data["color"]
        for color in set(colors):
            min_value = min(self.data[self.data["color"] == color]["result"])
            max_value = max(self.data[self.data["color"] == color]["result"])
            min_value = float(Decimal(min_value) * m + c)
            max_value = float(Decimal(max_value) * m + c)
            if min_value < 0:
                min_value = 0
            values += [[min_value, color],
                       [max_value, color]]
        values = sorted(values, key=lambda x: x[0])
        values[0][0] = 0
        self.colorscale = values

    def draw_map(self) -> go.Figure():
        """Draws a choropleth map of the data based on the GEOJSON."""
        fig = go.Figure(data=go.Choropleth(
            geojson=self.geojson,
            locations=self.data["id"],
            z=self.data["result"],
            colorscale=self.colorscale,
            showscale=False))
        fig.update_geos(fitbounds="locations",
                        visible=False,
                        projection_type=self.projection)
        fig.update_traces(marker_line_color=WHITE,
                          marker_line_width=0.5)
        fig.layout.paper_bgcolor = WHITE
        fig.layout.plot_bgcolor = WHITE
        return fig

    def draw_standard_map(self) -> None:
        """Draws a standard map and updates its boundaries."""
        standard_map = self.draw_map().write_image(self.name)
        edit_viewbox(self.name, self.boundaries)


def add_text(figure: go.Figure,
             point: list[float, float],
             text: str,
             size: float,
             color: str = "black") -> None:
    figure.add_annotation(x=point[0], y=point[1], text=text,
                          showarrow=False, ax=0, ay=0,
                          font=dict(size=size, color=color))


def add_rectangle(figure: go.Figure,
                  x_coords: list[float],
                  y_coords: list[float],
                  color: str) -> None:
    x_coords += [x_coords[-1]]
    y_coords += [y_coords[-1]]
    figure.add_trace(go.Scatter(x=x_coords, y=y_coords, fill="toself",
                                fillcolor=color,
                                opacity=1, mode="none"))


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
        self.results = results
        self.colors = colors
        self.color_other = color_other
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
        x_borders = self.x_borders
        y_borders = self.y_borders
        for color in self.colors:
            add_rectangle(self.figure, x_borders, y_borders, color)
            y_borders = [i+self.block_height+self.y_margin
                         for i in y_borders]

    def add_text(self):
        for text, position in zip(self.candidate_text,
                                  self.candidate_text_positions):
            add_text(self.figure, position, text, self.candidate_text_size)
        for text, position in zip(self.result_text,
                                  self.result_text_positions[::-1]):
            add_text(self.figure, position, text, self.result_text_size)


def main() -> None:
    pres_map = ChoroplethMap("data-montana-pres.xlsx", "counties.geojson",
                             "transverse mercator",
                             COLORS_D_PRES, COLORS_R_PRES,
                             "montana-presidential.svg",
                             "130 130 440 240")
    sen_map = ChoroplethMap("data-montana-sen.xlsx", "counties.geojson",
                            "transverse mercator",
                            COLORS_I_DOWN, COLORS_R_DOWN,
                            "montana-senate.svg",
                            "130 130 440 240")


def main() -> None:
    figure = go.Figure()
    figure.update_layout(template='simple_white',
                         xaxis_range=[0, 300],
                         yaxis_range=[0, 500],
                         margin=dict(l=0, r=0, t=0, b=0),
                         showlegend=False)
    figure.update_xaxes(visible=False, showticklabels=False)
    figure.update_yaxes(visible=False, showticklabels=False,
                        scaleanchor="x", scaleratio=1)
    circles = ResultCircle(results=[56.92, 40.55],
                           colors=[COLORS_R_PRES[1], COLORS_D_PRES[1]],
                           color_other=COLOR_OTHER,
                           turnout=73.1,
                           circle_point=[80, 305],
                           radii=[66, 63, 60, 30],
                           turnout_text_size=15,
                           figure=figure)
    legend = Legend(palettes=[COLORS_R_PRES, COLORS_D_PRES],
                    total_x_borders=[190, 190, 295, 295],
                    total_y_borders=[170, 380, 380, 170],
                    border_x_margin=5,
                    border_y_margin=5,
                    palette_x_margin=5,
                    palette_y_margin=10,
                    horizontal_text=["R", "D"],
                    horizontal_text_positions=[[217.5, 160], [265, 160]],
                    horizontal_text_size=13,
                    vertical_text=[f">{i}%" for i in range(40, 100, 10)][::-1],
                    vertical_text_position=[169, 188.5],
                    vertical_text_size=13,
                    figure=figure)
    blocks = CandidateBlocks(x_borders=[10, 10, 290, 290],
                             y_borders=[385, 435, 435, 385],
                             y_margin=5,
                             colors=[COLORS_D_PRES[1], COLORS_R_PRES[1]],
                             candidate_text=["Trump/Pence (R)",
                                             "Biden/Harris (D)"],
                             candidate_text_positions=[[100, 465], [98, 410]],
                             candidate_text_size=20,
                             result_text=["56.9%", "40.5%"],
                             result_text_positions=[[250, 410], [250, 465]],
                             result_text_size=20,
                             figure=figure)
    figure.write_image("test-from-scratch.svg", width=300, height=500)


if __name__ == "__main__":
    main()
