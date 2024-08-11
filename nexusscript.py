import argparse
import requests
import time

parser = argparse.ArgumentParser(description="calls ttp scheduler api to find appointments and sends ntfy notification")
 
parser.add_argument("-l", "--location_code", metavar="location_code", type=int, help="enter the ttp interview location code" )
parser.add_argument("-t", "--ntfy_topic", metavar="ntfy_topic", type=str, help="enter your ntfy topic name")
parser.add_argument("-i", "--interval", metavar="interval", type=int, help="api request interval (s)")

args = parser.parse_args()

loc_code = str(args.location_code)
api_url = f"https://ttp.cbp.dhs.gov/schedulerapi/slot-availability?locationId={loc_code}"

ntfy_topic = args.ntfy_topic
ntfy_url = f"https://ntfy.sh/{ntfy_topic}"

interval = args.interval

current_timestamp = ""

# Function to check slot availability
def check_slots():
    global current_timestamp
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
                notify_response = requests.post(ntfy_url, data=message)

                if notify_response.status_code == 200:
                    print(f"Notification sent: {message} ({time.ctime()})")
                    current_timestamp = start_timestamp
                else:
                    print("Failed to send notification.")
                
            else:
                print(f"Appointment on {start_timestamp}, notification previously sent {time.ctime()}")

        else:
            print(f"No slots found({time.ctime()})")

    except requests.RequestException as e:
        print(f"An error occurred: {e}")

while True:
    check_slots()
    time.sleep(interval)