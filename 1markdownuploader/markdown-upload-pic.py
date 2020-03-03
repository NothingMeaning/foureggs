#coding:utf-8

'''
根据以下两个脚本修改：
https://github.com/JyHu/useful_script
https://github.com/hxzqlh/qiniu-markdown-pics
'''


"""

转换md文件中的图片

python 脚本地址 文件地址 [是否需要压缩]

eg：

python ~/Dropbox/useful_script/Scripts/md文件图片图床转换/md_transfer.py ~/Desktop/t.md 0

Windows中本地路径是用反斜杠 by chalkit

0 - 不需要图片压缩
1 - 需要图片压缩

"""

import re
import os
import sys
import time
import math
import imghdr
import shutil
import random
import string
import tinify
import urllib
import sqlite3
import operator
from hashlib import md5
from qiniu import Auth, put_file, etag, BucketManager
from datetime import date
import validators
from array import *
import sys, getopt
import six
if six.PY2:
    import ConfigParser as configparser
else:
    import configparser

from datetime import datetime
from shutil import copyfile
import pypandoc

os.environ.setdefault('PYPANDOC_PANDOC', 'C:\\Program Files\\Pandococ')

# 
# ak = '4bm7YaqUpRKnALOdWQkIVpZ_f3KH-uHL5SgV5MjH'
# sk = '0uhj2OlLO_HMlAr7psd-A_ChxXpPeu_5GLPRgHY3'
# domain = 'picres.pdusb.com' # 上传域名
# bucket = 'pdusb' # 空间名称
ak = ''
sk = ''
bucket=''

tinify.key = ' ' # 设置tinipng的key
md_loc = ''    # md地址
q = None

today = date.today()
yyyymmdd = today.strftime('%Y%m%d')   #创建时间变量，用于图片起名
total, success, failure, ignore = 0, 0, 0, 0

def upload_file(upload_file_name):
    '''
    根据给定的图片名上传图片，并返回图片地址和一些上传信息
    '''
    global success , ignore , failure
    global MdPath , RemotePath,UrlBase
    #rstr = str(time.time())+''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 12))
    #key = md5(rstr.encode('utf-8')).hexdigest()   # 上传到七牛后的图片名
    # key = yyyymmdd+"_"+os.path.splitext(os.path.basename(sys.argv[1]) )[0]+"/image"+('{0}'.format(success+1))+os.path.splitext(upload_file_name)[1]
    # 上传到七牛后的图片名:上传日期-MD文件名/image序号.png or jpg
    mime_type = upload_file_name[upload_file_name.rfind('.') + 1:]
    key = RemotePath+"/"+os.path.basename(upload_file_name)
    token = q.upload_token(bucket, key)
    print("Target key {} token {} mime {}".format(key,token,mime_type))
    ret, info = put_file(token, key, upload_file_name, mime_type=mime_type, check_crc=True)
    if ret['key'] == key and ret['hash'] == etag(upload_file_name):
        success = success + 1
        return UrlBase + '/' +key, info
    failure = failure + 1
    return None,None

def transfer_online_img(old_link):
    '''
    根据给定的图片链接上传图片到七牛，并返回图片地址和一些上传信息
    '''
    global success , ignore , failure
    if validators.url(old_link) is not True:
        ignore = ignore + 1
        print('invalid url, ignore')
        return None

    # maybe a url
    # already from qiniu
    if old_link.find(domain) != -1:
        ignore = ignore + 1
        print('already in qiuniu, ignore')
        return None

    # omit the query string section like:?arg1=val1&arg2=val2 in the url
    if old_link.find('?') != -1:
        old_link = old_link[: old_link.index('?')]

    #key = yyyymmdd + "-" +''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 6))
    key = yyyymmdd+"_"+os.path.splitext(os.path.basename(sys.argv[1]) )[0]+"/image"+('{0}'.format(success+1))
    # 上传到七牛后的图片名:上传日期-MD文件名/image序号
    ret, info = Bucket_Manager.fetch(old_link, bucket, key)
    if ret['key'] == key :
        success = success + 1
        return 'http://' + domain + '/' +key
    failure = failure + 1
    return None

