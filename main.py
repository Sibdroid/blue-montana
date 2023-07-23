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


class GraphData:


    def __init__(self,
                 palette1: list[str],
                 palette2: list[str],
                 result1: float,
                 result2: float,
                 turnout: float,
                 major_rectangle_x_coords: list[float],
                 major_rectangle_y_coords: list[float],
                 major_rectangle_y_margin: float,
                 rectangle_x_coords: list[float],
                 rectangle_y_coords: list[float],
                 rectangle_x_margin: float,
                 rectangle_y_margin: float,
                 circle_point: list[float],
                 circle_radii: list[float],
                 horizontal_text: list[str],
                 horizontal_text_point: list[float],
                 horizontal_text_size: float,
                 vertical_text: list[str],
                 vertical_text_point: list[float],
                 vertical_text_size: float,
                 width: float,
                 height: float,
                 name: str,
                 draw_instantly: bool=True) -> None:
        """Initializes an instance of GraphData class.

        Args:
            palette1 (list[str]): the first set of colors.
            palette2 (list[str]): the second set of colors.
            result1 (float): the result of the first candidate.
            result2 (float): the result of the second candidate.
            turnout (float): the turnout.
            major_rectangle_x_coords (list[float): the 'x' coordinates
            of the bottom major rectangle.
            major_rectangle_x_coords (list[float): the 'y' coordinates
            of the bottom major rectangle.
            major_rectangle_y_margin (float): the vertical margin
            between the major rectangles.
            rectangle_x_coords (list[float]): the 'x' coordinates
            of the bottom-left rectangle.
            rectangle_y_coords (list[float]): the 'y' coordinates
            of the bottom-left rectangle.
            rectangle_y_margin (float): the vertical margin between
            the rectangles.
            circle_point (list[float]): the coordinates of the center
            of the circle.
            circle_radii (list[float]): a list of radii for the circle.
            Four radii are required:
                1) The one for the turnout.
                2) The one for the border between the turnout and the results.
                3) The one for the results.
                4) The one for the hole in the results.
            horizontal_text (list[str]): the text values of the
            horizontal text entries.
            horizontal_text_point (list[float]): the coordinates of the
            bottom-left horizontal text entry.
            horizontal_text_size (float): the size of the horizontal
            text entries.
            vertical_text (list[str]): the text values of the
            vertical text entries.
            vertical_text_point (list[float]): the coordinates of the
            left vertical text entry.
            vertical_text_size (float): the size of the vertical
            text entries.
            width (float): the width of the image.
            height (float): the height of the image.
            name (str): the name of the image.
            Strongly advised to be <name>.svg.
            draw_instantly (bool): whether to draw the map when initialized.
            Defaults to True.

        Raises:
            A ValueError if palettes have different lengths.
            A ValueError if the sum of results is greater than 100."""
        if len(palette1) != len(palette2):
            raise ValueError("The palettes should have the same length")
        self.palette1 = palette1
        self.palette2 = palette2
        if result1+result2 > 100:
            raise ValueError("The sum of results cannot not be more than 100")
        self.result1 = result1
        self.result2 = result2
        if turnout > 100:
            raise ValueError("The turnout cannot be more than 100")
        self.turnout = turnout
        self.major_rectangle_x_coords = major_rectangle_x_coords
        self.major_rectangle_y_coords = major_rectangle_y_coords
        self.major_rectangle_x_coords += [self.major_rectangle_x_coords[-1]]
        self.major_rectangle_y_coords += [self.major_rectangle_y_coords[-1]]
        self.major_rectangle_y_margin = major_rectangle_y_margin
        self.rectangle_x_coords = rectangle_x_coords
        self.rectangle_y_coords = rectangle_y_coords
        self.rectangle_x_coords += [self.rectangle_x_coords[-1]]
        self.rectangle_y_coords += [self.rectangle_y_coords[-1]]
        self.rectangle_x_margin = rectangle_x_margin
        self.rectangle_y_margin = rectangle_y_margin
        self.circle_point = circle_point
        if len(circle_radii) != 4:
            raise ValueError("circle_radii should contain precisely 4 values")
        self.circle_radii = circle_radii
        self.horizontal_text_point = horizontal_text_point
        self.horizontal_text = horizontal_text
        self.horizontal_text_size = horizontal_text_size
        self.vertical_text_point = vertical_text_point
        self.vertical_text = vertical_text
        self.vertical_text_size = vertical_text_size
        self.width = width
        self.height = height
        self.name = name
        self.draw_instantly = draw_instantly
        self.major_rectangle_width = (self.major_rectangle_x_coords[2]
                                      -self.major_rectangle_x_coords[0])
        self.major_rectangle_height = (self.major_rectangle_y_coords[2]
                                       -self.major_rectangle_y_coords[0])
        self.rectangle_width = (self.rectangle_x_coords[2]
                                -self.rectangle_x_coords[0])
        self.rectangle_height = (self.rectangle_y_coords[2]
                                 -self.rectangle_y_coords[0])
        if self.draw_instantly:
            self.create_figure()
            self.add_major_rectangle()
            self.add_rectangles()
            self.add_circle()
            self.add_text()
            self.save()


    def create_figure(self):
        """Creates an empty figure with white background and hidden axis."""
        self.figure = go.Figure()
        self.figure.update_layout(template='simple_white',
                                  xaxis_range=[0, self.width],
                                  yaxis_range=[0, self.height],
                                  margin=dict(l=0, r=0, t=0, b=0),
                                  showlegend=False)
        self.figure.update_xaxes(visible=False, showticklabels=False)
        self.figure.update_yaxes(visible=False, showticklabels=False,
                                 scaleanchor="x", scaleratio=1)


    def _add_rectangle(self,
                       x_coords: list[float],
                       y_coords: list[float],
                       color: str) -> None:
         """Adds a rectangle to the figure.

         Args:
             x_coords (list[float]): the 'x' coordinates of a rectangle.
             y_coords (list[float): the 'y' coordinates of a rectangle.
             color (str): the color.

         Example(s):
             >>> self._add_rectangle([2, 2, 6, 6], [1, 3, 3, 1], "red")
             # Adds a red rectangle with the following points:
             # (2, 1), (2, 3), (6, 3), (6, 1).
         """
         self.figure.add_trace(go.Scatter(x=x_coords, y=y_coords, fill="toself",
                                          fillcolor=color,
                                          opacity=1, mode="none"))

    def add_major_rectangle(self):
        """Adds two major rectangles to the figure, one for each
        candidate."""
        x_coords = self.major_rectangle_x_coords
        y_coords = self.major_rectangle_y_coords
        self._add_rectangle(x_coords, y_coords, self.palette2[1])
        y_coords = [i+self.major_rectangle_height+self.major_rectangle_y_margin
                    for i in y_coords]
        self._add_rectangle(x_coords, y_coords, self.palette1[1])


    def add_rectangles(self) -> None:
        """Adds an N*2 set of rectangles to the figure,
        where N is the amount of colors given in palette1 and palette2."""
        x_coords = self.rectangle_x_coords
        other_x_coords = [i+self.rectangle_width+self.rectangle_x_margin
                          for i in x_coords]
        y_coords = self.rectangle_y_coords
        for color1, color2 in zip(self.palette1[::-1], self.palette2[::-1]):
            self._add_rectangle(x_coords, y_coords, color1)
            self._add_rectangle(other_x_coords, y_coords, color2)
            y_coords = [i+self.rectangle_height+self.rectangle_y_margin
                        for i in y_coords]

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


    def add_circle(self) -> None:
        """Adds the main circle with results to the figure.
        The circle consists of three partS: the sector for the
        result1, the sector for the result2, and the sector for
        other results, calculated as 100-result1-result2.
        If result1 and result2 combine for 100, there is no third sector.
        """
        segment0 = self.turnout/100*360
        segment1 = self.result1/100*360
        segment2 = self.result2/100*360+segment1
        self._add_circle(self.circle_point, self.circle_radii[0],
                         0, segment0, 50, False, COLOR_OTHER)
        self._add_circle(self.circle_point, self.circle_radii[1],
                         0, 360, 50, False, "white")
        self._add_circle(self.circle_point, self.circle_radii[2],
                         0, segment1, 50, False, self.palette1[1])
        self._add_circle(self.circle_point, self.circle_radii[2],
                         segment1, segment2, 50, False, self.palette2[1])
        self._add_circle(self.circle_point, self.circle_radii[2],
                         segment2, 360, 50, False, COLOR_OTHER)
        self._add_circle(self.circle_point, self.circle_radii[3],
                         0, 360, 50, False, "white")


    def _add_text(self,
                  point: list[float, float],
                  text: str,
                  size: float) -> None:
        self.figure.add_annotation(x=point[0], y=point[1], text=text,
                                   showarrow=False, ax=0, ay=0,
                                   font=dict(size=size))

    def add_text(self):
        point = self.horizontal_text_point
        for text in self.horizontal_text:
            self._add_text(point, text, self.horizontal_text_size)
            point[1] += self.rectangle_height+self.rectangle_y_margin
        point = self.vertical_text_point
        for text in self.vertical_text:
            self._add_text(point, text, self.vertical_text_size)
            point[0] += self.rectangle_width


    def save(self) -> None:
        """Saves the figure."""
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
    text = [f">{i}%" for i in range(40, 100, 10)][::-1]
    data = GraphData(palette1=COLORS_R_PRES,
                     palette2=COLORS_D_PRES,
                     result1=56.92,
                     result2=40.55,
                     turnout=73.10,
                     major_rectangle_x_coords=[10, 10, 290, 290],
                     major_rectangle_y_coords=[385, 435, 435, 385],
                     major_rectangle_y_margin=5,
                     rectangle_x_coords=[195, 195, 240, 240],
                     rectangle_y_coords=[170, 195, 195, 170],
                     rectangle_x_margin=5,
                     rectangle_y_margin=10,
                     circle_point=[80, 300],
                     circle_radii=[66, 63, 60, 30],
                     horizontal_text=text,
                     horizontal_text_point=[169, 183.5],
                     horizontal_text_size=13,
                     vertical_text=["D", "R"],
                     vertical_text_point=[0, 0],
                     vertical_text_size=1,
                     width=300,
                     height=500,
                     name="test-new-circle-big.svg")
                           

if __name__ == "__main__":
    main()



