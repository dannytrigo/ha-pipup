from typing import Final

DOMAIN = "ha_pipup"
ANDROIDTV_DOMAIN = "androidtv"
DEFAULT_NAME: Final = "HA PipUp"

ATTR_DURATION = "duration"
ATTR_POSITION = "position"
ATTR_TITLE = "title"
ATTR_TITLE_COLOUR = "title_colour"
ATTR_TITLE_SIZE = "title_size"
ATTR_MESSAGE = "message"
ATTR_MESSAGE_COLOUR = "message_colour"
ATTR_MESSAGE_SIZE = "message_size"
ATTR_BACKGROUND_COLOUR = "background_colour"
ATTR_MEDIA_IMAGE = "media_image"
ATTR_MEDIA_VIDEO = "media_video"
ATTR_MEDIA_WEB = "media_web"
ATTR_MEDIA_WIDTH = "media_width"
ATTR_MEDIA_HEIGHT = "media_height"
ATTR_IMAGE_FILENAME = "image_filename"
POST_VARS = {
    ATTR_DURATION: "duration",
    ATTR_POSITION: "position",
    ATTR_TITLE: "title",
    ATTR_TITLE_COLOUR: "titleColor",
    ATTR_TITLE_SIZE: "titleSize",
    ATTR_MESSAGE: "message",
    ATTR_MESSAGE_COLOUR: "messageColor",
    ATTR_MESSAGE_SIZE: "messageSize",
    ATTR_BACKGROUND_COLOUR: "backgroundColor",
}
MEDIA_POST_VARS = {
    ATTR_MEDIA_IMAGE: "image",
    ATTR_MEDIA_VIDEO: "video",
    ATTR_MEDIA_WEB: "web",
}
MEDIA_PARAM_VARS = {
    ATTR_MEDIA_WIDTH: "width",
    ATTR_MEDIA_HEIGHT: "height",
}
