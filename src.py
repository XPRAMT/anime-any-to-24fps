import numpy as np
from fractions import Fraction
from operator import itemgetter
import ffmpeg
import os
from joblib import Parallel, delayed
############自訂參數############
num_cores = 14                  #多執行序
input_args = {
    "hwaccel": "nvdec",         #硬體解碼
}
output_args = {
    "vcodec": "hevc_nvenc",     # 使用編碼器
    "preset": "slow",           # 編碼速度:fast,medium,slow,
    "profile:v": "main10",      # 設置主要配置:main10
    "pix_fmt": "p010le",        # 設置像素格式:yuv420p,p010le
    "rc-lookahead": 16,         # 設置編碼器的預測深度
    "cq": 15,                   # 設置CQP模式的量化參數(QP)
}
pipe_fmt='yuv444p'              #rgb24,yuv444p,p010le...(rgb可能導致色彩偏移)
############全局參數############
OutputName = ''     
frate = ''
width = ''
height = ''
num_frames = ''
Even = 1
##############函式##############
def GetVideoInfo(VieoPath):
    global frate,width,height,num_frames,colors
    probe = ffmpeg.probe(VieoPath)
    v_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(v_stream['width'])
    height = int(v_stream['height'])
    frate = float(Fraction(v_stream['avg_frame_rate']))
    num_frames = int(v_stream.get('nb_frames',0))
    if num_frames == 0:
        tags = v_stream.get('tags', {})
        num_frames = int(tags.get('NUMBER_OF_FRAMES', 0))
    if 'color_space' in v_stream:
        output_args["colorspace"] = v_stream.get('color_space')
    if 'color_transfer' in v_stream:
        output_args["color_trc"] = v_stream.get('color_transfer')
    if 'color_primaries' in v_stream:
        output_args["color_primaries"] = v_stream.get('color_primaries')
    print("-----------input-----------")
    print(v_stream)
    print("-----------output-----------")
    print(output_args)
    return frate

def ImageSimilarity(image1, image2):
    Difference = abs(image2 - image1)
    degree = np.mean(Difference)
    return degree
    
def Remove(video,audio):#30->24
    global Even,frate,width,height,num_frames,OutputName
    encoder = (
        ffmpeg
        .input('pipe:', framerate='{}'.format(frate), format='rawvideo', pix_fmt=pipe_fmt, s='{}x{}'.format(width,height))
        .output(audio,OutputName,**output_args)
        .overwrite_output()
        .run_async(pipe_stdin=True)
        )

    s=np.zeros((5,2))#索引,相似度
    in_bytes = video.stdout.read(width * height * 3)#讀取第0幀
    img0 = np.frombuffer(in_bytes, np.uint8)
    imglist=[]#圖片序列
    imglist.append(img0)
    write_frames=[]#寫入清單
    k=0
    for i in range(1,num_frames):
        #讀取圖片
        in_bytes = video.stdout.read(width * height * 3)
        frame = np.frombuffer(in_bytes, np.uint8)
        #寫入圖片序列
        if(i%Even==0):
            write_frames.append(k)
            imglist.append(frame)
            k+=1
        #比較排序圖片
        if(i%(5*Even)==0):
            imglist=np.array(imglist)
            #比較圖片
            def compute_similarity(j):
                nonlocal imglist
                return ImageSimilarity(imglist[j], imglist[j + 1])
            result = Parallel(num_cores)(delayed(compute_similarity)(i) for i in range(5))
            for j in range(5):
                s[j,0] = j
                s[j,1] = result[j]
            #排序
            s2 = sorted(s,key = itemgetter(1))
            s2 = np.array(s2,dtype=int)
            #從寫入清單移除
            write_frames.remove(s2[0,0])
            Remove_frame = i + s2[0,0]*Even
        #寫入
        if(i%(5*Even)==0) or (i==num_frames):
            write_frames=np.array(write_frames)
            for index in write_frames:
                encoder.stdin.write(
                            imglist[index]
                            .astype(np.uint8)
                            .tobytes()
                        )
            #顯示狀態
            realindex = i + write_frames*Even
            print(f'{i} in {num_frames} |移除幀:{Remove_frame} |保存幀:{realindex}')
            #重置
            if(i!=num_frames):
                temp=imglist[5]
                imglist=[]
                imglist.append(temp)
                write_frames=[]
                Remove_frame='None'
                k=0
        
    encoder.stdin.close() #關閉影片流
        
##############Main##############
def Main(path):
    global frate,num_frames,Even,OutputName
    #取得輸出檔名
    fileName, _ = os.path.splitext(os.path.basename(path))
    OutputName = f"{fileName}_fix{'.mkv'}"
    #分離影片聲音流
    input=ffmpeg.input(path,**input_args)
    video = (
        input
        .output('pipe:', format='rawvideo', pix_fmt=pipe_fmt, vframes=num_frames)
        .run_async(pipe_stdout=True)
    )
    audio = input.audio
    
    if (59<frate<61):
        Even = 2
        frate /= 2

    if (29<frate<31):
        frate = frate*4/5
        Remove(video,audio)
    elif(23<frate<25):
        print("不需要處理")
    else:
        print("例外情況")

    print("處理完成!")