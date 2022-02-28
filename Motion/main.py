import os
import shutil

from datetime import datetime
from Motion.operateCamera import videoRecord
from Motion.into_frames import toFrames
from Motion.compare_frames import compare
from Motion.send_email import fromFlaggedToSent
from Motion.send_email import establishAttachment

local_max = 0


def de_main(identity):
    for i in range(2):

        saveDir, videoFile = videoRecord(identity)
        print(f'saveDir is {saveDir} and videoFile is {videoFile}')
        toFrames(saveDir, videoFile)
        print(f'dir is {saveDir}')
        local_max, issueID = compare(saveDir)

        if (local_max > 5):  # significant movement is detected
            print(f'Max is {local_max}, moving to Flagged...')
            os.mkdir(f'./Motion/Flagged/{saveDir}')
            os.replace(f'./{saveDir}/{videoFile}', f'./Motion/Flagged/{saveDir}/{videoFile}')
            os.replace(f'./{saveDir}/frame_{issueID}.jpg', f'./Motion/Flagged/{saveDir}/frame_{issueID}-Detected.jpg')
            shutil.rmtree(f'./{saveDir}')

            attach_path = f'./Motion/Flagged/{saveDir}/frame_{issueID}-Detected.jpg'

            establishAttachment(attach_path)
            fromFlaggedToSent(saveDir, videoFile, issueID)

        elif (local_max <= 5):  # significant movement is not detected
            print(f'Insignificant max of {local_max} is found. Removing ./{saveDir}')
            shutil.rmtree(f'./{saveDir}')


local_max = 0
