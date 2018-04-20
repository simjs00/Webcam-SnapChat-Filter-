from tkinter import *
from PIL import Image
from PIL import ImageTk
import cv2, threading, os, time
from threading import Thread
from os import listdir
from os.path import isfile, join

import dlib
from imutils import face_utils, rotate_bound
import math


#Filters path

detector = dlib.get_frontal_face_detector()
#Facial landmarks

model = "./filters/shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(model) # link to model: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
print("[INFO] loading facial landmark predictor...")



# Draws sprite over a image
# It uses the alpha chanel to see which pixels need to be reeplaced
# Input: image, sprite: numpy arrays
# output: resulting merged image
def draw_sprite(frame, sprite, x_offset, y_offset):
    (h,w) = (sprite.shape[0], sprite.shape[1])
    (imgH,imgW) = (frame.shape[0], frame.shape[1])

    if y_offset+h >= imgH: #if sprite gets out of image in the bottom
        sprite = sprite[0:imgH-y_offset,:,:]

    if x_offset+w >= imgW: #if sprite gets out of image to the right
        sprite = sprite[:,0:imgW-x_offset,:]

    if x_offset < 0: #if sprite gets out of image to the left
        sprite = sprite[:,abs(x_offset)::,:]
        w = sprite.shape[1]
        x_offset = 0

    #for each RGB chanel
    for c in range(3):
            #chanel 4 is alpha: 255 is not transpartne, 0 is transparent background
            frame[y_offset:y_offset+h, x_offset:x_offset+w, c] =  \
            sprite[:,:,c] * (sprite[:,:,3]/255.0) +  frame[y_offset:y_offset+h, x_offset:x_offset+w, c] * (1.0 - sprite[:,:,3]/255.0)
    return frame

#Adjust the given sprite to the head's width and position
#in case of the sprite not fitting the screen in the top, the sprite should be trimed
def adjust_sprite2head(sprite, head_width, head_ypos, ontop = True):
    (h_sprite,w_sprite) = (sprite.shape[0], sprite.shape[1])
    factor = 1.0*head_width/w_sprite
    sprite = cv2.resize(sprite, (0,0), fx=factor, fy=factor) # adjust to have the same width as head
    (h_sprite,w_sprite) = (sprite.shape[0], sprite.shape[1])

    y_orig =  head_ypos-h_sprite if ontop else head_ypos # adjust the position of sprite to end where the head begins
    if (y_orig < 0): #check if the head is not to close to the top of the image and the sprite would not fit in the screen
            sprite = sprite[abs(y_orig)::,:,:] #in that case, we cut the sprite
            y_orig = 0 #the sprite then begins at the top of the image
    return (sprite, y_orig)

# Applies sprite to image detected face's coordinates and adjust it to head
def apply_sprite(image, path2sprite,w,x,y, angle, ontop = True):
    sprite = cv2.imread(path2sprite,-1)
    #print sprite.shape
    sprite = rotate_bound(sprite, angle)
    (sprite, y_final) = adjust_sprite2head(sprite, w, y, ontop)
    image = draw_sprite(image,sprite,x, y_final)
    return image
#points are tuples in the form (x,y)
# returns angle between points in degrees
def calculate_inclination(point1, point2):
    x1,x2,y1,y2 = point1[0], point2[0], point1[1], point2[1]
    incl = 180/math.pi*math.atan((float(y2-y1))/(x2-x1))
    return incl


def calculate_boundbox(list_coordinates):
    x = min(list_coordinates[:,0])
    y = min(list_coordinates[:,1])
    w = max(list_coordinates[:,0]) - x
    h = max(list_coordinates[:,1]) - y
    return (x,y,w,h)

def get_face_boundbox(points, face_part):
    if face_part == 1:
        (x,y,w,h) = calculate_boundbox(points[17:22]) #left eyebrow
    elif face_part == 2:
        (x,y,w,h) = calculate_boundbox(points[22:27]) #right eyebrow
    elif face_part == 3:
        (x,y,w,h) = calculate_boundbox(points[36:42]) #left eye
    elif face_part == 4:
        (x,y,w,h) = calculate_boundbox(points[42:48]) #right eye
    elif face_part == 5:
        (x,y,w,h) = calculate_boundbox(points[29:36]) #nose
    elif face_part == 6:
        (x,y,w,h) = calculate_boundbox(points[48:68]) #mouth
    return (x,y,w,h)


#Principal Loop where openCV (magic) ocurs
def main(image,opt):

        dir_ = "./sprites/flyes/"
        flies = [f for f in listdir(dir_) if isfile(join(dir_, f))] #image of flies to make the "animation"
        i = 0
        video_capture = cv2.VideoCapture(0) #read from webcam
        (x,y,w,h) = (0,0,10,10) #whatever initial values

 

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)

        for face in faces: #if there are faces
            print("Loop")
            (x,y,w,h) = (face.left(), face.top(), face.width(), face.height())
            # *** Facial Landmarks detection
            shape = predictor(gray, face)
            shape = face_utils.shape_to_np(shape)
            incl = calculate_inclination(shape[17], shape[26]) #inclination based on eyebrows

            # condition to see if mouth is open
            is_mouth_open = (shape[66][1] -shape[62][1]) >= 10 #y coordiantes of landmark points of lips

            #hat condition
            if (opt==1):
               print("hat")
               image= apply_sprite(image, "./sprites/hat.png",w,x,y, incl)

            #mustache condition
            elif (opt==2):
                print("mouth")
                (x1,y1,w1,h1) = get_face_boundbox(shape, 6)
                image=apply_sprite(image, "./sprites/mustache.png",w1,x1,y1, incl)

            #glasses condition
            elif (opt==3):
                (x3,y3,_,h3) = get_face_boundbox(shape, 1)
                image=apply_sprite(image, "./sprites/glasses.png",w,x,y3, incl, ontop = False)

            #flies condition
            elif (opt==4):
                #to make the "animation" we read each time a different image of that folder
                # the images are placed in the correct order to give the animation impresion
                image= apply_sprite(image, dir_+flies[i],w,x,y, incl)
                i+=1
                i = 0 if i >= len(flies) else i #when done with all images of that folder, begin again

            #doggy condition
           
            elif (opt==5):
                (x0,y0,w0,h0) = get_face_boundbox(shape, 6) #bound box of mouth
                (x3,y3,w3,h3) = get_face_boundbox(shape, 5) #nose
                image=apply_sprite(image, "./sprites/doggy_nose.png",w3,x3,y3, incl, ontop = False)

                image=apply_sprite(image, "./sprites/doggy_ears.png",w,x,y, incl)

                if is_mouth_open:
                   image=apply_sprite(image, "./sprites/doggy_tongue.png",w0,x0,y0, incl, ontop = False)
            elif (opt==6):
                (x0,y0,w0,h0) = get_face_boundbox(shape, 6) #bound box of mouth
                if is_mouth_open:
                    image=apply_sprite(image, "./sprites/rainbow.png",w0,x0,y0, incl, ontop = False)
        


        return image


