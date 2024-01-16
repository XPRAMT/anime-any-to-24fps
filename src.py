import numpy as np
from fractions import Fraction
from operator import itemgetter
import ffmpeg
from joblib import Parallel, delayed
import multiprocessing
num_cores = multiprocessing.cpu_count() - 2
################################
frate = ''
width = ''
height = ''
num_frames = ''
Remove_frames = []
Even = 1
input_args = {
    "hwaccel": "nvdec",
}
output_args = {
    "vcodec": "hevc_nvenc",     # 使用 hevc_nvenc 編碼器進行 HEVC 編碼
    "preset": "medium",         # 選擇適當的預設，例如 "slow"
    "profile:v": "main10",      # 選擇 10 位色深的主要配置
    "pix_fmt": "p010le",        # 設置像素格式為 10 位 yuv420p
    "rc-lookahead": 16,         # 設置編碼器的預測深度
    "cq": 20,                   # 設置 CQP 模式的量化參數（QP）
}

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
    if 'color_space' in v_stream:
        output_args["color_transfer"] = v_stream.get('color_transfer')
    if 'color_space' in v_stream:
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
    
def Remove(decoder):#30->24
    global Even,frate,width,height,num_frames,colors
    encoder = (
        ffmpeg
        .input('pipe:', framerate='{}'.format(frate), format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(width,height))
        .output('output.mkv',**output_args)
        .overwrite_output()
        .run_async(pipe_stdin=True)
        )

    s=np.zeros((5,2))#索引,相似度
    in_bytes = decoder.stdout.read(width * height * 3)
    img0 = (np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3]))
    imglist=[]
    imglist.append(img0)
    for i in range(1,num_frames):
        #讀取圖片
        in_bytes = decoder.stdout.read(width * height * 3)
        frame = (np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3]))
        if(i%Even==0):
            imglist.append(frame)

        if(i%(5*Even)==0):
            imglist=np.array(imglist)
            write_frames=np.array([0,1,2,3,4])
            #比較圖片
            def compute_similarity(j):
                nonlocal imglist
                return ImageSimilarity(imglist[j], imglist[j + 1])
            result = Parallel(n_jobs=num_cores)(delayed(compute_similarity)(i) for i in range(5))
            for j in range(5):
                s[j,0] = j
                s[j,1] = result[j]
            #排序
            s2 = sorted(s,key = itemgetter(1))
            s2 = np.array(s2,dtype=int)
            print(s2)
            write_frames = write_frames[write_frames != s2[0,0]]
            #寫入
            for index in write_frames:
                encoder.stdin.write(
                            imglist[index]
                            .astype(np.uint8)
                            .tobytes()
                        )
            #顯示狀態
            realindex = i + write_frames*Even
            print(f'{i} in {num_frames} |保存:{realindex}')
            temp=imglist[5]
            imglist=[]
            imglist.append(temp)
        
    encoder.stdin.close()
        

##############Main##############
def Main(path):
    global frate,Remove_frames,num_frames,Even
    decoder = (
        ffmpeg.input(path,**input_args)
        .output('pipe:', format='rawvideo', pix_fmt='rgb24', vframes=num_frames)
        .run_async(pipe_stdout=True)
    )

    if (59<frate<61):
        Even = 2
        frate /= 2

    if (29<frate<31):
        frate = frate*4/5
        Remove(decoder)
    else:
        print("不需要處理")

    
