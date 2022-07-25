pyinstaller -F Core.py --hidden-import skimage.filters.edges
RMDIR /S /Q binary
mkdir binary
cd binary
robocopy C:\Users\roman\PycharmProjects\glaive\ C:\Users\roman\PycharmProjects\glaive\binary\ LICENSE
ren LICENSE LICENSE.txt
robocopy C:\Users\roman\PycharmProjects\glaive\ C:\Users\roman\PycharmProjects\glaive\binary\ README.txt
robocopy C:\Users\roman\PycharmProjects\glaive\dist\ C:\Users\roman\PycharmProjects\glaive\binary\ Core.exe
ren Core.exe GLAIVE.exe
robocopy C:\Users\roman\PycharmProjects\glaive\metalBits C:\Users\roman\PycharmProjects\glaive\binary\metalBits /COPYALL /E
robocopy C:\Users\roman\PycharmProjects\glaive\ C:\Users\roman\PycharmProjects\glaive\binary\ config.ini_for_addons
ren config.ini_for_addons config.ini
robocopy C:\Users\roman\PycharmProjects\glaive\ C:\Users\roman\PycharmProjects\glaive\binary\ loggingForCore.yaml
robocopy C:\Users\roman\PycharmProjects\glaive\ C:\Users\roman\PycharmProjects\glaive\binary\ loggingForSubprocess.yaml
mkdir stabilityMarkers
robocopy C:\Users\roman\PycharmProjects\glaive\stabilityMarkers\ C:\Users\roman\PycharmProjects\glaive\binary\stabilityMarkers\ STABILITY_MARKERS_ARE_STORED_HERE
mkdir statsForProcessedShips
robocopy C:\Users\roman\PycharmProjects\glaive\statsForProcessedShips\ C:\Users\roman\PycharmProjects\glaive\binary\statsForProcessedShips\ DO_NOT_PUT_OTHER_FILES_HERE
