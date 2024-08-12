import argparse
import requests
import time
import threading
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler('nexusscript.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

parser = argparse.ArgumentParser(description="calls ttp scheduler api to find appointments and sends ntfy notification")

parser.add_argument("-l", "--location_code", metavar="location_code", type=int, help="enter the ttp interview location code")
parser.add_argument("-t", "--ntfy_topic", metavar="ntfy_topic", type=str, help="enter your ntfy topic name")
parser.add_argument("-i", "--interval", metavar="interval", type=int, help="api request interval (s)")

args = parser.parse_args()

loc_code = str(args.location_code)
api_url = f"https://ttp.cbp.dhs.gov/schedulerapi/slot-availability?locationId={loc_code}"

ntfy_topic = args.ntfy_topic
ntfy_url = f"https://ntfy.sh/{ntfy_topic}"

interval = args.interval

current_timestamp = ""
current_status = ""

def check_slots():
    global current_timestamp, current_status
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad status codes

        data = response.json()

        if data["availableSlots"]:
            slot = data["availableSlots"][0]
            start_timestamp = slot["startTimestamp"]

            if start_timestamp != current_timestamp:
                # Send notification via ntfy.sh
                message = f"Appointment on {start_timestamp}"
                notify_response = requests.post(ntfy_url, data=message, headers={"Priority": "5"})

                if notify_response.status_code == 200:
                    log_message = f"Notification sent: {message} ({time.ctime()})"
                    logger.info(log_message)
                    current_timestamp = start_timestamp
                    current_status = log_message
                else:
                    log_message = "Failed to send notification."
                    logger.error(log_message)

            else:
                log_message = f"Appointment on {start_timestamp}, notification previously sent ({time.ctime()})"
                logger.info(log_message)
                current_status = log_message

        else:
            log_message = f"No slots found ({time.ctime()})"
            logger.info(log_message)
            current_status = log_message

    except requests.RequestException as e:
        log_message = f"An error occurred: {e}"
        logger.error(log_message)
        current_status = log_message

def status_update():
    global current_status
    while True:
        time.sleep(15)
        requests.post(ntfy_url, data=f"STATUS UPDATE Current time: {time.ctime()} last status {current_status}", headers={"Priority": "1"})
        logger.info("Status message sent")
        time.sleep(585)

# Start the status_update thread
status_thread = threading.Thread(target=status_update)
status_thread.daemon = True
status_thread.start()

# Main loop to run check_slots every interval seconds
while True:
    check_slots()
    time.sleep(interval)