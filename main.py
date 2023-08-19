import typing as t
import plotly.graph_objects as go
import json
from decimal import Decimal
from drawing import *
from tools import *
COLORS_D_PRES = ["#AFE9AF", "#73D873", "#42CA42",
                 "#30A630", "#217821", "#165016"]
COLORS_R_PRES = ["#FEE391", "#FED463", "#FE9929",
                 "#EC7014", "#CC4C02", "#8C2D04"]
COLOR_OTHER = "#696969"
THRESH_MARGIN = [40, 50, 60, 70, 80, 90, 100]
WHITE = "#FFFFFF"

class ChoroplethMap:

    def __init__(self,
                 data: str,
                 geojson: str,
                 projection: str,
                 colors_up: list[str],
                 colors_down: list[str],
                 thresh_margins: list[float],
                 name: str,
                 boundaries: str,
                 width: float,
                 height: float,
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
            thresh_margins (list[float]): the thresholds used to link
            values to colors.
            name (str): the name of the image. '<name>.svg' strongly advised.
            boundaries (str): the boundaries of the image. Should consist of
            four integers divided by spaces: for example, '130 130 440 240'.
            draw_instantly (bool): whether to draw the map when initialized.
            Defaults to True.
        """

        self.data = read_data(data, {"id": str})
        with open(geojson) as file:
            self.geojson = json.load(file)
        self.projection = projection
        self.colors_up = colors_up
        self.colors_down = colors_down
        self.thresh_margins = thresh_margins
        self.name = name
        self.boundaries = boundaries
        self.width = width
        self.height = height
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
            The color from self.colors_up or self.colors_down.
        """
        if value > 0:
            colors = self.colors_up
        else:
            colors = self.colors_down
        for i, (left, right) in enumerate(zip(self.thresh_margins,
                                              self.thresh_margins[1:])):
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
        fig = go.Figure()
        fig.add_trace(go.Choropleth(
            geojson=self.geojson,
            locations=self.data["id"],
            z=self.data["result"],
            colorscale=self.colorscale,
            showscale=False,
            name="map"))
        """Temporary stuff, tread carefully"""
        data = pd.read_excel("cities-test.xlsx", header=0,
                             dtype={"lat": float, "lon": float})
        fig.add_trace(go.Scattergeo(
            lon=data["lon"],
            lat=data["lat"],
            marker=dict(color="rgba(0, 0, 0, 0)",
                        size=4,
                        opacity=1,
                        line=dict(
                            width=0.5,
                            color="black")
                        ),
            text=data["name"],
            textfont=dict(size=5,
                          family="Roboto"),
            textposition="bottom center",
            mode="markers+text",
            name="cities"
        ))
        """Temporary stuff ends"""
        fig.update_geos(fitbounds="locations",
                        visible=False,
                        projection_type=self.projection)
        fig.update_traces(marker_line_color=WHITE,
                          marker_line_width=0.25,
                          selector = {"name": "map"})
        fig.layout.paper_bgcolor = WHITE
        fig.layout.plot_bgcolor = WHITE
        return fig


    def draw_standard_map(self) -> None:
        """Draws a standard map and updates its boundaries."""
        standard_map = self.draw_map().write_image(self.name,
                                                   width=self.width,
                                                   height=self.height)
        edit_viewbox(self.name, self.boundaries)

def draw_legend(candidates: list[str],
                results: list[float],
                past_results: list[float],
                turnout: float,
                palettes: list[list[str]],
                parties: list[str],
                bar_colors: list[str],
                bar_years: list[str],
                name: str) -> None:
    """Draws a standard legend.

    Args:
        candidates (list[str]): the names of the candidates.
        results (list[float]).
        past_results (list[float]). The results of previous two elections.
        palettes (list[list[str]]).
        parties (list[str]).
        bar_colors (list[str]).
        bar_years (list[str]).
        name (str). The name of the legend.
    """
    figure = go.Figure()
    figure.update_layout(template='simple_white',
                         xaxis_range=[0, 300],
                         yaxis_range=[0, 500],
                         margin=dict(l=0, r=0, t=0, b=0),
                         showlegend=False)
    figure.update_xaxes(visible=False, showticklabels=False)
    figure.update_yaxes(visible=False, showticklabels=False,
                        scaleanchor="x", scaleratio=1)
    circles = ResultCircle(results=results,
                           colors=[palettes[0][1], palettes[1][1]],
                           color_other=COLOR_OTHER,
                           turnout=turnout,
                           circle_point=[80, 309],
                           radii=[66, 63, 60, 30],
                           turnout_text_size=15.5,
                           figure=figure)
    legend = Legend(palettes=palettes,
                    total_x_borders=[190, 190, 295, 295],
                    total_y_borders=[174, 384, 384, 174],
                    border_x_margin=5,
                    border_y_margin=5,
                    palette_x_margin=5,
                    palette_y_margin=10,
                    horizontal_text=parties,
                    horizontal_text_positions=[[217.5, 164], [265, 164]],
                    horizontal_text_size=13,
                    vertical_text=[f">{i}%" for i in range(40, 100, 10)][::-1],
                    vertical_text_position=[171, 192],
                    vertical_text_size=13.5,
                    figure=figure)
    blocks = CandidateBlocks(x_borders=[10, 10, 290, 290],
                             y_borders=[389, 439, 439, 389],
                             y_margin=5,
                             colors=[palettes[1][1], palettes[0][1]],
                             candidate_text=candidates,
                             candidate_text_positions=[[108, 469], [97, 414]],
                             candidate_text_size=20,
                             result_text=[f"{i}%" for i in results],
                             result_text_positions=[[250, 414], [250, 469]],
                             result_text_size=20,
                             figure=figure)
    bars = ResultPlot(x_borders=[10, 10, 240, 240],
                      y_borders=[30, 60, 60, 30],
                      y_margin=10,
                      results=([max(results)]+past_results)[::-1],
                      colors=bar_colors,
                      neutral_color="#EEEEEE",
                      year_text=bar_years,
                      year_text_positions=[[265, 46], [265, 86], [265, 126]],
                      year_text_size=14,
                      result_text_positions=[[35, 46], [35, 86], [35, 126]],
                      result_text_size=14,
                      figure=figure)
    figure.write_image(name, width=300, height=500)

def main() -> None:
    pres_map = ChoroplethMap("north-virginia-2024.xlsx", "counties.geojson",
                             "mercator", COLORS_D_PRES, COLORS_R_PRES,
                             THRESH_MARGIN,
                             "map.svg",
                             "350 245 300 30", 1000, 500)
    svg_to_png("map.svg", "map.png")
    print("Map complete")
    draw_legend(["Sanders/Manchin (P)", "Christie/Ayotte (U)"],
                [59.5, 38.3], [54.2, 49.7], 77.4,
                [COLORS_D_PRES, COLORS_R_PRES],
                ["P", "U"], [COLORS_R_PRES[1], COLORS_D_PRES[1],
                COLORS_D_PRES[1]], ["2016", "2012", "2008"],
                "legend.png")
    print("Legend complete")
    combine_images("map.png", "legend.png",
                   "north-virginia-test-0.png")


if __name__ == "__main__":
    main()
