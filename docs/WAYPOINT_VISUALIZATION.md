# Grid-Center Waypoint Visualization

그리드 중심 좌표에 웨이포인트를 표시하는 자동화 도구입니다.

## 🚀 빠른 시작 (원라이너)

```bash
cd ~/keyframe-filter-slam && git pull origin main && bash scripts/run_waypoint_visualization.sh
```

## 📦 포함된 파일

### 1. `src/waypoint_generator.py`
- 3D 그리드 기반 웨이포인트 자동 생성
- 각 그리드 셀의 **중심 좌표** 계산
- `position` 필드에 그리드 중심 좌표 저장

### 2. `patches/viewer_fixed.cc`
- `load_selected_keyframes()`: JSON에서 그리드 중심 좌표 파싱
- `draw_selected_keyframes()`: 그리드 중심에 빨간 점 표시
- 키프레임 위치가 아닌 **그리드 중심 위치** 사용

### 3. `scripts/run_waypoint_visualization.sh`
- 전체 프로세스 자동화
- 키프레임 점수 계산 → 웨이포인트 생성 → viewer.cc 수정 → 컴파일 → 실행

## 🔧 수동 설치

```bash
# 1. 저장소 업데이트
cd ~/keyframe-filter-slam
git pull origin main

# 2. 스크립트 실행
bash scripts/run_waypoint_visualization.sh
```

## 📋 작업 순서

스크립트가 자동으로 수행하는 작업:

1. ✅ `waypoint_generator.py` 업데이트
2. ✅ 키프레임 점수 계산 (`filter.py`)
3. ✅ 그리드 중심 웨이포인트 생성 (2m 간격)
4. ✅ `viewer.cc` 자동 수정
5. ✅ `pangolin_viewer` 컴파일 및 설치
6. ✅ `stella_vslam_examples` 컴파일
7. ✅ Viewer 자동 실행

## 🎯 결과

- **"Show Selected KFs"** 체크박스를 켜면
- 그리드 중심에 **빨간 점**이 표시됩니다
- 키프레임 위치가 아닌 **2m × 2m × 2m 그리드의 중심 좌표**

## 🔍 디버깅

로그에서 다음 메시지를 확인하세요:

```
[INFO] Loading waypoints from: ...
[INFO] Parsing waypoints with grid center positions...
[DEBUG] Waypoint 1: ID=0, pos=(3.5, 0.5, 0.5)
[SUCCESS] Loaded 24 waypoints with grid center positions
[DEBUG] draw_selected_keyframes: waypoints=24
```

## 📝 참고사항

- 그리드 크기: 2.0m (수정 가능)
- 웨이포인트 선택 방법: balanced (방향 60% + 품질 40%)
- 지원 맵: `kyw_3_map.msg` (다른 맵도 가능)

## 🛠️ 문제 해결

### 빨간 점이 보이지 않는 경우

1. 로그에서 `[SUCCESS] Loaded X waypoints` 확인
2. `draw_selected_keyframes: waypoints=X` 확인 (X > 0)
3. JSON 파일 경로 확인

### 컴파일 오류

```bash
# viewer.cc 백업 복원
cp ~/lib/pangolin_viewer/src/viewer.cc.backup ~/lib/pangolin_viewer/src/viewer.cc
```

## 📧 문의

- GitHub: https://github.com/tophtud/keyframe-filter-slam
- Email: gangjunki@gmail.com
