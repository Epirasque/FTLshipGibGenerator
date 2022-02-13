import sys
import time
from segmenter import segment

def main(argv):
    start = time.time()
    segment()
    end = time.time()
    print(end-start)

if __name__ == '__main__':
    main(sys.argv)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