def cached_img_url(img_loc_path):
    '''
    根据给定的本地图片绝对路径，转换成一个网上路径。
    如果本地缓存中有，则直接读取并返回，如果没有，则上传后返回。
    '''
    conn = sqlite3.connect(md_loc + '/img_hash_cache.db')
    cursor = conn.cursor()
    try:
        cursor.execute(''' 
            CREATE TABLE img_cache_table (
                img_hash TEXT,
                real_p TEXT,
                img_url TEXT,
                u_info TEXT
            )
            ''')
    except Exception as e: pass
    img_hash = md5(open(img_loc_path, 'rb').read()).hexdigest()     # 图片的hash值，用来确定图片的唯一性，避免多次上传，浪费流量
    cursor.execute("SELECT img_url FROM img_cache_table WHERE img_hash='%s'" % img_hash)    #根据图片的hash值来找缓存下来的图片网址
    select_res = [row for row in cursor]
    img_url = (select_res[0][0] if select_res and len(select_res) > 0 and select_res[0] and len(select_res[0]) > 0 else None)

    remote_exists = False
    if img_url:
        try: remote_exists = urllib.request.urlopen(img_url).code == 200
        except Exception as e: 
            print('#warning: 网址不存在 ：', img_url)
            remote_exists = False
    if not img_url or not remote_exists:     # 如果没有查到图片的网址，或者网址失效
        img_loc_path=os.path.join(MdPath,img_loc_path)
        print('上传图片 ：', img_loc_path)
        img_url, uinfo = upload_file(img_loc_path)  # 接取上传后的图片信息
        if not img_url:     # 如果图片地址为空，则说明上传失败
            print('#warning: 上传失败')
            conn.close()
            return None
        else:
            print("Url {} ".format(img_url))
            if not remote_exists:  cursor.execute('INSERT INTO img_cache_table VALUES(?,?,?,?)', (img_hash, img_loc_path, img_url, str(uinfo))) # 如果上传成功，则直接缓存下来
            else :  cursor.execute("UPDATE img_cache_table SET img_url='%s', u_info='%s' WHERE img_hash='%s'" % (img_url, str(uinfo), img_hash))
            conn.commit()
    conn.close()

    return img_url

def md_img_find(md_file):
    '''
    将给定的markdown文件里的图片本地路径转换成网上路径
    '''
    post = None  # 用来存放markdown文件内容
    global total , success , failure , ignore
    global DoZip
    with open(md_file, 'r',encoding='utf-8') as f: #使用utf-8 编码打开 by chalkit
      post = f.read()
      matches = re.compile('!\\[.*?\\]\\((.*?)\\)|<img.*?src=[\'\"](.*?)[\'\"].*?>').findall(post)     # 匹配md文件中的图片
      if matches and len(matches) > 0:
        for sub_match in matches:       # 正则里有个或，所以有分组，需要单独遍历去修改   
          for match in sub_match:     # 遍历去修改每个图片
            total = total + 1
            if match and len(match) > 0:
              print("match pic : ", match)
              if not re.match('((http(s?))|(ftp))://.*', match):  # 判断是不是已经是一个图片的网址
                loc_p = match
                if not os.path.exists(loc_p) or not os.path.isfile(loc_p):  # 如果文件不存在，则可能这是用的一个相对路径，需要转成绝对路径
                    loc_p = md_file[:md_file.rfind('\\')+1] + match     # Windows中 md_file的本地路径为反斜杠\\, match的相对路径为 "MD标题\图片文件名"
                if os.path.exists(loc_p) and os.path.isfile(loc_p):
                    if imghdr.what(loc_p):  # 如果是一个图片的话，才要上传，否则的话，不用管
                        if DoZip:
                            o_img = loc_p + '.ori'  # 原始未压缩的图片
                            try:
                                if not os.path.isfile(o_img) or not imghdr.what(o_img):     # 如果没有的话，那就需要进行压缩处理
                                    print('压缩图片 ：', loc_p) 
                                    s_img = tinify.from_file(loc_p)
                                    s_img.to_file(loc_p + '.z')
                                    os.rename(loc_p, loc_p + '.ori')
                                    os.rename(loc_p + '.z', loc_p)
                            except Exception as e:
                                print('#warning: tinypng压缩出问题了，图片未压缩。')
                        file_url = cached_img_url(loc_p)    # 获取上传后的图片地址
                        if file_url:    # 在图片地址存在的情况下进行替换
                            print('图片地址是:{} and replace it {}'.format(file_url,match))
                            post = post.replace(match, file_url)    # 替换md文件中的地址
                    else:
                        ignore = ignore + 1
                        print('#warning: 不是一个图片文件 ：', loc_p)
                        continue
                else:
                    ignore = ignore + 1
                    print('#warning: 文件不存在 ：', loc_p)
              else:
                print('markdown文件中的图片用的是网址 ：', match)
                file_url = transfer_online_img(match)  # 获取上传后的图片地址
                if file_url:  # 在图片地址存在的情况下进行替换
                    print('图片地址是 ： ', file_url)
                    post = post.replace(match, file_url)  # 替换md文件中的地址
        
        if post: 
          # print("Do have post {}".format(post))
          open(md_file, 'w',encoding='utf-8').write(post) #如果有内容的话，就直接覆盖写入当前的markdown文件
                                    #仍然注意用uft-8编码打开
    print ('Complete!')
    print (' total   :%d' %(total))
    print (' success :%d' %(success))
    print (' failure :%d' %(failure))
    print (' ignore  :%d' %(ignore))


def convert_md_to_rtf(mdfile,rtf):
  print('Markdown {} to RTF {}'.format(mdfile,rtf))
  try:
    output = pypandoc.convert_file(mdfile, 'rst', format='md')
  


