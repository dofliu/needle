from pathlib import Path

from PIL import Image


source = Path("/tmp/esp32-pocket-control-icon.png")
destinations = [
    Path("/home/ubuntu/esp32-pocket-control/assets/images/icon.png"),
    Path("/home/ubuntu/esp32-pocket-control/assets/images/splash-icon.png"),
    Path("/home/ubuntu/esp32-pocket-control/assets/images/favicon.png"),
    Path("/home/ubuntu/esp32-pocket-control/assets/images/android-icon-foreground.png"),
]

with Image.open(source) as image:
    rgba = image.convert("RGBA")
    rgba.thumbnail((512, 512), Image.Resampling.LANCZOS)
    for destination in destinations:
        rgba.save(destination, format="PNG", optimize=True, compress_level=9)
