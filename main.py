#!/usr/bin/env python
#
# Project: Video Streaming with Flask
# Author: Log0 <im [dot] ckieric [at] gmail [dot] com>
# Date: 2014/12/21
# Website: http://www.chioka.in/
# Description:
# Modified to support streaming out with webcams, and not just raw JPEGs.
# Most of the code credits to Miguel Grinberg, except that I made a small tweak. Thanks!
# Credits: http://blog.miguelgrinberg.com/post/video-streaming-with-flask
#
# Usage:
# 1. Install Python dependencies: cv2, flask. (wish that pip install works like a charm)
# 2. Run "python main.py".
# 3. Navigate the browser to the local webpage.
from flask import Flask, render_template, Response,request,jsonify
from camera import VideoCamera
import main_dlib
import cv2
import numpy as np
from PIL import Image

import re,io
from io import StringIO 

import base64
import json
app = Flask(__name__)

@app.route('/')
def index():

    return render_template('index.html',base_url =request.base_url)

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/process_image/', methods=['POST'])
def process() :
 
    if request.method == "POST":
        image_b64 = request.values['imageBase64']
        opt = int(request.values['option'])

        imgstr = re.sub('^data:image/.+;base64,', '', image_b64)
        image_bytes = io.BytesIO(base64.b64decode(imgstr))
        im = Image.open(image_bytes)
        arr = np.array(im)

        
        print ('Image received: {}'.format(arr.shape),' Option : ',opt)
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        
        arr=main_dlib.main(arr,opt)

        ret, jpeg = cv2.imencode('.jpg', arr)
        conv = base64.b64encode(jpeg)
          
    return  conv

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)


# arr=cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
#image = request.args.get('image', default = 0, type = np.uint8)
#image = request.args.get('opt', default = 0, type = int)
#json = request.get_json()
#print(image_b64)
#.decode('base64')
#imgstr = re.search(r'base64,(.*)', image_b64).group(1)
# image_data =base64.b64decode(image_data)
# print(image_data)
# image_PIL = Image.open(StringIO(image_data))
# image = np.array(image_PIL)