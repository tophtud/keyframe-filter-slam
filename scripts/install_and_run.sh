#!/bin/bash
# 원라이너 설치 및 실행 스크립트
# 사용법: bash <(curl -fsSL https://raw.githubusercontent.com/tophtud/keyframe-filter-slam/main/scripts/install_and_run.sh)

set -e

echo "========================================="
echo "Grid-Center Waypoint Visualization"
echo "========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 저장소 업데이트
echo -e "${YELLOW}[1/3] Updating repository...${NC}"
cd ~/keyframe-filter-slam
git pull origin main
echo -e "${GREEN}✓ Repository updated${NC}"

# 스크립트 실행
echo -e "${YELLOW}[2/3] Running visualization script...${NC}"
bash scripts/run_waypoint_visualization.sh

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Installation and execution complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
