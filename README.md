特別對崩3動畫設計<br>
崩3動畫以24幀製作，但封裝成60幀，每個場景的重複順序還不同
導致一般方法很難移除重複幀<br>
運作方式:每5幀一組，比較每幀的相似度並排序，刪除一相似度最高的幀<br>

安裝:<br>
下載[ffmpeg](https://ffmpeg.org)<br>
解壓後將 ffmpeg.exe,ffprobe.exe 放到系統路徑<br>
python>=3.10
```
pip install -r requirements.txt
```
<br>
使用:
run.bat
輸出檔案保存在與輸入相同的資料夾<br>
可以自訂的參數:

```
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
```
