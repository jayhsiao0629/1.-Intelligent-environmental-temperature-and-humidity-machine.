from __future__ import barry_as_FLUFL
from bluepy.btle import Scanner, DefaultDelegate
import Adafruit_DHT
import time
import requests
import random
import sys
import threading
import logging
import os
import speech_recognition as sr
from gtts import gTTS
from tkinter.tix import ButtonBox
import RPi.GPIO as GPIO
import cv2
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier('haarcascade_smile.xml')

'''
global variables
'''
ENDPOINT = "industrial.api.ubidots.com"
DEVICE_LABEL = "weather-station"
VARIABLE_LABEL = "temperature"
VARIABLE_LABEL2 = "humid"
TOKEN = "BBFF-BGKP7VSKRvpVd6tvwrhizWXgGU19d0" # replace with your TOKEN
DELAY = 1  # Delay in seconds
enter_smile = False
enter_voice = False
LED_PIN = 12
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)
mode = 0


humid_temperature_list = [0, 0]


def post_var(payload, url=ENDPOINT, device=DEVICE_LABEL, token=TOKEN):
    try:
        url = "http://{}/api/v1.6/devices/{}".format(url, device)
        headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

        attempts = 0
        status_code = 400

        while status_code >= 400 and attempts < 5:
            # print("[INFO] Sending data, attempt number: {}".format(attempts))
            req = requests.post(url=url, headers=headers,
                                json=payload)
            status_code = req.status_code
            attempts += 1
            time.sleep(1)

        # print("[INFO] Results:")
        print(req.text)
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))

def detect_humid(name):
    dht11 = Adafruit_DHT.DHT11
    DHT_PIN = 4
    global enter_smile
    while True:
        
        h, t = Adafruit_DHT.read_retry(dht11, DHT_PIN)
        print(h, t)
        time.sleep(1)
        payload = {VARIABLE_LABEL: t}
        payload2 = {VARIABLE_LABEL2: h}
        humid_temperature_list[0] = h
        humid_temperature_list[1] = t
        post_var(payload)
        post_var(payload2)
        if enter_smile:
            return
        
        
        time.sleep(5)

flag = False
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

def detect_near(name):
    global flag
    # global enter_smile
    scanner = Scanner().withDelegate(ScanDelegate())
    while 1:
        try:
            # if enter_smile:
            #     return
            devices = scanner.scan(1)

            for dev in devices:
                for (adtype, desc, value) in dev.getScanData():
                    if '177777' in value:
                        print("RSSI = ", dev.rssi)
                        if dev.rssi > -60:
                            flag = True
                            GPIO.output(LED_PIN, GPIO.HIGH)
                            time.sleep(3)
                            return
                        else:
                            flag = False
                            GPIO.output(LED_PIN, GPIO.LOW)
                            time.sleep(3)
                            return
                if flag:
                    break
        except KeyboardInterrupt:
            break

def recognize_voice(name):
    global flag
    with sr.Microphone() as source:
        recognizer = sr.Recognizer()
        recognizer.adjust_for_ambient_noise(source)
        recognizer.dynamic_energy_threshold = 3000

        try:
            print("Listening....")
            audio = recognizer.listen(source, timeout=5.0)
            response = recognizer.recognize_google(audio)
            print(response)
            if 'humid' in response:
                if flag == True:
                    print("enter")
                    h = humid_temperature_list[0]
                    t = humid_temperature_list[1]
                    # h = 1
                    # t = 2
                    tts = gTTS(text='the temperature is{},humid is{}'.format(h, t), lang='en')
                    tts.save('hello_tw_open8.mp3')
                    os.system('omxplayer -o local -p hello_tw_open8.mp3 > /dev/null 2>&1')
                else:
                    tts = gTTS(text='you are not my owner', lang='en')
                    tts.save('hello_tw_open5.mp3')
                    os.system('omxplayer -o local -p hello_tw_open5.mp3 > /dev/null 2>&1')
            
            else:
                tts = gTTS(text='i can not understand', lang='en')
                tts.save('hello_tw_open1.mp3')
                os.system('omxplayer -o local -p hello_tw_open1.mp3 > /dev/null 2>&1')
        except sr.UnknownValueError:
            print("DiDN'T RECOGNIZE THAT.")

