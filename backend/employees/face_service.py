import cv2
import numpy as np
from insightface.app import FaceAnalysis

app = FaceAnalysis(
    name="buffalo_l",
    root=r"D:\InsightFace"
)

app.prepare(ctx_id=0)

def get_face_embedding(image_path):
    image = cv2.imread(image_path)

    if image is None:
        return None

    faces = app.get(image)

    if len(faces) == 0:
        return None

    return faces[0].embedding.tolist()