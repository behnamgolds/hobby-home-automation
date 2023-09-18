#!/usr/bin/python3

from random import randrange
from time import sleep
import Adafruit_BBIO.GPIO as GPIO
import requests
import routeros_api
import xmltodict
import sys
import logging


### GPIO
BTN = "P9_15"
LED = "P9_12"
GPIO.setup(BTN, GPIO.IN)
GPIO.setup(LED, GPIO.OUT)
GPIO.output(LED, GPIO.LOW)
### GPIO

### LOG
LOG_FORMAT = '%(message)s'
logging.basicConfig(format=LOG_FORMAT)
### LOG


### DVR
# alarm_status variable this holds the previous status for
# the isapi_check() function to detect status change
DVR_IP = "1.1.1.1"
DVR_OUTPUTS_PATH = "/ISAPI/System/IO/outputs/"
DVR_ALARM_OUT_ID = "O-1"
DVR_BASE_URL = "http://" + DVR_IP + DVR_OUTPUTS_PATH  + DVR_ALARM_OUT_ID
DVR_STATUS_URL = DVR_BASE_URL + "/status"
DVR_TRIGGER_URL = DVR_BASE_URL + "/trigger"
DVR_AUTH = ("admin", "dvr_password_here")
DVR_HEADERS = {"Content-Type": "application/xml; charset='UTF-8'"}
DVR_ACTIVATION_PAYLOAD = "/root/cam-privacy/alarm_activate.xml"
DVR_DEACTIVATION_PAYLOAD = "/root/cam-privacy/alarm_deactivate.xml"
dvr_alarm_status = "disabled"
### DVR

### RouterOS
ROS_IP = "2.2.2.2"
ROS_FILTER_PATH = "/interface/bridge/filter"
ROS_FILTER_RULE = "0"
ROS_FILTER_COMMENT = "dvr-mgr"
ROS_USER = "admin"
ROS_PASS = "routeros_password_here"
ros_connection = None
ros_api = None
### RouterOS


def ros_activate_rule():
    ros_connect()
    if ros_api:
        ros_api.get_binary_resource(ROS_FILTER_PATH).call('enable', {'numbers': ROS_FILTER_RULE})
        ros_disconnect()


def ros_deactivate_rule():
    ros_connect()
    if ros_api:
        ros_api.get_binary_resource(ROS_FILTER_PATH).call('disable', {'numbers': ROS_FILTER_RULE})
        ros_disconnect()


def ros_is_rule_enabled():
    ros_connect()
    result = None
    if ros_api:
        try:
            filter_list = ros_api.get_resource(ROS_FILTER_PATH)
            result = filter_list.get(comment=ROS_FILTER_COMMENT)[0]['disabled']
        finally:
            ros_disconnect()

        if result == 'false':
            return True
        else:
            return False

    return False


def ros_disconnect():
    if ros_connection:
        ros_connection.disconnect()


def ros_connect():
    global ros_connection
    global ros_api
    ros_disconnect()
    try:
        ros_connection = routeros_api.RouterOsApiPool(ROS_IP, username=ROS_USER, password=ROS_PASS, plaintext_login=True,)
        ros_api = ros_connection.get_api()
    except:
        ros_log_connection_failure()
        ros_connection = None
        ros_api = None


def ros_log_connection_failure():
    logging.error("RouterOS API connection failure")


def dvr_activate_alarm():
    with open(DVR_ACTIVATION_PAYLOAD) as payload:
        try:
            res = requests.put(DVR_TRIGGER_URL, headers=DVR_HEADERS, auth=DVR_AUTH, data=payload, timeout=3)
            res.close()
        except:
            dvr_log_connection_failure()
        finally:
            return


def dvr_deactivate_alarm():
    with open(DVR_DEACTIVATION_PAYLOAD) as payload:
        try:
            res = requests.put(DVR_TRIGGER_URL, headers=DVR_HEADERS, auth=DVR_AUTH, data=payload, timeout=3)
            res.close()
        except:
            dvr_log_connection_failure()
        finally:
            return


def dvr_get_alarm_status():
    try:
        res = requests.get(DVR_STATUS_URL, auth=DVR_AUTH, timeout=3)
        xml_dict = xmltodict.parse(res.text)
        res.close()
        return xml_dict["IOPortStatus"]["ioState"]
    except:
        dvr_log_connection_failure()
        return "inactive"


def dvr_log_connection_failure():
    logging.error("DVR API connection failure")


def gpio_blink():
    for i in range(1, 4):
        gpio_turn_on_led()
        sleep(0.06)
        gpio_turn_off_led()
        sleep(0.06)
    if dvr_alarm_status == 'active':
        gpio_turn_on_led()


def gpio_btn_pushed(channel):
    # we just trigger the dvr alarm on or off here, the main
    # function checks it every 3 seconds and acts accordingly.
    gpio_blink()
    if dvr_alarm_status == "inactive":
        # ros_activate_rule()
        dvr_activate_alarm()
    elif dvr_alarm_status == "active":
        # ros_deactivate_rule()
        dvr_deactivate_alarm()


def gpio_turn_off_led():
    GPIO.output(LED, GPIO.LOW)


def gpio_turn_on_led():
    GPIO.output(LED, GPIO.HIGH)


def log_activating():
    logging.info("Activating")


def log_deactivating():
    logging.info("Deactivating")


def log_starting():
    print("Starting Camera Privacy")
    logging.info("Starting Camera Privacy")


def log_stopping():
    print("Stopping Camera Privacy")
    logging.info("Stopping Camera Privacy")


def main():
    global dvr_alarm_status
    while True:
        try:
            # Check ISAPI here and handle the exceptions in its own function
            new_status = dvr_get_alarm_status()
            # we should make a decision here to check if we should change the status
            # we need to change ros rules here and also turn on/off the LED
            if new_status != dvr_alarm_status:
                gpio_blink()
                dvr_alarm_status = new_status
                if dvr_alarm_status == "active":
                    log_activating()
                    ros_activate_rule()
                    # Maybe check the rule status on ros and then turn the LED on?!
                    if ros_is_rule_enabled():
                        gpio_turn_on_led()
                    else:
                        log_deactivating()
                        dvr_deactivate_alarm()
                        dvr_alarm_status = 'inactive'
                elif dvr_alarm_status == "inactive":
                    log_deactivating()
                    ros_deactivate_rule()
                    if not ros_is_rule_enabled():
                        gpio_turn_off_led()
            sleep(3)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    # This runs in another thread and will not get blocked by main()
    log_starting()
    GPIO.add_event_detect(BTN, GPIO.FALLING, callback=gpio_btn_pushed, bouncetime=500)
    main()
    log_stopping()
    ros_disconnect()
    GPIO.remove_event_detect(BTN)
    GPIO.cleanup()
    sys.exit(0)