def find_md(folder):
    '''
    在给定的目录下寻找md文件  
    '''
    if len(folder) > 3: 
        if folder[folder.rfind('.') + 1:] == 'md': md_img_find(folder) # 判断是否是一个md文件，如果是的话，直接开始转换
    elif os.path.isdir(folder):
        files = os.listdir(folder)
        # 读取目录下的文件
        for file in files:
            curp = folder + '/' + file
            if os.path.isdir(curp): find_md(curp) # 递归读取
            elif file[file.rfind('.') + 1:] == 'md': md_img_find(curp)

def final_out(reason):
  print("Command failed by ",reason)
  os.system('pause')
  sys.exit(reason)

MdPath=''
MdFile=''
MdFiles=''
DoZip=''
UrlBase=''
RemotePath=''
RtfTest=''

if __name__ == '__main__':
  try:
    opts, args = getopt.getopt(sys.argv[1:],"u:d:m:raz")
  except getopt.GetoptError:
    print('-m MDfile path\n')
    print('-a Upload all md files in the directrory')
    print('-z ZIP ')
    print('-d directory in remote ')
    print('-u URL base')
    final_out(2)

  print("CMD OPTS all ",opts)
  for opt, arg in opts:
    print("Cmd opt {} and {}".format(opt,arg))
    arg=arg.strip()
    if opt == '-u':
      if arg is not None:
        if arg.startswith('http') :
          UrlBase=arg
        else:
          UrlBase='http://'+arg
      else:
        print('ERR: -u http://youdaonm.com/xx/yy')
        final_out(3)
    elif opt == '-m':
      if arg is None:
        print('ERR: -m filepath ')
        final_out(4)
      MdFile=os.path.abspath(arg)
      print("MD file is ",MdFile)
      if not os.path.isfile(MdFile):
        print("ERR File not exist ",MdFile)
        final_out(5)
    elif opt == '-d':
      if arg is None:
        print("ERR -d must have one path")
        final_out(6)
      RemotePath=arg
    elif opt == '-r':
      RtfTest = True

  if len(MdFile) ==0 :
    print("Must specify the MD file by -m")
    final_out(11)

  cmdPath=os.path.abspath(os.path.dirname(sys.argv[0]))
  pureName=os.path.splitext(os.path.basename(MdFile))[0]
  print('CMD file {} RemotePath {} URL {} Rtf {}'.format(MdFile,RemotePath,UrlBase,RtfTest))
  curDate=datetime.now()
  bkdirname='qiniu_'+pureName+'_'+str(curDate.year)+'_' \
    +str(curDate.month)+'_'+str(curDate.day)+'_'+str(curDate.microsecond)
  MdPath=os.path.dirname(MdFile)
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

    if RemotePath == '' :
      RemotePath=config.get('qiniu','folder')
    dbpath=config.get('system','dbpath')
    if dbpath == "default":
      md_loc = cmdPath
    elif dbpath == "mdpath":
      md_loc=MdPath
    ak=config.get('qiniu','ak')
    sk=config.get('qiniu','sk')
    UrlBase=config.get('qiniu','domain')
    bucket=config.get('qiniu','bucket')
    if DoZip == '':
      DoZip=config.getboolean('system','zip')
    if DoZip is None or DoZip == '' or DoZip == ' ':
      DoZip=False
  else:
    print("No ini file {}".format(os.path.join(cmdPath,'config.ini')))
  
  if not os.path.exists(MdPath):
    print("Create {} name {} bk {}".format(MdPath,pureName,bkdirname))
    try:
      os.mkdir(MdPath)
    except:
      print("ERR create directory failed ",MdPath)
  
  if len(ak) == 0 or len(sk) == 0 or len(UrlBase) == 0 or len(bucket) == 0:
    print("Config missed AK {} SK {} domain {} bucket {}".format(
      ak,sk,UrlBase,bucket
    ))
    final_out(10)
  
  print("Copy {} to {}".format(MdFile,MdPath))
  tfile=bkdirname+".md"
  rtf=bkdirname+'.rtf'
  shutil.copyfile(MdFile,os.path.join(MdPath,tfile))
  shutil.copyfile(MdFile,os.path.join(MdPath,rtf))
  if RtfTest :
    RtfFile=os.path.join(MdPath,rtf)
    print("Converting to rtf {}".format(RtfFile))
    convert_md_to_rtf(MdFile,RtfFile)
    print("Convert done")
    sys.exit(0)

  MdFile=os.path.join(MdPath,tfile)
  print("MD file {}, Remote PATH {}".format(MdFile,RemotePath))
  # print("Config AK {} SK {} domain {} bucket {}".format(
  #     ak,sk,UrlBase,bucket
  #   ))
  q = Auth(ak, sk)    # 七牛认证
  #初始化BucketManager
  Bucket_Manager = BucketManager(q)
  md_img_find(MdFile)

  print("File upload done and will exit in 8 seconds")
  time.sleep(8)
    
