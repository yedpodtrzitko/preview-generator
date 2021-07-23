# -*- coding: utf-8 -*-
import os
from shutil import which
from subprocess import DEVNULL
from subprocess import STDOUT
from subprocess import check_call
from subprocess import check_output
import tempfile
import typing

from preview_generator.exception import BuilderDependencyNotFound
from preview_generator.exception import IntermediateFileBuildingFailed
from preview_generator.preview.builder.image__pillow import ImagePreviewBuilderPillow  # nopep8
from preview_generator.preview.generic_preview import ImagePreviewBuilder
from preview_generator.utils import ImgDims
from preview_generator.utils import executable_is_available

INKSCAPE_EXECUTABLE = "inkscape"
DEFAULT_INKSCAPE_VERSION = "1.0"

INKSCAPE_092_SVG_TO_PNG_OPTIONS = ["--export-area-drawing", "-e"]
INKSCAPE_100_SVG_TO_PNG_OPTIONS = ["--export-area-drawing", "--export-type=png", "-o"]


def get_inkscape_version() -> float:
    return float(os.environ.get("INKSCAPE_VERSION", default=DEFAULT_INKSCAPE_VERSION))


def get_inkscape_svg_to_png_options(inkscape_version: float) -> typing.List[str]:
    if inkscape_version < 1:
        return INKSCAPE_092_SVG_TO_PNG_OPTIONS
    else:
        return INKSCAPE_100_SVG_TO_PNG_OPTIONS


def generate_inkscape_command(
    input_path: str, output_path: str, options: typing.List[str]
) -> typing.List[str]:
    return [INKSCAPE_EXECUTABLE, input_path, *options, output_path]


class ImagePreviewBuilderInkscape(ImagePreviewBuilder):
    weight = 70

    @classmethod
    def get_label(cls) -> str:
        return "Vector images - based on Inkscape"

    @classmethod
    def get_supported_mimetypes(cls) -> typing.List[str]:
        return ["image/svg+xml", "image/svg"]

    @classmethod
    def check_dependencies(cls) -> None:
        if not executable_is_available("inkscape"):
            raise BuilderDependencyNotFound("this builder requires inkscape to be available")

    @classmethod
    def dependencies_versions(cls) -> typing.Optional[str]:
        return "{} from {}".format(
            check_output(["inkscape", "--version"], universal_newlines=True).strip(),
            which("inkscape"),
        )

    def build_jpeg_preview(
        self,
        file_path: str,
        preview_name: str,
        cache_path: str,
        page_id: int,
        extension: str = ".jpg",
        size: ImgDims = None,
        mimetype: str = "",
    ) -> None:
        if not size:
            size = self.default_size
        # inkscape tesselation-P3.svg  -e
        with tempfile.NamedTemporaryFile(
            "w+b", prefix="preview-generator-", suffix=".png"
        ) as tmp_png:
            inkscape_version = get_inkscape_version()
            build_png_result_code = check_call(
                generate_inkscape_command(
                    file_path,
                    tmp_png.name,
                    options=get_inkscape_svg_to_png_options(inkscape_version),
                ),
                stdout=DEVNULL,
                stderr=STDOUT,
            )

            if build_png_result_code != 0:
                raise IntermediateFileBuildingFailed(
                    "Building PNG intermediate file using inkscape "
                    "failed with status {}".format(build_png_result_code)
                )

            return ImagePreviewBuilderPillow().build_jpeg_preview(
                tmp_png.name, preview_name, cache_path, page_id, extension, size, mimetype
            )
