from common.assets import ImageAsset, load_image_asset
from common.behaviours.ui.widget import Widget


class UIImage(Widget):
    def on_init(self):
        self._image: ImageAsset | None = None

    @property
    def image(self):
        return self._image

    def on_serialize(self, out_dict: dict):
        if self._image:
            out_dict["image"] = self._image.path

    def on_deserialize(self, in_dict: dict):
        dict_image = in_dict.get("image")
        if dict_image is not None:
            self._image = load_image_asset(dict_image)
