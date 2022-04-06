#!/usr/bin/env python
import logging
import threading
import time
from importlib import import_module
import os

import cv2
import numpy as np
from flask import Flask, render_template, Response, request

from camera_opencv import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)
status_event = threading.Event()
status = "init"


@app.route("/")
def index():
    """Video streaming home page."""
    return render_template("index.html", initial_status=status)


@app.route("/buttons", methods=["POST"])
def handle_buttons():
    global status
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
        status_event.set()
    return ""


def frame_stream(camera):
    """Video streaming generator function."""
    yield b"--frame\r\n"
    while True:
        if status == "stopped":
            status_event.wait()
            continue
        frame = camera.get_frame()
        yield b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n--frame\r\n"


def status_stream():
    while True:
        status_event.wait()
        status_event.clear()
        yield f"data: {status}\n\n"


@app.route("/video_feed")
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        frame_stream(Camera()), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/status")
def status_feed():
    return Response(status_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    print("woooo")
    logging.basicConfig(level="DEBUG")
    app.run(host="0.0.0.0", threaded=True, debug=True)
