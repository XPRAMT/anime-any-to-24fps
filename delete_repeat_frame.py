import os
import cv2
import numpy as np
from operator import itemgetter, attrgetter

#路徑(資料夾)
path=r'C:\Users\XPRAMT\Downloads\AI繪圖'
#幀數(30or60)
frate=30

##############函式##############
def ImageSimilarity(image1, image2):
    # RGB每個通道的直方圖相似度
    # 分離爲RGB三個通道，再計算每個通道的相似值
    sub_image1 = cv2.split(image1)
    sub_image2 = cv2.split(image2)
    sub_data = 0
    for im1, im2 in zip(sub_image1, sub_image2):
        sub_data += calculate(im1, im2)
    sub_data = sub_data / 3
    return sub_data
    
def move_even():
    piclist=os.listdir(path)
    #建立move_even資料夾
    if not os.path.isdir(os.path.join(path,'move_even')):
        os.makedirs(os.path.join(path,'move_even'))
        #移除偶數幀
        j=0
        for i in range(np.size(piclist)):
            j=j+1
            if j == 2:
                j=0
                src=os.path.join(path,piclist[i])
                des=os.path.join(path,'move',piclist[i])
                os.replace(src,des)
                
def move():
    piclist=os.listdir(path)
    s=np.zeros((5,2))

    #建立move資料夾
    if not os.path.isdir(os.path.join(path,'move')):
        os.makedirs(os.path.join(path,'move'))
    #30->24
    j=0
    for i in range(np.size(piclist)):
        img1 = cv2.imread(os.path.join(path,piclist[i]))
        img2 = cv2.imread(os.path.join(path,piclist[i+1]))
    
        s[j,0]=i
        s[j,1]=ImageSimilarity(img1,img2)
    
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
            
##############Main##############
if frate == 60:
    print('移除偶數幀')
    move_even()
    frate = 30

if frate == 30:
    print('30幀>24幀')
    move()












