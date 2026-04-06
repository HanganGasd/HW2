import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import logging

# 기본적인 로깅 설정 (MLOps 관점에서 로깅은 필수적입니다)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Age Prediction API",
    description="MLOps 파이프라인 구축을 위한 가벼운 얼굴 인식 및 나이 예측 API",
    version="1.0.0"
)

# 1. 가벼운 얼굴 검출 모델 로드 (OpenCV 기본 제공 Haar Cascade 사용)
# MLOps 관점: 모델은 서버 시작 시 메모리에 한 번만 로드하여 재사용합니다.
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def predict_age(face_img: np.ndarray) -> int:
    """
    가상의 나이 예측 추론 함수입니다.
    실제 프로젝트에서는 여기에 경량화된 모델 (예: TFLite, ONNX, MobileNet 등)의 
    추론 로직을 연동합니다.
    """
    # TODO: 실제 AI 모델의 model.predict() 로 교체 필요
    # 현재는 얼굴 크기나 픽셀 값에 기반한 가상의 나이를 리턴하도록 모킹해두었습니다.
    pseudo_random_age = int(np.mean(face_img) % 40) + 15
    return pseudo_random_age

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    이미지를 업로드 받아 얼굴을 찾고 나이를 예측합니다.
    """
    if not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type uploaded: {file.content_type}")
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    try:
        # 업로드된 파일을 메모리에서 바로 읽어 처리합니다 (디스크 I/O 최소화)
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("이미지를 디코딩할 수 없습니다.")

        # 처리 속도 향상을 위한 그레이스케일 변환 및 얼굴 검출
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )

        results = []
        for (x, y, w, h) in faces:
            # 1. 얼굴 영역(ROI) 크롭
            face_roi = img[y:y+h, x:x+w]
            
            # 2. 나이 예측 추론 실행
            predicted_age = predict_age(face_roi)
            
            results.append({
                "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "predicted_age": predicted_age
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
    """로드 밸런서 또는 쿠버네티스의 헬스 체크용 엔드포인트"""
    return {"status": "healthy"}

# 개발 환경 실행용
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
