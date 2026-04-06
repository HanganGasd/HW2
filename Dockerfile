# 1. Base Image - 모델 서빙을 위해 불필요한 OS 패키지가 제외된 파이썬 slim 공식 이미지 사용
FROM python:3.10-slim

# 2. 시스템 환경 변수 설정
# 파이썬 출력이 버퍼링 없이 즉시 터미널에 출력되고 pyc 파일을 만들지 않도록 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

# 3. 작업 디렉토리 생성 및 워킹 디렉토리 지정
WORKDIR $APP_HOME

# 4. 운영체제 패키지 업데이트 및 빌드에 필요한 최소 패키지 설치
# (slim 이미지를 사용하므로 필요한 경우 apt 설치. 현재는 기본 패키지로 충분합니다.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 5. 의존성 파일 복사 및 설치
# 도커 캐싱 계층의 이점을 얻기 위해 패키지 의존성 파일을 소스코드보다 먼저 복사합니다.
# 이렇게 하면 소스코드만 수정되었을 때 패키지를 매번 다시 설치하지 않습니다.
COPY requirements.txt .

# 패키지 설치 후 캐시를 삭제(--no-cache-dir)하여 최종 이미지 크기 최소화
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. 실제 어플리케이션 소스 코드 복사
COPY main.py .

# 7. 보안성 강화: 모델이 root 권한으로 실행되는 것을 방지하기 위해 일반 유저 생성
RUN useradd -m -s /bin/bash appuser \
    && chown -R appuser:appuser $APP_HOME

# 생성한 일반 유저로 권한 전환
USER appuser

# 8. 컨테이너가 외부에 노출할 포트 명시
EXPOSE 8000

# 9. FastAPI 구동 명령어 정의 (uvicorn 사용)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
