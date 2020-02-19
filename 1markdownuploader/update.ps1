
cd build
rm markdown-upload-pic.py
cp ..\markdown-upload-pic.py .
pyinstaller.exe --onefile markdown-upload-pic.py
rm ../release/markdown-upload-pdbolt.exe
cp .\dist\markdown-upload-pic.exe ../release/markdown-upload-pdbolt.exe
