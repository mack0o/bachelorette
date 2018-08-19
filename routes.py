import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import os

from app import app
from apps import index, numbers

# Add a static image route that serves images from desktop
@app.server.route("/{route}/<image_name>".format(route=app.static_image_route))
def serve_image(image_name):
    if image_name not in app.valid_images:
        raise Exception(
            '"{}" is excluded from the allowed static files'.format(image_name))
    return flask.send_from_directory(app.image_dir, image_name)

# display pages based on url
@app.callback(Output("page-content", "children"),
    [Input("url", "pathname")])
def display_page(pathname):
    if pathname:
        pathname = pathname.strip("/")
    paths = {
        "": index.layout,
        "the-numbers": numbers.layout,
    }
    # TODO change default behavior to return 404 error
    return paths.get(pathname, index.layout)