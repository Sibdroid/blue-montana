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
    return degrees*pi/180


class ChoroplethMap:


    def __init__(self,
                 data: str,
                 geojson: str,
                 projection: str,
                 colors_up: list[str],
                 colors_down: list[str],
                 name: str,
                 boundaries: str,
                 draw_instantly: bool=True) -> None:
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
                 draw_instantly: bool=True) -> None:
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


    def _add_circle(self,
                    center: list[float, float],
                    radius: float,
                    start_angle: float,
                    end_angle: float,
                    n: float,
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
        end_angle = 360-end_angle
        start = deg_to_rad(start_angle+90)
        end = deg_to_rad(end_angle+90-360)
        t = np.linspace(start, end, n)
        x = center[0]+radius*np.cos(t)
        y = center[1]+radius*np.sin(t)
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
        turnout_segment = self.turnout/100*360
        self._add_circle(self.circle_point, self.radii[0],
                         0, turnout_segment, 50, False, self.color_other)
        self._add_circle(self.circle_point, self.radii[1],
                         0, 360, 50, False, "white")
        start_segment = 0
        end_segment = 0
        for result, color in zip(self.results, self.colors):
            end_segment += result/100*360
            self._add_circle(self.circle_point, self.radii[2],
                             start_segment, end_segment, 50, False, color)
            start_segment = end_segment
        self._add_circle(self.circle_point, self.radii[2], end_segment, 360,
                         50, False, self.color_other)
        self._add_circle(self.circle_point, self.radii[3], 0, 360,
                         50, False, "white")



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
    circles = ResultCircle(results=[45.4, 39.4, 9.1],
                           colors=[COLORS_D_DOWN[1], COLORS_R_DOWN[1],
                                   COLORS_I_DOWN[1]],
                           color_other=COLOR_OTHER,
                           turnout=55.0,
                           circle_point=[80, 305],
                           radii=[66, 63, 60, 30],
                           turnout_text_size=20,
                           figure=figure)
    figure.write_image("test-from-scratch.svg", width=300, height=500)

if __name__ == "__main__":
    main()



