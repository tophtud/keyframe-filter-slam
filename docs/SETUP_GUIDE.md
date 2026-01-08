# 프로젝트 설정 및 사용 가이드

이 문서는 `keyframe-filter-slam` 프로젝트를 설정하고 사용하는 방법을 안내합니다.

---

## 전제 조건

- **stella_vslam이 설치되어 있어야 합니다.** 설치 방법은 [`installation/README.md`](../installation/README.md)를 참고하세요.
- Python 3.8 이상

---

## 1. 저장소 클론

```bash
git clone https://github.com/tophtud/keyframe-filter-slam.git
cd keyframe-filter-slam
```

---

## 2. Python 패키지 설치

```bash
pip3 install -r requirements.txt
```

---

## 3. 프로젝트 구조

```
keyframe-filter-slam/
├── src/                        # 소스 코드
│   ├── extract_keyframes.py    # 키프레임 데이터 추출
│   ├── generate_waypoints.py   # 웨이포인트 생성
│   ├── visualize_coverage.py   # 커버리지 시각화
│   ├── position_score.py       # 위치 평가 (신규)
│   ├── direction_score.py      # 방향 평가 (신규)
│   ├── quality_score.py        # 품질 평가 (신규)
│   └── filter.py               # 메인 필터링 로직 (신규)
├── config/                     # stella_vslam 설정 파일
│   ├── insta360_x3_stella_vslam.yaml
│   └── equirectangular.yaml
├── data/                       # 데이터 파일
│   └── (map.msg, video.mp4 등)
├── results/                    # 실험 결과
│   ├── figures/               # 그래프 및 시각화
│   └── filtered_maps/         # 필터링된 맵
├── installation/              # stella_vslam 설치 가이드
│   └── README.md
└── docs/                      # 프로젝트 문서
    ├── methodology.md         # 방법론 상세 설명
    └── SETUP_GUIDE.md         # 본 파일
```

---

## 4. 기본 사용 흐름

### 4.1. SLAM 실행 및 맵 생성

```bash
cd ~/stella_vslam_examples

# 비디오로부터 맵 생성
./build/run_video_slam \
  -v data/orb_vocab.fbow \
  -c /path/to/keyframe-filter-slam/config/equirectangular.yaml \
  -m ./data/input_video.mp4 \
  --frame-skip 3 \
  --viewer pangolin_viewer \
  --map-db-out ./data/output_map.msg
```

### 4.2. 키프레임 데이터 추출

```bash
cd /path/to/keyframe-filter-slam

python3 src/extract_keyframes.py \
  --map /path/to/output_map.msg \
  --output-json data/keyframe_data.json
```

### 4.3. 세미-오토매틱 웨이포인트 생성

```bash
python3 src/generate_waypoints.py \
  --keyframe-data data/keyframe_data.json \
  --output data/waypoints.json \
  --num-waypoints 20
```

### 4.4. 커버리지 시각화

```bash
python3 src/visualize_coverage.py \
  --map /path/to/output_map.msg \
  --selected data/waypoints.json \
  --output-dir results/figures/
```

---

## 5. 신규 필터링 알고리즘 사용 (개발 중)

교수님 피드백을 반영한 새로운 다중 평가 지표 기반 필터링:

```bash
python3 src/filter.py \
  --map /path/to/output_map.msg \
  --output results/filtered_maps/filtered_map.msg \
  --alpha 0.4 --beta 0.4 --gamma 0.2
```

---

## 6. 데이터 파일 관리

### 6.1. 대용량 파일 (Git에 포함하지 않음)

- `*.msg` (맵 파일)
- `*.mp4` (비디오 파일)
- `orb_vocab.fbow` (어휘 파일)

이 파일들은 `.gitignore`에 등록되어 있으므로, 별도로 관리하거나 다운로드 링크를 제공하세요.

### 6.2. 샘플 데이터 다운로드

```bash
# ORB 어휘 파일
cd data
wget https://github.com/stella-cv/FBoW_orb_vocab/raw/main/orb_vocab.fbow
```

---

## 7. 문제 해결

### Python 모듈을 찾을 수 없음

```bash
pip3 install msgpack numpy opencv-python matplotlib scipy
```

### stella_vslam 실행 파일을 찾을 수 없음

`installation/README.md`를 참고하여 stella_vslam을 먼저 설치하세요.

---

## 참고 자료

- [방법론 상세 설명](methodology.md)
- [stella_vslam 설치 가이드](../installation/README.md)
- [GitHub 저장소](https://github.com/tophtud/keyframe-filter-slam)
