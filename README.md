## Rasa 기반 지능형 기숙사 정보 안내 챗봇

챗봇 제작 과정
https://aurora718.tistory.com/14


# 📖 프로젝트 소개
본 프로젝트는 선문대학교 성화학숙(기숙사) 학생들을 위한 지능형 정보 안내 챗봇이다. Rasa 프레임워크와 MySQL 데이터베이스를 기반으로, 기숙사 규칙, 교내 연락처, 시설 안내 등 반복적인 질문에 24시간 실시간으로 응답한다. 텍스트와 이미지를 활용한 직관적인 정보 제공을 통해 학생들의 편의를 증진하고 행정 업무의 효율성을 높이는 것을 목표로 한다.

# ✨ 주요 기능
데이터베이스 연동 정보 제공: MySQL DB에 저장된 300여 개의 규칙 및 연락처 정보를 동적으로 조회하여 텍스트로 답변
멀티미디어 응답 (이미지): 규칙 안내, 수강신청 방법, 학교 지도 등 특정 질문에 텍스트와 함께 관련 이미지를 시각적으로 제공하여 정보 이해도 향상
지능형 한국어 처리: KoNLPy(Okt) 기반의 커스텀 토크나이저(korean_tokenizer.py)를 직접 구현하여, 한국어의 유연한 띄어쓰기 및 다양한 표현에 대응하는 NLU 모델 구축
다국어 지원 기반: googletrans 라이브러리를 활용하여, 외국인 유학생의 비한국어 질문에 대한 기본적인 응대 및 번역 기능 구현

# 🛠️ 기술 스택
분야	주요 기술
챗봇 프레임워크	Rasa (NLU, Core)
백엔드	Python, Flask (이미지 서버), MySQL (데이터베이스)
자연어 처리	KoNLPy (Okt), Googletrans
개발 환경	Anaconda, Git, GitHub

# 🏗️ 시스템 아키텍처
본 챗봇은 안정성과 확장성을 위해 역할에 따라 3개의 독립적인 서버와 1개의 데이터베이스로 구성된 모듈형 아키텍처를 가진다.

 <img src="https://github.com/aurora843/aurora843/blob/main/%EB%8B%A4%EC%9A%B4%EB%A1%9C%EB%93%9C%20(2).png">

Rasa 서버 (Port 5005): NLU(자연어 이해) 및 Core(대화 관리)를 담당하는 챗봇의 핵심 두뇌

액션 서버 (Port 5055): 데이터베이스 조회 등 복잡한 로직을 수행하는 actions.py 실행

이미지 서버 (Port 8080): Flask 기반으로 구축, 로컬 이미지 파일을 웹 URL로 제공

데이터베이스 (MySQL): rules_data(규칙), chatbot(연락처), images(이미지 정보) 테이블에 챗봇의 모든 지식 저장

# ⚙️ 설치 및 시작하기
사전 요구사항
Anaconda 
Python 3.10
Rasa 3.6.21
numpy 1.23.5
pydantic 1.10.9
tensorflow 2.11.1 (or 2.10)
spacy3.5

MySQL Server
1. 프로젝트 클론
Bash
git clone https://github.com/your-username/your-repository.git
cd your-repository

2. Python 가상 환경 설정
Bash

# 새로운 Conda 가상 환경 생성 및 활성화
conda create --name rasa_env python=3.10
conda activate rasa_env

# 필수 라이브러리 설치 (Rasa 및 의존성)
pip install rasa==3.6.21
pip install mysql-connector-python pymysql googletrans==4.0.0-rc1 konlpy

# Rasa 3.6.21 호환성을 위한 버전 고정 (중요)
pip install packaging==20.9 protobuf==4.23.3 tensorflow==2.12.0 tensorflow-intel==2.12.0
3. 데이터베이스 및 데이터 설정
MySQL 서버에 rasa_core 데이터베이스를 생성한다.
프로젝트 내 Python 스크립트(insert_rules.py, insert_contacts.py 등)를 실행하여 rules_data, chatbot, images 테이블에 초기 데이터를 삽입한다.
image_server.py의 BASE_IMAGE_DIR 경로에 맞게 이미지 파일들을 준비한다.
4. Rasa 모델 학습
Bash

rasa train
🚀 실행 방법
프로젝트를 실행하려면 3개의 터미널 창이 필요하다. 각 터미널에서 가상 환경을 활성화(conda activate rasa_env)한 후 다음을 순서대로 실행한다.

터미널 1: 이미지 서버 실행

Bash

python image_server.py
터미널 2: Rasa 액션 서버 실행

Bash

rasa run actions
터미널 3: Rasa 메인 서버 실행

Bash

rasa run
<!-- end list -->

모든 서버가 실행되면, webchat.html 파일을 웹 브라우저에서 열어 챗봇을 테스트할 수 있다.
