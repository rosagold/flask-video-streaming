#!/usr/bin/env python
import logging
import threading
import time
from importlib import import_module
import os

import cv2
import numpy as np
from flask import Flask, render_template, Response, request, session

from camera_opencv import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)
app.secret_key = b'asdjcn2388u28*(UY#89h239-*(Y(#@*HYR(Q#@*'

status_event = threading.Event()
status = "init"
main_client = None
clients = 0


# @app.route("/dead")
# def dead():
#     return "This app is meant to run as a single instance, but another currently " \
#            "is running. Please refresh the page"


@app.route("/")
def index():
    global main_client
    session['id'] = threading.get_ident()
    main_client = session['id']
    status_event.set()
    time.sleep(0)
    return render_template("index.html", initial_status=status)


@app.route("/buttons", methods=["POST"])
def handle_buttons():
    global status, viewer_id
    last = status
    action = request.data.decode()
    if action == "start":
        status = "running"
    if action == "stop":
        status = "stopped"
    if last == status:
        logging.debug(f"{action=}, {status=}, => no update")
    else:
        logging.info(f"{action=} => {status=}")
    if not status_event.is_set():
        status_event.set()
        time.sleep(0)  # needed for gevent
    return ""


def frame_stream(id):
    """Video streaming generator function."""
    print(f'new stream {id}')
    camera = Camera()
    yield b"--frame\r\n"
    while True:
        if id != main_client:
            return b"--frame\r\n"
        else:
            time.sleep(0.1)
        frame = camera.get_frame()
        yield b"Content-Type: image/png\r\n\r\n" + frame + b"\r\n--frame\r\n"


def status_stream(id):
    while True:
        status_event.wait()
        status_event.clear()
        if id != main_client:
            s = "Another client is using the app. Please refresh the page."
            yield f"data: foo\n\n"

        yield f"data: {status}\n\n"


@app.route("/video_feed")
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(frame_stream(session['id']),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/status")
def status_feed():
    return Response(status_stream(session['id']), mimetype="text/event-stream")


if __name__ == "__main__":
    # either so or so
    # gunicorn --workers=1 --threads=8 --bind=10.10.10.10:5000 app:app
    # gunicorn --workers=1 --worker-class gevent --bind=10.10.10.10:5000 app:app
    print("swoooosh")
    logging.basicConfig(level="DEBUG")
    app.run(threaded=True, debug=True, port=5000)

    # app.run(host="10.10.10.10", threaded=True, debug=True, port=5000)
