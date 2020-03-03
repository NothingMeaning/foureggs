#coding:utf-8
"""

输入：
  ttt.mp4 【 要处理的mp4，不包含声音]
  ttt.txt 【 要合成的语音的，txt】 
功能：
  将ttt.txt中的文字 自动分布到ttt.mp4的时长中，并且自动生成语音
限制:
  文件名相同，后缀不同，自动处理，其他方式要单独输入参数

输出:
  combine_all_ttt.mp3 【 语音的包 ] 
  combine_all_ttt.srt [ 字幕文件]
  combine_all_ttt.mp4 [ 包含自动语音的新mp4文件 ]

python 本脚本文件 -m mp4filename

"""

import re
import os
import sys
import time
import shutil
import sys, getopt
import six
# from moviepy.editor import VideoFileClip
if six.PY2:
    import ConfigParser as configparser
else:
    import configparser

# import ffmpeg
import datetime
from shutil import copyfile
from aip import AipSpeech
from pydub import AudioSegment
from moviepy.editor import * 
import moviepy.video.tools.cuts as cuts
from moviepy.utils import close_all_clips
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.tools.subtitles import SubtitlesClip, file_to_subtitles
from moviepy.video.VideoClip import ColorClip, TextClip
import srt

list_gap=[]
list_item=[]
list_delay=[]
num_cha=0
num_itm=0
MY_APPID="TEST1234567891111"

class ItemLine:
  def __init__(self,txt,seq=0,start=None,end=None,offset=0,audio=None):
    self.txt=txt
    self.cha=len(txt)
    self.seq=seq
    self.start=start
    self.end=end
    self.audio=audio
    self.offset=offset
    self.pit=180
    self.speed=0

  def set_txt(self,txt):
    self.txt=txt
    self.cha=len(self.txt)
  def set_time(self,start,end,speed):
    self.start=start
    self.end=end
    self.speed=speed
  def set_audio(self,audio):
    self.audio=audio
  def set_offset(self,offset):
    self.offset=offset

def final_out(reason):
  print("Command failed by ",reason)
  os.system('pause')
  sys.exit(reason)

def read_text_srt(txtfile):
  global list_delay
  global list_gap
  global list_item
  global num_itm
  global num_cha
  lcnt=0
  with open(txtfile, "r",encoding='utf-8') as fh: 
    lines=fh.readlines()  #使用readlines()函数 读取文件的全部内容，存成一个列表，每一项都是以换行符结尾的一个字符串，对应着文件的一行

    for line in lines:     #开始进行处理 把第一列存到list_name 第二列存到list_scores,,,,,
      lcnt = lcnt + 1
      if line.startswith('#') :
        continue
      if len(line) <= 3:
        print("Line {} content {} too short".format(lcnt,line))
        continue
      if line.startswith("GAP"):
        list_gap.append(line)
      if line.startswith("DELAY"):
        list_delay.append(line)
      num_cha+=len(line)
      thisitem=ItemLine(line,seq=lcnt)
      list_item.append(thisitem)
      num_itm  = num_itm + 1

  print("File {},GAP {} Delay {}, Line {}".format(
    lcnt,len(list_gap),len(list_delay),len(list_item)))

# t = datetime.time(1, 10, 20, 13)
def create_one_item_srt(fh,seq,start,end,line):
  fh.write("{}\n".format(seq))
  # 00:00:02,000 --> 00:00:05,000
  fh.write("{:02d}:{:02d}:{:02d},{:03d} --> {:02d}:{:02d}:{:02d},{:03d}\n".format(
    start.hour,start.minute,start.second,int(start.microsecond/1000),
    end.hour,end.minute,end.second,int(end.microsecond/1000)))
  # fh.write("{} --> {}}".format(
  #   start.strftime("%H:%M:%S,,start.minute,start.second,start.microsecond,
  #   end.hour,end.minute,end.second,end.microsecond))
  fh.write(line)
  if not line.endswith('\n'):
    fh.write("\n")
  fh.write("\n")

# def time_plus(time, timedelta):
#   start = datetime.datetime(
#       2000, 1, 1,
#       hour=time.hour, minute=time.minute, second=time.second,microseconds=time.microseconds)
#   end = start + timedelta
#   return end.time()

