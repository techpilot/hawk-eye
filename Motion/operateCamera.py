import cv2
from datetime import datetime
import time
import os


def videoRecord(identity):

    capture = cv2.VideoCapture(identity)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    saveDir = f'{datetime.now().date()}@{datetime.now().hour}-{datetime.now().minute}-{datetime.now().second}'
    os.mkdir(saveDir)
    videoFile = f'{datetime.now().time().hour}-{datetime.now().time().minute}-{datetime.now().time().second}.avi'
    print(f'Saving in {saveDir} as: {videoFile}')
    out = cv2.VideoWriter(f'./{saveDir}/{videoFile}', fourcc, 20.0, (640, 480))

    start_time = time.time()

    while (capture.isOpened()):
        ret, frame = capture.read()
        if ret == True:
            # frame = cv2.flip(frame, 0)

            out.write(frame)
            # cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            end_time = time.time()
            elapsed = end_time - start_time
            if elapsed > 10:
                break
        else:
            break
    capture.release()
    out.release()
    cv2.destroyAllWindows()

    return saveDir, videoFile