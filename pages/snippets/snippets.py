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


def status(env, start_res):
    start_res("200 OK", [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", "0")
    ])
    return ""



def initialize(wsgi_application_handler):
    for regex, func in {
            r"/(code_)?snippets?/?":
                    static_file(""),
            r"/(code_)?snippets?/pointer(_event)?(\.html?)?":
                    static_file("pages/snippets/pointer_event.htm"),
            r"/(code_)?snippets?/react(\.html?)?":
                    static_file("pages/snippets/react.htm"),
            r"/status": status,
    }.items():
        wsgi_application_handler.add("GET", regex, func)