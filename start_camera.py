import base64
import datetime
import json
import os
import sys
import argparse
import requests

from Speed.updated_speed import *

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--server-hostname", default=os.environ.get("SERVER_URL", "localhost:3001"),
                    help="The name of the server, INCLUDING port (for example 127.0.0.1:1337")
parser.add_argument("--gui", action="store_true")
args = parser.parse_args()

server_address = f"http://{args.server_hostname}"
image_server = f"{server_address}/img"
notify_server = f"{server_address}/notify"


def main(gui):
    for (distance, speed, frame) in get_incoming_danger(gui):
        # print(f"distance: {distance} , speed: {speed}")
        if should_alert(distance, speed):
            alert(distance=distance, speed=speed, frame=frame)
        else:
            relax(danger=calculate_danger(distance, speed))


def send_frame(frame):
    retval, buffer = cv2.imencode('.jpg', frame)
    encoded_data = base64.b64encode(buffer).decode('utf-8')

    # Create a JSON payload with the base64-encoded data
    payload = {
        'data': encoded_data
    }

    headers = {'Content-Type': 'application/json'}

    response = requests.post(image_server, data=json.dumps(payload), headers=headers)
    print(response)


def notify_api(danger, alert=1):
    try:
        params = {'danger': danger, 'alert': alert}
        response = requests.post(notify_server, params=params)
        print(response)
    except Exception as e:
        pass


def calculate_danger(distance, speed):
    danger = 15 / distance + 4 * speed
    return danger


relax_counter = 0


def relax(danger):
    global relax_counter
    print("relaxing")
    relax_counter += 1
    if relax_counter >= 10:
        notify_api(danger=danger, alert=0)
        relax_counter = 0


last_sent_frame = datetime.datetime.now()


def alert(distance, speed, frame):
    global last_sent_frame
    if datetime.datetime.now() - last_sent_frame > datetime.timedelta(seconds=0.5):
        last_sent_frame = datetime.datetime.now()
        send_frame(frame)
    notify_api(danger=calculate_danger(distance, speed))
    print(f"ALERT: distance: {distance} , speed: {speed}")


def should_alert(distance, speed):
    return (speed >= 0 or distance < 0.5) and calculate_danger(distance, speed) > 30


if __name__ == '__main__':
    main(gui=args.gui)
