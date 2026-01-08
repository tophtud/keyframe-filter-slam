# 스코어 모듈 테스트 가이드

새로 작성된 스코어 정규화 모듈들을 테스트하는 방법을 안내합니다.

---

## 전제 조건

```bash
# OpenCV 설치 (Ubuntu)
sudo apt-get install python3-opencv

# 또는 pip로 설치
pip3 install opencv-python numpy
```

---

## 1. Position Score 테스트

```bash
cd ~/keyframe-filter-slam
python3 src/position_score.py
```

**예상 출력:**
```
=== Position Score Module Test ===

마지막 위치: [0. 0. 0.]
현재 위치: [2. 0. 0.]
거리: 2.00m
위치 점수: 0.6065

=== 거리별 점수 테이블 (σ=2.0m) ===
거리(m) | 점수
--------|------
   0.0  | 1.0000
   0.5  | 0.9692
   1.0  | 0.8825
   ...
```

---

## 2. Direction Score 테스트

```bash
python3 src/direction_score.py
```

**예상 출력:**
```
=== Direction Score Module Test ===

쿼터니언: [0. 0. 0. 1.]
참조 방향: [0. 0. 1.]
방향 점수: 1.0000

=== 각도별 점수 테이블 ===
각도(도) | 코사인 유사도 | 정규화 점수
---------|---------------|-------------
      0  |        1.0000 | 1.0000
     30  |        0.8660 | 0.9330
     90  |        0.0000 | 0.5000
    180  |       -1.0000 | 0.0000
```

---

## 3. Quality Score 테스트

```bash
python3 src/quality_score.py
```

**예상 출력:**
```
=== Quality Score Module Test ===

선명한 이미지 분산: 1234.56 (매우 선명)
흐린 이미지 분산: 123.45 (보통)

=== 정규화 결과 ===
원본 분산 | 정규화 점수
----------|-------------
   123.45 | 0.0000
  1234.56 | 1.0000
   678.90 | 0.5000
```

---

## 4. 통합 테스트 (실제 데이터)

실제 stella_vslam의 map.msg 파일로 테스트:

```bash
# 키프레임 데이터 추출
python3 src/extract_keyframes.py \
  --map /path/to/your_map.msg \
  --output-json data/keyframe_data.json

# 스코어 계산 (다음 단계에서 작성 예정)
python3 src/filter.py \
  --keyframe-data data/keyframe_data.json \
  --output results/filtered_keyframes.json
```

---

## 문제 해결

### OpenCV 모듈을 찾을 수 없음

```bash
# Ubuntu
sudo apt-get install python3-opencv

# 또는 pip
pip3 install opencv-python
```

### NumPy 버전 충돌

```bash
pip3 install --upgrade numpy
```

---

## 다음 단계

스코어 모듈 테스트가 완료되면, 다음 작업을 진행합니다:

1. **메인 필터링 로직 작성** (`src/filter.py`)
2. **세미-오토매틱 웨이포인트 생성 로직 추가**
3. **시각화 코드 작성**
