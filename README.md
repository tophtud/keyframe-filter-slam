# Keyframe Filter for SLAM

다중 평가 지표 기반 SLAM 키프레임 필터링 시스템

## 개요

Visual SLAM 시스템에서 생성된 키프레임을 위치, 방향, 품질 세 가지 지표로 평가하여 최적의 키프레임을 선별하는 후처리 도구입니다.

## 주요 기능

- **위치 평가**: 가우시안 함수 기반 거리 점수 계산
- **방향 평가**: 코사인 유사도 기반 방향 일치도 계산
- **품질 평가**: 라플라시안 분산 기반 이미지 선명도 계산
- **세미-오토매틱 웨이포인트 생성**: 초기 2-3개 선택으로 나머지 자동 생성

## 프로젝트 구조

```
keyframe-filter-slam/
├── src/                    # 소스 코드
│   ├── filter.py          # 메인 필터링 로직
│   ├── position_score.py  # 위치 평가
│   ├── direction_score.py # 방향 평가
│   ├── quality_score.py   # 품질 평가
│   └── waypoint_gen.py    # 웨이포인트 자동 생성
├── data/                   # 데이터 파일
│   └── map.msg            # stella_vslam 맵 파일
├── results/                # 실험 결과
│   ├── figures/           # 그래프 및 시각화
│   └── filtered_maps/     # 필터링된 맵
├── docs/                   # 문서
│   └── methodology.md     # 방법론 상세 설명
├── tests/                  # 테스트 코드
├── requirements.txt        # Python 패키지 의존성
└── README.md              # 프로젝트 설명
```

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
python src/filter.py --input data/map.msg --output results/filtered_map.msg
```

## 연구 배경

본 프로젝트는 2026년 KCI 논문 투고를 목표로 진행 중인 연구입니다.

## 라이센스

MIT License
