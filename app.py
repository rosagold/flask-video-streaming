#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, request

from camera_opencv import Camera
# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)

status = 'running'


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html', init_status=status)


def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        if status == 'stopped':
            continue
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(
        gen(Camera()),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/buttons', methods=['POST', 'GET'])
def handle_buttons():
    global status
    action = request.data.decode()
    if action == 'start':
        status = 'running'
    if action == 'stop':
        status = 'stopped'
    print(f"{action=} -> {status}")
    return status


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=True)
