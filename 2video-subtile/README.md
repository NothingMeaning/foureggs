# 四知回--通过给的txt文件自动给视频文件添加配音

&#8195;&#8195;

## 功能说明

输入：
  ttt.mp4 【 要处理的mp4，不包含声音]
  ttt.txt 【 要合成的语音的，txt,每句一行】 
功能：
  将ttt.txt中的文字 自动分布到ttt.mp4的时长中，并且自动生成语音
限制:
  文件名相同，后缀不同，自动处理，其他方式要单独输入参数

输出:
  combine_all_ttt.mp3 【 语音的包 ] 
  combine_all_ttt.srt [ 字幕文件]
  combine_all_ttt.mp4 [ 包含自动语音的新mp4文件 ]

python 本脚本文件 -m mp4filename

##   文件说明
- auto-srt-speech.py 主代码函数文件

- update.ps1 powershell 脚本程序，用于重新编译出.exe文件
```
  update.ps1 .\auto-srt-speech.py
```
- release/config.ini 程序运行所需要的配置文件，主要用于配置百度云的信息

------