def convert_txt_to_srt(txtfile,srtfile) :
  global VideoLen
  global num_cha
  gaplen=0
  # ftxt=open(txtfile, "r",encoding='utf-8')
  fsrt=open(srtfile, "w",encoding='utf-8')
  if fsrt is None:
    print("Open file failed")
    return

  # Ref 180 - 360 character/minute = 3 - 6 char perl second,each word use 333 ms - 125ms
  # 1000/
  avg_speed=int(1000*VideoLen/num_cha)
  if avg_speed <= 185 :
    print("每秒钟字数{}/{}/{}太多了 远超过一般的，要做修改，参考范围180-320".format(avg_speed,
      VideoLen,num_cha))
    tk=int(1000*VideoLen/185)
    print("大约还需要裁剪{}个字".format(num_cha-tk))
    return

  if avg_speed >= 335 :
    tk=int(1000*VideoLen/260)
    print("目前内容较少，还可以补充完善哦，大约还可以补充{}个字".format(tk-num_cha))
    avg_speed = 260
    # In ms
    gaplen=int((VideoLen*1000 - avg_speed*num_cha)/num_itm)

  print("Line {} Char {}  AVG {} dur {} GAP {}".format(num_itm,
    num_cha,avg_speed,VideoLen,gaplen))

  tstart = datetime.datetime(2000,1,1,
    0, 0, 0, 500000)
  seq = 1
  # lines = ftxt.readlines() 
  for itm in list_item:
    ldur=len(itm.txt)*avg_speed
    print("Line {},dur {}".format(seq,ldur))
    tend=tstart+datetime.timedelta(milliseconds=ldur)
    itm.set_time(tstart,tend,avg_speed)
    create_one_item_srt(fsrt,seq,tstart,tend,itm.txt)
    tstart=tend
    seq = seq + 1
    if gaplen:
      tstart = tstart + datetime.timedelta(milliseconds=gaplen)
  
  fsrt.close()

def convert_txt_to_speech_baidu(tpath):
  global baidu_client,VOL,PER,QPS,PIT,SPD,pureName
  bpath=tpath
  for itm in list_item:
    aname="audio_"+pureName+"_"+"{:02d}".format(itm.start.second)+"{:03d}".format(int(itm.start.microsecond/1000))+".mp3"
    aname=os.path.join(tpath,aname)
    tnow=time.time()
    print("Convert {} time {} name {} start {}:{}".format(itm.txt,tnow,aname,
      itm.start.second,itm.start.microsecond))
    fname=os.path.join(bpath,aname)
    if os.path.isfile(fname) :
      print("Load {} audio".format(fname))
      itm.set_audio(fname)
    else:
      result  = baidu_client.synthesis(itm.txt, 'zh', 1, {
          'vol': VOL,
          'per': PER,
          'pit': PIT,
          'spd': SPD
      })
      # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
      if not isinstance(result, dict):
        with open(aname, 'wb') as f:
          f.write(result)
        itm.set_audio(aname)
        nnow=time.time()
        rdelta=(nnow-tnow)
        if rdelta >0 :
          if rdelta < QPS :
            tdelay=(QPS - rdelta)/1000;
          else:
            tdelay = 1
        else:
          tdelay=1
      else:
        print("ERR: Baidu return {}".format(result))
        tdelay=3

      if tdelay:
        time.sleep(tdelay)

def combine_all_speech_into_one(tpath):
  global baidu_client,VOL,PER,QPS,PIT,SPD
  global pureName
  seq=1
  final_audio = AudioSegment.empty()
  tstart = datetime.datetime(2000,1,1,
    0, 0, 0, 0)
  tlast=tstart
  for itm in list_item:
    tdelta=itm.start-tlast
    print("Delta are {} start {} last {} total {} and {}".format(tdelta,itm.start,tlast,
      tdelta.total_seconds()*1000,int(tdelta.total_seconds()*1000)))
    tdelta=int(tdelta.total_seconds()*1000)
    if tdelta >0 :
      aempty=AudioSegment.silent(duration=tdelta)
      print("Append silent {} ".format(tdelta))
      final_audio=final_audio + aempty
    print("Slice {} pre {} audio {} ".format(seq,tdelta,itm.audio))
    song = AudioSegment.from_mp3(itm.audio)
    final_audio = final_audio + song
    tdelta=itm.end - itm.start
    # Subtitle in millseconds
    tdelta=tdelta.total_seconds()*1000
    # Actual audio length in 
    adelta=len(song)
    print("Target {} actual {} ".format(tdelta,adelta))
    if adelta < tdelta:
      tdelta=tdelta - adelta
      aempty=AudioSegment.silent(duration=tdelta)
      final_audio = final_audio + aempty
    tlast=itm.end
    seq=seq + 1

  fname=os.path.join(tpath,"combine_audio_"+pureName+".mp3")
  print("Combine {} len {} ".format(fname,len(final_audio)))
  final_audio.export(fname,format="mp3")
  return fname

