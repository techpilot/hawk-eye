from PIL import Image
import imagehash


def compare(directory):
    comparisonGraph = []

    # establishes the control (first frame) of the video for comparison
    control = Image.open(f'./{directory}/frame_0.jpg')
    control_hash = imagehash.whash(control)
    print(control_hash)
    max = 0
    id_flagged = 0
    n = 0
    while (True):
        try:
            compare = Image.open(f'./{directory}/frame_{n}.jpg')
            print(f'Reading hash from ./{directory}/frame_{n}.jpg ...')
            compare_hash = imagehash.whash(compare)
            similarity = control_hash - compare_hash
            # shows the similarity between the control and each frame of the video
            if similarity > max:
                max = similarity
                id_flagged = n
            comparisonGraph.append(similarity)
            n = n + 1

        except FileNotFoundError:
            print("Error: File not Found")
            break

    length = len(comparisonGraph)
    print("length is " + str(length))

    # Display the difference for all the frames vs the control frame
    for i in range(length):
        print("comparisonGraph[" + str(i) + "] == " + str(comparisonGraph[i]))

    return max, id_flagged