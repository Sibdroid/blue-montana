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
        """Initializes the instance of ChoroplethMap class.

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
        for i, (left, right) in enumerate(zip(THRESH_MARGIN, THRESH_MARGIN[1:])):
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


class GraphData:


    def __init__(self,
                 palette1: list[str],
                 palette2: list[str],
                 result1: float,
                 result2: float,
                 rectangle_x_coords: list[float],
                 rectangle_y_coords: list[float],
                 rectangle_x_margin: float,
                 rectangle_y_margin: float,
                 width: float,
                 height: float,
                 name: str) -> None:
        self.palette1 = palette1
        self.palette2 = palette2
        self.result1 = result1
        self.result2 = result2
        self.rectangle_x_coords = rectangle_x_coords
        self.rectangle_y_coords = rectangle_y_coords
        self.rectangle_x_margin = rectangle_x_margin
        self.rectangle_y_margin = rectangle_y_margin
        self.width = width
        self.height = height
        self.rectangle_length = (self.rectangle_x_coords[2]
                                 -self.rectangle_x_coords[0])
        self.rectangle_height = (self.rectangle_y_coords[2]
                                 -self.rectangle_y_coords[0])
        self.name = name
        self.create_figure()
        self.add_rectangles()
        self.add_circle()
        self.save()


    def create_figure(self):
        self.figure = go.Figure()
        self.figure.update_layout(template='simple_white',
                                  xaxis_range=[0, self.width],
                                  yaxis_range=[0, self.height],
                                  margin=dict(l=0, r=0, t=0, b=0),
                                  showlegend=False)
        self.figure.update_xaxes(visible=False, showticklabels=False)
        self.figure.update_yaxes(visible=False, showticklabels=False,
                                 scaleanchor="x", scaleratio=1)


    def add_rectangle(self,
                      x_coords: list[float],
                      y_coords: list[float],
                      color: str) -> None:
        self.figure.add_trace(go.Scatter(x=x_coords, y=y_coords, fill="toself",
                                         fillcolor=color,
                                         opacity=1, mode="none"))

    def add_rectangles(self):
        assert len(self.palette1) == len(self.palette2)
        x_coords = self.rectangle_x_coords
        other_x_coords = [i+self.rectangle_length+self.rectangle_x_margin
                          for i in x_coords]
        y_coords = self.rectangle_y_coords
        for color1, color2 in zip(self.palette1[::-1], self.palette2[::-1]):
            self.add_rectangle(x_coords, y_coords, color1)
            self.add_rectangle(other_x_coords, y_coords, color2)
            y_coords = [i+self.rectangle_height+self.rectangle_y_margin
                        for i in y_coords]

    def get_circle_path(self,
                        center: list[float, float],
                        radius: float,
                        start_angle: float,
                        end_angle: float,
                        n: float,
                        seg: bool) -> str:
        start = deg_to_rad(start_angle)
        end = deg_to_rad(end_angle)
        t = np.linspace(start, end, n)
        x = center[0]+radius*np.cos(t)
        y = center[1]+radius*np.sin(t)
        path = f"M {x[0]},{y[0]}"
        for xc, yc in zip(x[1:], y[1:]):
            path += f" L{xc},{yc}"
        if seg:
            return path + "Z"
        return path + f" L{center[0]},{center[1]} Z"


    def add_circle(self):
        path = self.get_circle_path([75, 425], 60, 0, 90, 50, False)
        self.figure.add_shape(type="path",
                              path=path,
                              fillcolor="LightPink",
                              line_color="LightPink")

    def save(self):
        self.figure.write_image(self.name, width=self.width,
                                height=self.height)



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
    data = GraphData(COLORS_D_PRES, COLORS_R_PRES, 60, 40,
                     [50, 50, 95, 95, 50], [105, 130, 130, 105, 105],
                     5, 10, 150, 500, "test-new-circle.svg")
                           

if __name__ == "__main__":
    main()