red_line = 0

def detect(gray, frame):
    global flag
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), ((x + w), (y + h)), (255, 0, 0), 2)
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]
        smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)

        for (sx, sy, sw, sh) in smiles:
            cv2.rectangle(roi_color, (sx, sy), ((sx + sw), (sy + sh)), (0, 0, 255), 2)
            global red_line
            red_line += 1
            # global enter_smile
            # enter_smile = True
            # if flag:
            #     h = humid_temperature_list[0]
            #     t = humid_temperature_list[1]
            #     tts = gTTS(text='現在溫度{},濕度{}'.format(t, h), lang='zh-TW')
            #     tts.save('hello_tw_open.mp3')
            #     os.system('omxplayer -o local -p hello_tw_open.mp3 > /dev/null 2>&1')
            # else:
            #     tts = gTTS(text='你不是我的擁有人', lang='zh-TW')
            #     tts.save('hello_tw_open.mp3')
            #     os.system('omxplayer -o local -p hello_tw_open.mp3 > /dev/null 2>&1')
    return frame


def smile_detection(name):
    video_capture = cv2.VideoCapture(0)
    while video_capture.isOpened():
    # Captures video_capture frame by frame
        _, frame = video_capture.read()

        # To capture image in monochrome					
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # calls the detect() function	
        canvas = detect(gray, frame)

        # Displays the result on camera feed					
        cv2.imshow('Video', canvas)
        if red_line >= 5:
            global enter_smile
            enter_smile = True
            if flag:
                h = humid_temperature_list[0]
                t = humid_temperature_list[1]
                tts = gTTS(text='現在溫度{},濕度{}'.format(t, h), lang='zh-TW')
                tts.save('hello_tw_open.mp3')
                os.system('omxplayer -o local -p hello_tw_open.mp3 > /dev/null 2>&1')
                break
            else:
                tts = gTTS(text='你不是我的擁有人', lang='zh-TW')
                tts.save('hello_tw_open.mp3')
                os.system('omxplayer -o local -p hello_tw_open.mp3 > /dev/null 2>&1')
                break
        # The control breaks once q key is pressed						
        if cv2.waitKey(1) & 0xff == ord('q'):			
            break
       
    # Release the capture once all the processing is done.
    video_capture.release()								
    cv2.destroyAllWindows()


if __name__ == '__main__':
    # format = "%(asctime)s: %(message)s"
    # logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    print("enter the mode: ", end="")
    b = int(input("Enter the mode: "))
    if b == 1:
        detect_near(1)
        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
        logging.info("Main    : before creating thread1")
        r1 = threading.Thread(target=detect_humid, args=(1,))
        logging.info("Main    : before running thread1")
        
        # time.sleep(3)
        logging.info("Main    : before creating thread2")
        r2 = threading.Thread(target=recognize_voice, args=(2,))
        logging.info("Main    : before running thread2")
        
        # logging.info("Main    : before creating thread3")
        # z = threading.Thread(target=detect_near, args=(3,))
        # logging.info("Main    : before running thread3")
        r2.start()
        r1.start()
        r2.join()
        r1.join()
    else:
        logging.info("Main    : before creating thread1")
        x = threading.Thread(target=detect_humid, args=(1,))
        logging.info("Main    : before running thread1")
        x.start()
        time.sleep(1)
        logging.info("Main    : before creating thread3")
        z = threading.Thread(target=detect_near, args=(3,))
        logging.info("Main    : before running thread3")
        z.start()
        
        logging.info("Main    : before creating thread4")
        a = threading.Thread(target=smile_detection, args=(4,))
        logging.info("Main    : before running thread4")
        a.start()

        a.join()
        sys.exit()
        # x.join()
        # z.join()
                