def merge_audio_to_video(tpath,audio):
  global vidoclip,pureName
  global SrtFile

  audioclip=AudioFileClip(audio)
  finalclip = vidoclip.set_audio(audioclip)
  vname=os.path.join(tpath,"combine_video_"+pureName+".mp4")
  finalclip.write_videofile(vname)
  # generator = lambda txt: TextClip(txt, font=FONT,
  #                                  size=(800, 600), fontsize=24,
  #                                  method='caption', align='South',
  #                                  color='white')

  # subtitles = SubtitlesClip(SrtFile, generator)
  # final = CompositeVideoClip([finalclip, subtitles])
  # vname=os.path.join(tpath,"combine_video_subtitle_"+pureName+".mp4")
  # final.write_videofile(vname)

def load_srt_file(tfile):
  global list_delay
  global list_gap
  global list_item
  global num_itm
  global num_cha

  lcnt=0
  with open(tfile, "r",encoding='utf-8') as fh: 
    # lines=fh.readlines()  #使用readlines()函数 读取文件的全部内容，存成一个列表，每一项都是以换行符结尾的一个字符串，对应着文件的一行
    # subtitle_generator = srt.parse(str(lines))
    subtitle_generator = srt.parse(fh)
    # print("Sub {} type{}".format(subtitle_generator,type(subtitle_generator)))
    subtitles = list(subtitle_generator)
    # print("Here are {}".format(subtitles))
    tstart = datetime.datetime(2000,1,1,
      0, 0, 0, 0)
    for stt in subtitles:
      lcnt = lcnt + 1
      num_cha+=len(stt.content)
      thisitem=ItemLine(stt.content,seq=lcnt)
      thisitem.set_time(tstart+stt.start,tstart+stt.end,0)
      list_item.append(thisitem)
      print("Load {} content {} start {}".format(lcnt,stt.content,stt.start))
      num_itm  = num_itm + 1

  print("SRT  {}, Line {}".format(
    tfile,len(list_item)))

def load_audio_files_to_mem(tpath):
  bpath=os.path.join(tpath,'baidu_audio')
  for itm in list_item:
    aname="audio_"+pureName+"_"+"{:02d}".format(itm.start.second)+"{:03d}".format(int(itm.start.microsecond/1000))+".mp3"
    aname=os.path.join(bpath,aname)
    fname=os.path.join(bpath,aname)
    if os.path.isfile(fname) :
      print("Load {} audio".format(fname))
      itm.set_audio(fname)
    else:
      print("Can't find audio {} ".format(fname))

MdPath=''
MdFile=''
TxtFile=''
TxtPath=''
SrtFile=''
SrtPath=''
VideoLen=0
baidu_client=None
VOL=0
PER=4
QPS=0
PIT=0
SPD=0
vidoclip=None
audioclip=None
No_baidu=False
No_video=False
pureName=''

