#!/usr/bin/env python
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

status = 'init'
default_frame = cv2.imencode('.jpg', np.zeros((100,100)))[1].tobytes()

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        if status == 'stopped':
            time.sleep(1)
            frame = default_frame
        else:
            frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        gen(Camera()),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/buttons', methods=['POST'])
def handle_buttons():
    global status
    action = request.data.decode()
    if action == 'start':
        status = 'running'
    if action == 'stop':
        status = 'stopped'
    print(f"{action=} -> {status}")
    return ''


@app.route('/status', methods=['GET'])
def return_status():
    return status


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=True)
