import face_recognition
import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
import pandas as pd
import os
import csv

import time
import threading
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    event = CameraEvent()

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            # start background frame thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()

        # wait for a signal from the camera thread
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        return BaseCamera.frame

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def _thread(cls):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame = frame
            BaseCamera.event.set()  # send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()
                print('Stopping camera thread due to inactivity.')
                break
        BaseCamera.thread = None




class Camera_compare(BaseCamera):
    video_source = 0
    last_encoding = []
    encodings_core = {}
    encodings_few = {}
    enc_reset_cnt = 0
    enc_reset_cnt_lim = 20
    enc_add_to_core_cnt_lim = 10
    few_id_cnt = 0
    name_dict = {}
    
    def get_names_dict(file_name):
        with open(file_name, mode='r') as infile:
            reader = csv.reader(infile)
            #structure 0-ID 1-Name
            next(reader, None) 
            name_dict = {int(rows[0]):rows[1] for rows in reader}
            print(name_dict)
        return name_dict

    #some logic to upadte user names dict
    def update_name_dict(filename):
        if Camera_compare.enc_reset_cnt == 0:
            Camera_compare.name_dict = Camera_compare.get_names_dict(filename)

    
    @staticmethod
    def set_video_source(source):
        Camera_compare.video_source = source

    def get_name(encoding):
        name = "Undefined"
        found_likeness=0
        if bool(Camera_compare.encodings_core):
            for key, value in Camera_compare.encodings_core.items():
                if any(face_recognition.compare_faces(value, encoding, tolerance = 0.5)):
                    try:
                        print("key found")
                        name = Camera_compare.name_dict[key]
                    except KeyError:
                        name = str(key)
                    print("Found likeness in core, name = %s"%name)
                    found_likeness = 1
                    break
        if not found_likeness:
            print("No likeness found in core, name = %s"%name)
        return name     

    def add_to_core(key,encodings):
        #next key
        num = len(Camera_compare.encodings_core)
        exist_in_core = 0
        
        #transform incoming encodings --> averaging
        encoding = list(np.average(encodings,axis = 0))
        
        if bool(Camera_compare.encodings_core):
            for key, value in Camera_compare.encodings_core.items():
                if any(face_recognition.compare_faces(value, encoding, tolerance = 0.5)):
                    #encoding already exist in core
                    exist_in_core +=1  
        
        if exist_in_core==0:
            ##add new encoding to core
            Camera_compare.encodings_core[num] = [encoding]    
        
        print("Adding to core with id = %s"%num)

    def reset_few():
        #reset few buffer
        if Camera_compare.enc_reset_cnt >= Camera_compare.enc_reset_cnt_lim:
            Camera_compare.encodings_few = {}
            Camera_compare.enc_reset_cnt = 0
            Camera_compare.few_id_cnt = 0
            print("reset counter reached, clearing encodings_few")
        Camera_compare.enc_reset_cnt+=1
    
    def print_few_struct():
        #Printout
        printout_text = "Encoding few structure: \n"
        if len(Camera_compare.encodings_few):
            for key, value in Camera_compare.encodings_few.items():
                printout_text = "%s node '%s', length %s;  \n"%(printout_text,key,len(Camera_compare.encodings_few[key]))
        else:
            printout_text = "%s -- none --"%printout_text   
        print(printout_text) 
        
    def add_to_few(encoding):

        if bool(Camera_compare.encodings_few):
            likehood_counter = 0
            merge_dict = {}
            max_likeness_cnt = -1
            full_dict = {}

            #Camera_compare.print_few_struct()
            for key, value in Camera_compare.encodings_few.items():
                #check maximum numbers of likeness encoding for each ID
                if len(value)>=Camera_compare.enc_add_to_core_cnt_lim:
                    full_dict[len(full_dict)]=key
                    continue
                    
                #check encodings few base
                if any(face_recognition.compare_faces(value, encoding, tolerance = 0.2)):
                    print(face_recognition.compare_faces(value, encoding, tolerance = 0.2))
                    if likehood_counter > 0:
                        merge_dict[merge_num_0]=key
                    else:
                        print("Appending likeness to encodings_few node '%s', likehood_counter=%s"%(key,likehood_counter+1))
                        #do not add to merging nodes
                        Camera_compare.encodings_few[key].append(encoding)
                        merge_num_0 = key
                    likehood_counter += 1
            

            #adding new likeness node to few base
            if likehood_counter == 0:
                Camera_compare.encodings_few[Camera_compare.few_id_cnt]=[encoding] 
                print("No likeness found in few, creating new node %s"%Camera_compare.few_id_cnt)
                Camera_compare.few_id_cnt =+ 1
   
            #merging two likeness nodes
            if bool(merge_dict):
                print("Similar nodes found, merging dict is: %s"%merge_dict)
                for key, value in merge_dict.items():
                    Camera_compare.encodings_few[key].extend(Camera_compare.encodings_few.pop(value))
      
            #add full node to core
            if bool(full_dict):
                for key, value in full_dict.items():
                    print("few node %s is full"%value)
                    Camera_compare.add_to_core(key, Camera_compare.encodings_few[value])
                    Camera_compare.encodings_few.pop(value)
 
            
            Camera_compare.print_few_struct()
           
        
        else:
            print("Encodings_few is empty, adding first node")
            Camera_compare.encodings_few[len(Camera_compare.encodings_few)]=[encoding]
                
    @staticmethod
    def frames():
        camera = cv2.VideoCapture(Camera_compare.video_source)
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, frame = camera.read()

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_frame = frame[:, :, ::-1]

            # Find all the faces and face enqcodings in the frame of video
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            # Loop through each face in this frame of video
            face_iter = 0
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                
                print("--------------->")
                
                #udate name dictionary
                Camera_compare.update_name_dict('dict.csv')
                
                #clear few buffer time to time
                Camera_compare.reset_few()
                
                #check new encoding
                Camera_compare.add_to_few(face_encoding)
                
                # See if the face is a match for the known face(s)
                name = Camera_compare.get_name(face_encoding)
        
                face_iter += 1
  
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                
            #for face_landmarks in face_landmarks_list:
            #    pil_image = Image.fromarray(frame)
            #    d = ImageDraw.Draw(pil_image, 'RGBA')
            #    # Make the eyebrows into a nightmare
            #    print(face_landmarks['left_eyebrow'])
            #    d.polygon(face_landmarks['left_eyebrow'], fill=(68, 54, 39, 128))
            #    d.polygon(face_landmarks['right_eyebrow'], fill=(68, 54, 39, 128))
            #    frame = numpy.array(pil_image.getdata(),
            #        numpy.uint8).reshape(pil_image.size[1], pil_image.size[0], 3)


            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', frame)[1].tobytes()  #this for app
            #yield frame  #this for notebook jupyter
            
