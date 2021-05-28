from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import cv2
import time
import numpy as np
from predict import predictImage,get_output_layers

from database.models import Model_predict

def index(request):
    """
        Arg:
            request:receive request from browser
        Return:
            render request,'index.html',context
                (context:
                    filePathName is name of input image
                    name_img is name of output image
                )
    """
    context={'a':1}
    return render(request,'index.html',context)


def predict(request):
    """
            Arg:
                request:receive request from browser
            Return:
                render request,'index.html',context
                (context:
                    filePathName is name of input image
                    name_img is name of output image
                )
    """
    classes = None

    with open('./models/yolov4.txt', 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

    session = predictImage.predict_Image()
    testimage = session.get_url_img(request)
    img = testimage

    image = cv2.imread(testimage)

    Width = image.shape[1]
    Height = image.shape[0]
    scale = 0.00392


    net = cv2.dnn.readNet('./models/yolov4.weights', './models/yolov4.cfg')

    blob = cv2.dnn.blobFromImage(image, scale, (416, 416), (0, 0, 0), True, crop=False)

    net.setInput(blob)
    
    outs = net.forward(get_output_layers.get_output_layers(net))

    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = 0.5
    nms_threshold = 0.4

    # Thực hiện xác định bằng HOG và SVM
    start = time.time()

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        session.draw_prediction(classes,COLORS,image, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h))
    name_img = testimage[:-4] + '_predict.jpg'
    cv2.imwrite(name_img, image)
    img_predict = name_img
    model = Model_predict(img=img, img_predict = img_predict)
    model.save()
    context={'filePathName':testimage[1:],'name_img':name_img}
    return render(request,'index.html',context)