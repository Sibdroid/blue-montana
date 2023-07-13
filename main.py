import typing as t
import plotly.graph_objects as go
import pandas as pd
import json
import sys
import time
from decimal import Decimal

COLORS_D = ["#B9D7FF", "#86B6F2", "#4389E3", "#1666CB", "#0645B4", "#002B84"]
COLORS_R = ["#F2B3BE", "#E27F90", "#CC2F4A", "#D40000", "#AA0000", "#800000"]
THRESH_MARGIN = [40, 50, 60, 70, 80, 90, 100]
POINT = t.Tuple[float, float]
WHITE = "#FFFFFF"


def get_color(value: float) -> str:
    """Transforms the value into the corresponding color.

    Args:
        value (float): the value to be transformed.

    Returns:
        The color from 'colors' argument, correlating to the value.

    Examples:
    """
    if value > 0:
        colors = COLORS_D
    else:
        colors = COLORS_R
    for i, (left, right) in enumerate(zip(THRESH_MARGIN, THRESH_MARGIN[1:])):
        if left < abs(value) <= right:
            return colors[i]


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
        >>> (Decimal('-0.5555555555555555555555555556'),
             Decimal('4.444444444444444444444444444'))

    """
    m = Decimal(point2[1] - point1[1]) / Decimal(point2[0] - point1[0])
    c = (Decimal(point2[1]) - (m * Decimal(point2[0])))
    return m, c


class ElectoralMap:

    def __init__(self,
                 data: pd.DataFrame,
                 geojson: str,
                 projection: str) -> None:
        self.data = data
        with open(geojson) as file:
            self.geojson = json.load(file)
        self.projection = projection
        self.add_ids()
        self.add_colors()
        self.add_colorscale()

    def add_ids(self):
        features = self.geojson["features"]
        for feature in features:
            feature["id"] = feature["properties"]["GEOID"]
        self.geojson["features"] = features

    def add_colors(self) -> None:
        self.data["color"] = self.data["result"].apply(lambda x: get_color(x))

    def add_colorscale(self) -> None:
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
                          marker_line_width=1)
        fig.layout.paper_bgcolor = WHITE
        fig.layout.plot_bgcolor = WHITE
        return fig


def main() -> None:
    data = pd.read_excel("data-montana-pres.xlsx", header=0,
                         index_col=0, dtype={"id": str})
    projection = "transverse mercator"
    my_map = ElectoralMap(data, "counties.geojson", projection)
    my_map.draw_map().write_image(f"montana-{projection}.svg")


if __name__ == "__main__":
    main()



