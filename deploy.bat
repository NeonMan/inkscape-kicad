@echo off

SET INKSCAPE_PATH=C:\Program Files\Inkscape

copy *.inx "%INKSCAPE_PATH%\share\extensions\"
copy *.py "%INKSCAPE_PATH%\share\extensions\"

timeout /T 10

cd %INKSCAPE_PATH%
start inkscape.exe
