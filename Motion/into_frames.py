import cv2


def toFrames(directory, videoFile):
    capture = cv2.VideoCapture(f'./{directory}/{videoFile}')

    frameN = 0

    while True:
        success, frame = capture.read()

        if success:
            cv2.imwrite(f'./{directory}/frame_{frameN}.jpg', frame)

        else:
            break

        frameN = frameN + 1

    capture.release()
