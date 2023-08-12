import typing as t
import pandas as pd
import os
from decimal import Decimal
from wand.image import Image
from PIL import Image as Pillow_Image
POINT = t.Tuple[float, float]
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


def svg_to_png(path: str,
               new_path: str) -> None:
    with Image(filename=path) as img:
        img.format = "png"
        img.save(filename=new_path)


def combine_images(image1_path: str,
                   image2_path: str,
                   name: str) -> None:
    images = [Pillow_Image.open(i) for i in [image1_path, image2_path]]
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)
    new_image = Pillow_Image.new("RGB", (total_width, max_height))
    x_offset = 0
    for image in images:
        new_image.paste(image, (x_offset, 0))
        x_offset += image.size[0]
    new_image.save(name)