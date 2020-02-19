# 四知回--Markdown文件图片自动上传七牛云并更新文件---文件说明

&#8195;&#8195;

##   文件说明

- markdown-upload-pic.py 主代码函数文件

- setup.py 暂时无用，原用于py2exe生成windows可执行程序

- update.ps1 powershell 脚本程序，用于重新编译出.exe文件

- release/config.ini 程序运行所需要的配置文件，主要用于配置七牛云链接信息等

  - 配置条目很简单，参考文档中的说明即可

- AddUploadMdtoContextMenu_pdbolt.reg 注册表，右键菜单添加 'Upload to cloud' 功能

![PDBoLT右键菜单](../images/pdbolt-markdown-upload-menu.png)

- RemoveUploadMdfromContextMenu_pdbolt.reg 注册表，删除右键菜单的 'Upload to cloud'条目

------



