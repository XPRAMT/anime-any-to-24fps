# -*- coding: utf-8 -*-
import os
import cv2
import numpy as np
from operator import itemgetter, attrgetter

def calculate(image1, image2):
    # 灰度直方圖算法
    # 計算單通道的直方圖的相似值
    hist1 = cv2.calcHist([image1], [0], None, [256], [0.0, 255.0])
    hist2 = cv2.calcHist([image2], [0], None, [256], [0.0, 255.0])
    # 計算直方圖的重合度
    degree = 0
    for i in range(len(hist1)):
        if hist1[i] != hist2[i]:
            degree = degree + \
                (1 - abs(hist1[i] - hist2[i]) / max(hist1[i], hist2[i]))
        else:
            degree = degree + 1
    degree = degree / len(hist1)
    return degree


def classify_hist_with_split(image1, image2, size=(256, 256)):
    # RGB每個通道的直方圖相似度
    # 將圖像resize後，分離爲RGB三個通道，再計算每個通道的相似值
    image1 = cv2.resize(image1, size)
    image2 = cv2.resize(image2, size)
    sub_image1 = cv2.split(image1)
    sub_image2 = cv2.split(image2)
    sub_data = 0
    for im1, im2 in zip(sub_image1, sub_image2):
        sub_data += calculate(im1, im2)
    sub_data = sub_data / 3
    return sub_data
#======================================================
path='C:/Users/XPRAMT/Downloads/A'

piclist=os.listdir(path)
s=np.zeros((5,2))
j=0
if not os.path.isdir(os.path.join(path,'move')):
    os.makedirs(os.path.join(path,'move'))

for i in range(np.size(piclist)):
    img1 = cv2.imread(os.path.join(path,piclist[i]))
    img2 = cv2.imread(os.path.join(path,piclist[i+1]))
    
    s[j,0]=i
    s[j,1]=classify_hist_with_split(img1,img2)
    
    print(piclist[i],'與',piclist[i+1],'相似度:',s[j,1])
    
    j=j+1
    if j == 5:
        j=0

        s2 = sorted(s,key = itemgetter(1),reverse = True)
        s2=np.array(s2,dtype=int)
        print('移除',piclist[s2[0,0]])
        
        src=os.path.join(path,piclist[s2[0,0]])
        des=os.path.join(path,'move',piclist[s2[0,0]])
        os.replace(src,des)

























