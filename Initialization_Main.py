import InitiatlizationMethods as init
from pathlib import Path
import DataMethods as dm

# should all be in the same recording directory from Savio (recordingOutputDir)
recordingHomeDir = Path('/Users/kve/Desktop/Clubs/Harland_Lab/Round_11.nosync/RosarioFlores/20200920_RosarioFlores_SD_post_amp_457pm_cam4_1')

#automatic procurement from home directories if labeled right
pathOfPreInitializationDFDir = recordingHomeDir / 'Initialization_DF'
pathOfPreInitializationDFPath = dm.getCSVFilePaths(pathOfPreInitializationDFDir)[0]
pathOfInitializationStack = recordingHomeDir / 'Initialization_Stack'

print(recordingHomeDir.name)

init.initialization_Main(pathOfPreInitializationDFPath, pathOfInitializationStack, recordingHomeDir, True)


# TODO: add script that creates an orientation CSV after all the video processing chunks run. Should be after all the processes are joined and on Savio-HTC