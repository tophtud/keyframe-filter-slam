#!/bin/bash
set -e

echo "========================================="
echo "웨이포인트 시각화 자동화 스크립트"
echo "========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 경로 설정
KEYFRAME_FILTER_DIR="/home/miix/keyframe-filter-slam"
PANGOLIN_VIEWER_DIR="/home/miix/lib/pangolin_viewer"
STELLA_EXAMPLES_DIR="/home/miix/lib/stella_vslam_examples"

MAP_FILE="$KEYFRAME_FILTER_DIR/data/kyw_3_map.msg"
SCORES_FILE="$KEYFRAME_FILTER_DIR/results/kyw_3_scores.json"
WAYPOINTS_FILE="$KEYFRAME_FILTER_DIR/results/kyw_3_auto_waypoints_grid_center.json"

# 1. waypoint_generator.py 복사
echo -e "${YELLOW}[1/6] waypoint_generator.py 업데이트 중...${NC}"
cp /home/ubuntu/waypoint_generator_fixed.py $KEYFRAME_FILTER_DIR/src/waypoint_generator.py
chmod +x $KEYFRAME_FILTER_DIR/src/waypoint_generator.py
echo -e "${GREEN}✓ waypoint_generator.py 업데이트 완료${NC}"

# 2. 키프레임 점수 계산 (이미 있으면 스킵)
if [ ! -f "$SCORES_FILE" ]; then
    echo -e "${YELLOW}[2/6] 키프레임 점수 계산 중...${NC}"
    cd $KEYFRAME_FILTER_DIR
    python3 src/filter.py --map "$MAP_FILE" --output "$SCORES_FILE"
    echo -e "${GREEN}✓ 키프레임 점수 계산 완료${NC}"
else
    echo -e "${GREEN}[2/6] 키프레임 점수 파일 이미 존재 (스킵)${NC}"
fi

# 3. 그리드 중심 웨이포인트 생성
echo -e "${YELLOW}[3/6] 그리드 중심 웨이포인트 생성 중...${NC}"
cd $KEYFRAME_FILTER_DIR
python3 src/waypoint_generator.py \
    --scores "$SCORES_FILE" \
    --grid-size 2.0 \
    --output "$WAYPOINTS_FILE"
echo -e "${GREEN}✓ 웨이포인트 생성 완료: $WAYPOINTS_FILE${NC}"

# 4. viewer.cc 수정
echo -e "${YELLOW}[4/6] viewer.cc 수정 중...${NC}"

# viewer.cc 백업
cp $PANGOLIN_VIEWER_DIR/src/viewer.cc $PANGOLIN_VIEWER_DIR/src/viewer.cc.backup

# load_selected_keyframes 함수 교체
python3 << 'PYTHON_EOF'
import re

# 원본 파일 읽기
with open('/home/miix/lib/pangolin_viewer/src/viewer.cc', 'r') as f:
    content = f.read()

# 새 함수 읽기
with open('/home/ubuntu/viewer_fixed.cc', 'r') as f:
    new_functions = f.read()

# load_selected_keyframes 함수 교체
pattern = r'bool viewer::load_selected_keyframes\(const std::string& json_path\) \{[^}]*(?:\{[^}]*\}[^}]*)*\}'
match = re.search(pattern, content, re.DOTALL)
if match:
    # 새 load_selected_keyframes 추출
    new_load = re.search(r'bool viewer::load_selected_keyframes\(const std::string& json_path\) \{[^}]*(?:\{[^}]*\}[^}]*)*\}', new_functions, re.DOTALL)
    if new_load:
        content = content[:match.start()] + new_load.group() + content[match.end():]
        print("✓ load_selected_keyframes 함수 교체 완료")

# draw_selected_keyframes 함수 교체
pattern = r'void viewer::draw_selected_keyframes\(\) \{[^}]*(?:\{[^}]*\}[^}]*)*\}'
match = re.search(pattern, content, re.DOTALL)
if match:
    # 새 draw_selected_keyframes 추출
    new_draw = re.search(r'void viewer::draw_selected_keyframes\(\) \{[^}]*(?:\{[^}]*\}[^}]*)*\}', new_functions, re.DOTALL)
    if new_draw:
        content = content[:match.start()] + new_draw.group() + content[match.end():]
        print("✓ draw_selected_keyframes 함수 교체 완료")

# 저장
with open('/home/miix/lib/pangolin_viewer/src/viewer.cc', 'w') as f:
    f.write(content)

print("✓ viewer.cc 수정 완료")
PYTHON_EOF

echo -e "${GREEN}✓ viewer.cc 수정 완료${NC}"

# 5. 컴파일
echo -e "${YELLOW}[5/6] 컴파일 중...${NC}"

# pangolin_viewer 컴파일
cd $PANGOLIN_VIEWER_DIR/build
make -j4
sudo make install

# stella_vslam_examples 컴파일
cd $STELLA_EXAMPLES_DIR/build
make -j4

echo -e "${GREEN}✓ 컴파일 완료${NC}"

# 6. 실행
echo -e "${YELLOW}[6/6] Viewer 실행 중...${NC}"
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Viewer가 실행됩니다!${NC}"
echo -e "${GREEN}'Show Selected KFs' 체크박스를 켜면${NC}"
echo -e "${GREEN}그리드 중심에 빨간 점이 표시됩니다.${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

cd $STELLA_EXAMPLES_DIR
./build/run_slam_localization_with_waypoint \
    -v data/orb_vocab.fbow \
    -c /home/miix/lib/stella_vslam/example/aist/insta360_x3_stella_vslam.yaml \
    --video /home/miix/lib/stella_vslam_examples/data/kyw_3/video.mp4 \
    --viewer pangolin_viewer \
    --frame-skip 3 \
    -p "$MAP_FILE"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}작업 완료!${NC}"
echo -e "${GREEN}=========================================${NC}"
