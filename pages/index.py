#!/bin/python


from pages.util import *

def index(env, start_res):
    dt_str = env["HTTP_REQUEST"].log_date_time_string()
    print(f'{" " * 8}"GET /" @ [{dt_str}]')
    print()
    print("----" * 20)
    with open("pages/index.htm", "r") as f:
        content = f.read()
        start_res("200 OK", [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(content.encode("utf-8"))))
        ])
        return content

def index_css(env, start_res):
    with open("pages/index.css", "r") as f:
        content = f.read()
        start_res("200 OK", [
                ("Content-Type", "text/css; charset=utf-8"),
                ("Content-Length", str(len(content)))
        ])
        return content

def index_js(env, start_res):
    with open("pages/index.js", "r") as f:
        content = f.read()
        start_res("200 OK", [
                ("Content-Type", "application/javascript; charset=utf-8"),
                ("Content-Length", str(len(content.encode("utf-8"))))
                # it has non-ascii chr inside
        ])
        return content

def favicon(env, start_res):
    with open("pages/favicon.png", "rb") as f:
        content = f.read()
        start_res("200 OK", [
                ("Content-Type", "image/png"),
                ("Content-Length", str(len(content)))
        ])
        return content


def initialize(wsgi_application_handler):
    for regex, func in {
            "/(index(.html?)?)?": index,
            "/index.css": index_css,
            "/index.js": index_js,
            "/([^/]+/)*favicon.(png|icon?)": favicon,
    }.items():
        wsgi_application_handler.add("GET", regex, func)

        
    for abs_path in [
            "/", "/index", "/index.htm", "/index.html",
            "/index.css", "/index.js", "/favicon.ico"]:
        wsgi_application_handler.exclude_log(abs_path)