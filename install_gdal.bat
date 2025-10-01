wget https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe
osgeo4w-setup.exe --upgrade-also --arch x86_64 --advanced --autoaccept --quiet-mode --disable-buggy-antivirus --packages gdal,gdal-devel

set LIB=%userprofile%/appdata/local/programs/osgeo4w/lib
set INCLUDE=%userprofile%/appdata/local/programs/osgeo4w/include