"""Fill viewer_template.html (this folder) with one part family's models and views."""
import json
import os

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer_template.html")


def legend_html(items):
    return "".join('<span style="--sw:{}">{}</span>'.format(c, t) for c, t in items)


def fill(models, views, title, subtitle, description, legend, storage_key):
    html = open(TEMPLATE).read()
    for k, v in (("__TITLE__", title), ("__SUBTITLE__", subtitle), ("__DESCRIPTION__", description), ("__LEGEND__", legend_html(legend)), ("__STORAGE_KEY__", storage_key)):
        html = html.replace(k, v)
    return html.replace("__DATA__", json.dumps({"models": models, "views": views}))
