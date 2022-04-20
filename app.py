#!/usr/bin/env python
import logging
import threading
import time
from flask import Flask, render_template, Response, request, session

from camera_opencv import Camera

app = Flask(__name__)
app.secret_key = b'asdjcn2388u28*(UY#89h239-*(Y(#@*HYR(Q#@*'
status_event = threading.Event()
status = "init"
main_client_id = None


@app.route("/")
def index():
    global main_client_id
    session['id'] = threading.get_ident()
    main_client_id = session['id']
    status_event.set()
    time.sleep(0)
    return render_template("index.html", initial_status=status)


@app.route("/buttons", methods=["POST"])
def handle_buttons():
    global status
    # ignore other clients
    if session['id'] != main_client_id:
        return ""
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
    logging.debug(f'new video_stream {id}')
    camera = Camera()
    yield b"--frame\r\n"
    while id == main_client_id:
        frame = camera.get_frame()
        yield b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n--frame\r\n"


def status_stream(id):
    logging.debug(f'new status_stream {id}')
    while True:
        status_event.wait()
        status_event.clear()
        if id == main_client_id:
            yield f"data: {status}\n\n"
        else:
            yield f"data: close\n\n"
            break


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
