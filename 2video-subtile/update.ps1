
#echo $args[0]
#exit 0
#if ( Test-Path )
$fname=$args[0]
cd build
rm $fname
cp ..\$fname .
pyinstaller.exe --onefile $fname
rm ../release/*t.exe
cp dist/*.exe ../release/
cd ..
