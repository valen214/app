#!/bin/python

from pages.util import content_type

def static_file(static_path):
    def static_file(env, start_res):
        with open(static_path, "r") as f:
            content = f.read()
            start_res("200 OK", [
                ("Content-Type", content_type(static_path)),
                ("Content-Length", str(len(content)))
            ])
            return content
    return static_file



def initialize(wsgi_application_handler):
    for regex, func in {
            r"/snippets?/?":
                    static_file(""),
            r"/snippets?/pointer(_event)?(\.html?)?":
                    static_file("pages/snippets/pointer_event.htm"),
    }.items():
        wsgi_application_handler.add("GET", regex, func)