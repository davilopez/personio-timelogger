#!/usr/bin/env python3

import sys
import os
import json
import re
import urllib.request as request
import urllib.parse as parse
import http.cookiejar
import pytz
import requests

from time import sleep
from random import randint
from datetime import timedelta
from datetime import datetime

try:
    from config import (
        ATTENDANCE_URL,
        EMAIL,
        LOGIN_URL,
        PASSWORD,
        SLACK_BOT_URL,
        SLACK_SECRET,
        STARTING_HOUR,
        WORKING_DAYS,
        WORKING_HOURS
    )

except ImportError:
    print("WARNING: no config.py found. Please RTFM!")
    sys.exit(1)

if len(sys.argv) == 1 or sys.argv[1] == "--help":
    help_message = "Error. No argument" + "\n\n"
    help_message += "Usage: %s [date]" % __file__ + "\n"
    help_message += "Note: Date format yyyy-mm-dd" + "\n"
    print(help_message)
    exit()

WORKING_TIME = WORKING_HOURS * 60
MIN_START_TIME = STARTING_HOUR * 60

def is_dst(dt=None, timezone="UTC"):
    if dt is None:
        dt = datetime.utcnow()
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(dt, is_dst=None)
    return timezone_aware_date.tzinfo._dst.seconds != 0


def checkDate(dateInput):
    return re.fullmatch(r"\A([\d]{4})-([\d]{2})-([\d]{2})", dateInput)

if not checkDate(sys.argv[1]):
    error_message = "Error. Wrong date format" + "\n\n"
    error_message += "Usage: %s [date]" % __file__ + "\n"
    error_message += "Note: Date format yyyy-mm-dd" + "\n"
    print(error_message)
    exit()

def formatDate(date):
    if is_dst(timezone="Europe/Madrid"):
        return date + "T00:00:00+02:00"
    else:
        return date + "T00:00:00+01:00"


def generateMessage(date, message):
    post_date = formatDate(date)
    return [{"email": EMAIL, "date": post_date, "message": message}]

def format_datetime(date, time):
    return f'{date}T{time}Z'
    
def generateAttendance(date):
    post_date = formatDate(date)
    break_time = randint(50, 70)
    start_time = MIN_START_TIME + randint(5, 45)
    working_time = randint(WORKING_TIME - 25, WORKING_TIME - 5)
    end_time = start_time + working_time

    return [
        {
            "id": str(uuid.uuid1()),
            "start": format_datetime(date, start_time),
            "end": format_datetime(date, end_time),
            "comment": "",
            "project_id": None,
            "employee_id": employee_id,
            "activity_id": None,
        },
        {
            "id": str(uuid.uuid1()),
            "start": format_datetime(date, start_time),
            "end": format_datetime(date, end_time),
            "comment": "",
            "project_id": None,
            "employee_id": employee_id,
            "activity_id": None,
        }
    ]


def getDayInfo(date, urlOpener):
    month = date[:7]
    post_date = formatDate(date)
    response = urlOpener.open(ATTENDANCE_URL + "/" + month).read().decode("utf-8")
    day_list = json.loads(response)["data"]["rows"]
    the_day = next((x for x in day_list if x["date"] == post_date), False)
    if the_day:
        if the_day["absences_holidays"] in WORKING_DAYS:
            return {"isWorkingDay": True}
    return {"isWorkingDay": False, "dayLabel": the_day["absences_holidays"]}


def slack_bang(data):
    postData = {
        "email": EMAIL,
        "slackSecret": SLACK_SECRET,
        "day": str(data[0]["date"])[0:10],
        "startTime": str(timedelta(minutes=data[0]["start_time"]))
        if (data[0].get("start_time") is not None)
        else "",
        "endTime": str(timedelta(minutes=data[0]["end_time"]))
        if (data[0].get("end_time") is not None)
        else "",
        "breakTime": str(data[0]["break_time"])
        if (data[0].get("break_time") is not None)
        else "",
        "message": str(data[0]["message"])
        if (data[0].get("message") is not None)
        else "",
    }

    json_data = json.dumps(postData)

    command = "curl --silent -X POST -H 'Content-type: application/json'"
    command += " --data '" + json_data + "'"
    command += " " + SLACK_BOT_URL + "/timelogger"
    command += " > /dev/null"
    # print(command)
    os.system(command)


if __name__ == "__main__":
    # RUN

    # Wait between 1-10 seconds before logging in
    sleep(randint(1, 10))

    # Create request session
    session = requests.Session()

    response = session.post(
        LOGIN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"email": EMAIL, "password": PASSWORD}
    )



    response = session.post(
        ATTENDANCE_URL,
        json=[format_period_data(
            attendance_date, "09:31:00", "16:45:00", PROFILE_ID
        )],
    )

    data = json.loads(response.text)
    try:
        return f"Error: {data['error']['message']}"
    except KeyError:
        return f"Success: attendance on {attendance_date} registered!"

    # Inform User
    slack_bang(response.text)
