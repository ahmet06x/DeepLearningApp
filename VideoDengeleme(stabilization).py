import numpy as np
import cv2
import math

softeningRadius = 30
borderClipping = 20

vCapture = cv2.VideovCaptureture('test.mp4')

ret, prev = vCapture.read()
prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)

beforeTransformation = []

tip = 1

while (True):
    try:
        ret, curr = vCapture.read()
        curr_gray = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
        fParameter = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
        lk_params = dict(winSize=(15, 15), maxLevel=2,
                         criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        pCorner = cv2.goodFeaturesToTrack(prev_gray, mask=None, **fParameter)
        current_corner, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, pCorner, None, **lk_params)

        pCorner2 = pCorner[st == 1]
        current_corner2 = current_corner[st == 1]

        T = cv2.estimateRigidTransform(pCorner2, current_corner2, False)
        # if(T.any()):
        #	break
        dx = T[0, 2]
        dy = T[1, 2]
        da = math.atan2(T[1, 0], T[0, 0])

        beforeTransformation.append((dx, dy, da))
        prev = curr.copy()
        prev_gray = curr_gray.copy()
        cv2.imshow(curr)
        tip += 1
        key = cv2.waitKey(30) & 0xff
        if key == 27:
            break
    except:
        break;

topFrame = tip
a, x, y = 0.0, 0.0, 0.0
trajectory = []

for i in range(len(beforeTransformation)):
    tx, ty, ta = beforeTransformation[i]
    x += tx
    y += ty
    a += ta
    trajectory.append((x, y, a))

smoothed_trajectory = []

for i in range(len(trajectory)):
    sx, sy, sa, ctr = 0.0, 0.0, 0.0, 0
    for j in range(-softeningRadius, softeningRadius + 1):
        if (i + j >= 0 and i + j < len(trajectory)):
            tx, ty, ta = trajectory[i + j]
            sx += tx
            sy += ty
            sa += ta
            ctr += 1
    smoothed_trajectory.append((sx / ctr, sy / ctr, sa / ctr))

new_beforeTransformation = []
a, x, y = 0.0, 0.0, 0.0

for i in range(len(beforeTransformation)):
    tx, ty, ta = beforeTransformation[i]
    sx, sy, sa = smoothed_trajectory[i]
    x += tx
    y += ty
    a += ta
    new_beforeTransformation.append((tx + sx - x, ty + sy - y, ta + sa - a))

vBorder = borderClipping * len(prev) / len(prev[0])

vCapture = cv2.VideovCaptureture('test.mp4')

tip = 0

while (tip < topFrame - 1):
    ret, curr = vCapture.read()
    tx, ty, ta = new_beforeTransformation[k]
    T = np.matrix([[math.cos(ta), -math.sin(ta), tx], [math.sin(ta), math.cos(ta), ty]])
    curr2 = cv2.warpAffine(curr, T, (len(curr), len(curr[0])))
    curr2 = curr2[borderClipping:len(curr2[0] - borderClipping),
            vBorder:len(curr2) - vBorder]
    curr2 = cv2.resize(curr2, (len(curr[0]), len(curr)))

    cv2.imshow(curr2)

    key = cv2.waitKey(30) & 0xff
    if key == 27:
        break
    tip += 1

vCapture.release()