if __name__ == '__main__':
  try:
    opts, args = getopt.getopt(sys.argv[1:],"m:t:s:bv")
  except getopt.GetoptError:
    print('-m MP4 path\n')
    print('-t Text files ')
    print('-s SRT files ')
    final_out(2)

  print("CMD OPTS all ",opts)
  for opt, arg in opts:
    print("Cmd opt {} and {}".format(opt,arg))
    arg=arg.strip()
    if opt == '-t':
      if arg is None:
        print('ERR: -t filepath ')
        final_out(8)
      TxtFile=os.path.abspath(arg)
      print("Text file is ",TxtFile)
      if not os.path.isfile(TxtFile):
        print("ERR File not exist ",TxtFile)
        final_out(9)
    elif opt == '-m':
      if arg is None:
        print('ERR: -m filepath ')
        final_out(4)
      MdFile=os.path.abspath(arg)
      print("MP4 file is ",MdFile)
      if not os.path.isfile(MdFile):
        print("ERR File not exist ",MdFile)
        final_out(5)
    elif opt == '-s':
      if arg is None:
        print('ERR: -s filepath ')
        final_out(6)
      SrtFile=os.path.abspath(arg)
      print("SRT file is ",SrtFile)
      if not os.path.isfile(SrtFile):
        print("ERR File not exist ",SrtFile)
        final_out(7)
    elif opt == '-b':
      No_baidu = True
    elif opt == '-v':
      No_video = True

  if len(MdFile) ==0 :
    print("Must specify the MP4 file by -m")
    final_out(11)

  cmdPath=os.path.abspath(os.path.dirname(sys.argv[0]))
  pureName=os.path.splitext(os.path.basename(MdFile))[0]
  print('CMD file {} Txt {} Srt {}'.format(MdFile,TxtFile,SrtFile))
  curDate=datetime.datetime.now()
  bkdirname='asrt_'+pureName+'_'+str(curDate.year)+'_' \
    +str(curDate.month)+'_'+str(curDate.day)
  MdPath=os.path.dirname(MdFile)
  
  if not os.path.exists(MdPath):
    print("Create {} name {} bk {}".format(MdPath,pureName,bkdirname))
    try:
      os.mkdir(MdPath)
    except:
      print("ERR create directory failed ",MdPath)
  
  if six.PY2:
    config = ConfigParser.ConfigParser()
  else:
    config= configparser.ConfigParser(allow_no_value=True,)

  if os.path.isfile(os.path.join(cmdPath,'config.ini')):
    print("Load ini file {}".format(os.path.join(cmdPath,'config.ini')))
    # try:
    config.read(os.path.join(cmdPath,'config.ini'),encoding='utf-8')
    # except err:
    #   print("Failed load ini file ",err)
    #   exit(8)

    APP_ID=config.get('baidu','appid')
    API_KEY =config.get('baidu','apikey')
    SECRET_KEY = config.get('baidu','apisec')
    QPS = config.get('baidu','qps')
    if QPS is None or len(str(QPS)) ==0 or int(QPS) ==0 :
      QPS=5
    QPS=int(QPS)
    QPS=int(60/QPS)
    PIT = config.get('baidu','pit')
    VOL = config.get('baidu','vol')
    PER = config.get('baidu','per')
    SPD = config.get('baidu','spd')
  else:
    print("No ini file {}".format(os.path.join(cmdPath,'config.ini')))

  if len(APP_ID) <= 1 :
    print("BAIDU login info not correct")
    final_out(19)

  print("BAIDU {},key {},sec {},qps {},pit{},vol {},per {}".format(
    APP_ID,API_KEY,SECRET_KEY,QPS,PIT,VOL,PER))
  
  print("Copy {} to {}".format(MdFile,MdPath))
  tfile="bk_"+os.path.basename(MdFile)
  shutil.copyfile(MdFile,os.path.join(MdPath,tfile))
  MdFile=os.path.join(MdPath,tfile)
  
  if TxtFile :
    TxtPath = os.path.dirname(TxtFile)
    if SrtFile is None or len(SrtFile) == 0 :
      SrtPath = TxtPath
      SrtFile = os.path.splitext(os.path.basename(TxtFile))[0]+".srt"
      SrtFile = os.path.join(SrtPath,SrtFile)

  if SrtFile is None or len(SrtFile) == 0 :
    print("SRT file not defined and try same directory and file",MdPath)
    SrtFile=pureName+".srt"
    SrtFile=os.path.join(MdPath,SrtFile)
    if os.path.exists(SrtFile) :
      SrtPath = MdPath
      TxtFile = None
    else:
      TxtFile=pureName+".txt"
      TxtFile=os.path.join(MdPath,TxtFile)
      if os.path.exists(TxtFile):
        TxtPath = MdPath
      else:
        print("No srt or txt file and exist")
        final_out(21)
  else :
    if SrtPath is None or len(SrtPath) ==0 :
      SrtPath = os.path.dirname(SrtFile)

  print("MP4 {}/{} TXT {}/{} SRT {}/{} ".format(
    MdPath,MdFile,TxtFile,TxtPath,SrtFile,SrtPath))

  print("Reading length of the video")
  vidoclip = VideoFileClip(MdFile)
  VideoLen = vidoclip.duration
  if TxtFile :
    read_text_srt(TxtFile)
    convert_txt_to_srt(TxtFile,SrtFile)
  elif SrtFile:
    print("Load SrtFile {} directlly".format(SrtFile))
    load_srt_file(SrtFile)
  else:
    print("No text or srt file ")
    final_out(23)

  if num_itm:
    print("Convert txt to speach from baidu")
    baidu_client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    # time.sleep(8)
    if No_baidu is False:
      bpath=os.path.join(MdPath,'baidu_audio')
      if not os.path.exists(bpath):
        # print("Create {} name {} bk {}".format(bpath,pureName,bkdirname))
        try:
          os.mkdir(bpath)
        except:
          print("ERR create directory failed ",bpath)
      convert_txt_to_speech_baidu(bpath)
    else:
      load_audio_files_to_mem(MdPath)

    all_in_one_audiofile=combine_all_speech_into_one(MdPath)
    print("Combined all of the audio file into one {}".format(all_in_one_audiofile))
    if No_video is False:
      merge_audio_to_video(MdPath,all_in_one_audiofile)

  print("Done evertything")
