import os

if os.name == 'nt':
    import cvwin.cv2 as cv2
    cv = cv2.cv
else:
    import cv
