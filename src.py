from fractions import Fraction
from operator import itemgetter
import concurrent.futures
import numpy as np
import ffmpeg
import time
import copy
import os
############自訂參數############
input_args = {
    "hwaccel": "nvdec",         #硬體解碼
}
defual_output_args = {
    "c:a": "copy",              # 複製音訊流
    "vcodec": "hevc_nvenc",     # 使用編碼器
    "preset": "slow",           # 編碼速度:fast,medium,slow,
    "profile:v": "main10",      # 設置主要配置:main10
    "pix_fmt": "p010le",        # 設置像素格式:yuv420p,p010le
    "rc-lookahead": 16,         # 設置編碼器的預測深度
    "cq": 15,                   # 設置CQP模式的量化參數(QP)
}
pipe_fmt='yuv444p'              #rgb24,yuv444p,p010le...(rgb可能導致色彩偏移)
##############函式##############
isStop = False
isPause = False
# 強制停止
def Stop(process_queue,state_queue,All):
    global isStop
    if All:
        while not process_queue.empty():
            parameter = process_queue.get()
            #返回結束狀態
            parameter.append(2)
            state_queue.put(parameter)
    isStop = True
# 暫停
def Pause(Pause):
    global isPause
    isPause = Pause

# 取得影片資訊
def GetVideoInfo(VieoPath):
    global defual_output_args,print_info
    output_args = copy.deepcopy(defual_output_args)
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
    return frate,num_frames,width,height,output_args

def compare_sort_write(parameters):
    encoder,imglist,write_frames,i2,num_frames,Even,state_queue = parameters
    num_list=len(write_frames)
    i1=i2-num_list*Even
    #如果不足5幀補一幀
    if num_list<5:
        write_frames.append(write_frames[-1]+1)
        imglist.append(np.zeros_like(imglist[0]))
    s = np.zeros((num_list, 2))#索引,相似度
    imglist=np.array(imglist)
    #比較圖片
    def ImageSimilarity(image1, image2):
        Difference = abs(image2 - image1)
        degree = np.mean(Difference)
        return degree
    for j in range(num_list):
        s[j,0] = j
        s[j,1] = ImageSimilarity(imglist[j], imglist[j + 1])
    #排序
    s2 = sorted(s,key = itemgetter(1))
    s2 = np.array(s2,dtype=int)
    #從寫入清單移除
    write_frames.remove(s2[0,0])
    Remove_frame = i1 + s2[0,0]*Even
    #寫入
    write_frames=np.array(write_frames)
    for index in write_frames:
        encoder.stdin.write(imglist[index].astype(np.uint16).tobytes())
    #顯示狀態
    realindex = i1 + write_frames*Even
    state=[None,(f'處理幀:{i1}~{i2} in {num_frames} -[{Remove_frame}] +{realindex}'),3]
    state_queue.put(state)

def Remove(video,encoder,width,height,num_frames,Even,state_queue):#30->24
    global isStop,isPause
    in_bytes = video.stdout.read(width * height * 3)#讀取第0幀
    img1 = np.frombuffer(in_bytes, np.uint16)
    imglist=[]#圖片序列
    imglist.append(img1)
    write_frames=[]#寫入清單
    read_frame=''
    i=2
    k=0
    last_frame = False
    with concurrent.futures.ThreadPoolExecutor() as executor:
        threads = []
        while not last_frame:         #for i in range(2,num_frames+1):
            #讀取圖片
            in_bytes = video.stdout.read(width * height * 3)
            if len(in_bytes) == 0:
                last_frame = True
            elif (i%Even==1):
                #寫入圖片序列
                frame = np.frombuffer(in_bytes, np.uint16)
                write_frames.append(k)
                imglist.append(frame)
                read_frame=i
                k+=1
            #比較 排序 寫入
            if(k==5) or last_frame:
                parameters = encoder,imglist,write_frames,read_frame,num_frames,Even,state_queue
                t = executor.submit(compare_sort_write, parameters)
                threads.append(t)
                #重置
                if not last_frame:
                    imglist = [imglist[5]]
                    write_frames=[]
                    k=0

            # 暫停
            while isPause and not isStop:
                time.sleep(0.1)
            # 強制停止
            if isStop:
                isStop = False
                break
            i+=1
        # 等待所有執行緒結束
        concurrent.futures.wait(threads)
    #關閉影片流
    encoder.stdin.close()
       
##############Main##############
def Main(process_queue,state_queue):
    global print_info,isStop
    while (True):
        parameter = process_queue.get()#等待任務
        parameter.append(1)
        state_queue.put(parameter) #返回處理狀態
        isStop = False
        #取得輸出檔名
        path = parameter[1]
        fileName, _ = os.path.splitext(path)
        OutputName = f"{fileName}_fix{'.mkv'}"
        #取得影片資訊
        frate,num_frames,width,height,output_args = GetVideoInfo(path)
        #分離影片聲音流
        input=ffmpeg.input(path,**input_args)
        video = (
            input
            .output('pipe:', format='rawvideo', pix_fmt=pipe_fmt)
            .run_async(pipe_stdout=True)
        )
        audio = input.audio

        Even = 1
        if (59<frate<61):
            Even = 2
            frate /= 2
        if (29<frate<31):
            frate = frate*4/5
            #建立編碼器
            encoder = (
                ffmpeg
                .input('pipe:', framerate='{}'.format(frate)
                        , format='rawvideo', pix_fmt=pipe_fmt
                        , s='{}x{}'.format(width,height)
                        ,thread_queue_size=128,)
                .output(audio,OutputName,**output_args)
                .overwrite_output()
                .run_async(pipe_stdin=True)
                )
            Remove(video,encoder,width,height,num_frames,Even,state_queue)
            state=[None,f'處理完成! | 幀率:{frate:.3f}',3]
        elif(23<frate<25):
            state=[None,f'不需要處理 | 幀率:{frate:.3f}',3]
        else:
            state=[None,f'例外情況 | 幀率:{frate:.3f}',3]
        state_queue.put(state)
        #返回結束狀態
        parameter[2] = 2
        state_queue.put(parameter)



