import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import logging

# MLOps 관점에서 로깅은 필수적입니다.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Age & Gender Prediction API",
    description="MLOps 파이프라인 구축을 위한 가벼운 얼굴 인식 및 나이/성별 예측 API",
    version="1.1.0" # v1.1.0으로 마이너 버전 업데이트
)

# 1. 가벼운 얼굴 검출 모델 로드
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def predict_attributes(face_img: np.ndarray) -> dict:
    """
    가상의 나이 및 성별 예측 추론 함수입니다.
    실제 프로젝트에서는 여기에 경량화된 모델 (예: TFLite, ONNX 등)의 추론 로직을 연동합니다.
    """
    # 가상의 나이 도출
    pseudo_random_age = int(np.mean(face_img) % 40) + 15
    
    # [NEW] 성별 예측 기능 추가: 가상의 로직으로 배열의 총합 홀짝에 따라 성별 판별
    pseudo_random_gender = "Male" if int(np.sum(face_img)) % 2 == 0 else "Female"
    
    return {
        "age": pseudo_random_age,
        "gender": pseudo_random_gender
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    이미지를 업로드 받아 얼굴을 찾고, 나이 및 성별을 예측하는 엔드포인트
    """
    if not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file uploaded: {file.content_type}")
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    try:
        # 데몬 속도 최적화를 위해 메모리 자체에서 I/O
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("이미지를 디코딩할 수 없습니다.")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        results = []
        for (x, y, w, h) in faces:
            # 1. 얼굴 영역(ROI) 크롭 처리
            face_roi = img[y:y+h, x:x+w]
            
            # 2. 모델 업데이트: 나이 및 성별 동시 추론
            preds = predict_attributes(face_roi)
            
            results.append({
                "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "predicted_age": preds["age"],
                "predicted_gender": preds["gender"] # 응답 객체에 성별 속성 추가
            })

        logger.info(f"Prediction successful. Detected {len(results)} faces.")
        return JSONResponse(status_code=200, content={
            "status": "success",
            "faces_detected": len(results),
            "predictions": results
        })

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail="이미지 처리 중 서버 에러가 발생했습니다.")

@app.get("/health")
def health_check():
    # 배포 업데이트 확인을 위해 버전을 응답에 포함
    return {"status": "healthy", "version": "1.1.0"}
