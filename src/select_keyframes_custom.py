#!/usr/bin/env python3
"""
키프레임 선별 커스터마이징 스크립트

다양한 방법으로 원하는 키프레임을 선택할 수 있습니다.

사용법:
    # 방법 1: 키프레임 ID 직접 지정
    python3 select_keyframes_custom.py \\
        --method manual \\
        --keyframe-ids 10 25 50 75 100 \\
        --output keyframes_manual.json

    # 방법 2: 일정 간격으로 선택
    python3 select_keyframes_custom.py \\
        --method interval \\
        --keyframe-data keyframe_data.json \\
        --interval 20 \\
        --output keyframes_interval.json

    # 방법 3: 거리 기반 간격
    python3 select_keyframes_custom.py \\
        --method distance \\
        --keyframe-data keyframe_data.json \\
        --target-distance 1.5 \\
        --output keyframes_distance.json

    # 방법 4: 특정 영역 필터링
    python3 select_keyframes_custom.py \\
        --method region \\
        --keyframe-data keyframe_data.json \\
        --y-range -10.0 -5.0 \\
        --output keyframes_region.json

    # 방법 5: 회전 구간 선택
    python3 select_keyframes_custom.py \\
        --method turns \\
        --keyframe-data keyframe_data.json \\
        --count 10 \\
        --output keyframes_turns.json
"""

import json
import argparse
import sys
import math
from typing import List, Dict, Tuple


def select_manual(keyframe_ids: List[int]) -> List[Dict]:
    """수동으로 지정한 키프레임 ID 목록"""
    return [{"keyframe_id": kf_id} for kf_id in keyframe_ids]


def select_interval(keyframes: List[Dict], interval: int) -> List[Dict]:
    """일정 간격으로 키프레임 선택"""
    selected_ids = [kf['id'] for i, kf in enumerate(keyframes) if i % interval == 0]
    return [{"keyframe_id": kf_id} for kf_id in selected_ids]


def select_distance(keyframes: List[Dict], target_distance: float) -> List[Dict]:
    """거리 기반 간격으로 키프레임 선택"""
    if not keyframes:
        return []
    
    selected = [keyframes[0]]
    last_pos = (keyframes[0]['x'], keyframes[0]['y'], keyframes[0]['z'])
    
    for kf in keyframes[1:]:
        pos = (kf['x'], kf['y'], kf['z'])
        
        # 거리 계산
        dist = math.sqrt(
            (pos[0] - last_pos[0])**2 +
            (pos[1] - last_pos[1])**2 +
            (pos[2] - last_pos[2])**2
        )
        
        if dist >= target_distance:
            selected.append(kf)
            last_pos = pos
    
    selected_ids = [kf['id'] for kf in selected]
    return [{"keyframe_id": kf_id} for kf_id in selected_ids]


def select_region(keyframes: List[Dict], 
                  x_range: Tuple[float, float] = None,
                  y_range: Tuple[float, float] = None,
                  z_range: Tuple[float, float] = None) -> List[Dict]:
    """특정 영역의 키프레임 선택"""
    selected = []
    
    for kf in keyframes:
        if x_range and not (x_range[0] <= kf['x'] <= x_range[1]):
            continue
        if y_range and not (y_range[0] <= kf['y'] <= y_range[1]):
            continue
        if z_range and not (z_range[0] <= kf['z'] <= z_range[1]):
            continue
        selected.append(kf)
    
    selected_ids = [kf['id'] for kf in selected]
    return [{"keyframe_id": kf_id} for kf_id in selected_ids]


def select_turns(keyframes: List[Dict], count: int) -> List[Dict]:
    """회전이 많은 구간의 키프레임 선택"""
    if len(keyframes) < 3:
        return [{"keyframe_id": kf['id']} for kf in keyframes]
    
    # 헤딩 계산
    headings = []
    for i in range(1, len(keyframes)):
        dx = keyframes[i]['x'] - keyframes[i-1]['x']
        dy = keyframes[i]['y'] - keyframes[i-1]['y']
        heading = math.atan2(dy, dx)
        headings.append(heading)
    
    # 헤딩 변화율 계산
    heading_changes = []
    for i in range(1, len(headings)):
        change = abs(headings[i] - headings[i-1])
        # 각도 wrap-around 처리
        if change > math.pi:
            change = 2*math.pi - change
        heading_changes.append((i, change))
    
    # 헤딩 변화가 큰 상위 N개 선택
    heading_changes.sort(key=lambda x: x[1], reverse=True)
    selected_indices = [idx for idx, _ in heading_changes[:count]]
    selected_indices.sort()
    
    selected_ids = [keyframes[i]['id'] for i in selected_indices]
    return [{"keyframe_id": kf_id} for kf_id in selected_ids]


def select_milestones(keyframes: List[Dict], count: int) -> List[Dict]:
    """경로를 균등하게 나누어 마일스톤 키프레임 선택"""
    total = len(keyframes)
    if count >= total:
        return [{"keyframe_id": kf['id']} for kf in keyframes]
    
    indices = [int(i * total / count) for i in range(count)]
    selected_ids = [keyframes[i]['id'] for i in indices]
    return [{"keyframe_id": kf_id} for kf_id in selected_ids]


def main():
    parser = argparse.ArgumentParser(
        description='키프레임 선별 커스터마이징',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--method', required=True,
                        choices=['manual', 'interval', 'distance', 'region', 'turns', 'milestones'],
                        help='선별 방법')
    parser.add_argument('--keyframe-data', help='keyframe_data.json 파일 경로')
    parser.add_argument('--output', required=True, help='출력 JSON 파일')
    
    # Manual 방법용
    parser.add_argument('--keyframe-ids', nargs='+', type=int,
                        help='수동으로 지정할 키프레임 ID 목록')
    
    # Interval 방법용
    parser.add_argument('--interval', type=int, default=20,
                        help='키프레임 간격 (기본: 20)')
    
    # Distance 방법용
    parser.add_argument('--target-distance', type=float, default=1.5,
                        help='목표 거리 간격 (m, 기본: 1.5)')
    
    # Region 방법용
    parser.add_argument('--x-range', nargs=2, type=float, metavar=('MIN', 'MAX'),
                        help='X 좌표 범위')
    parser.add_argument('--y-range', nargs=2, type=float, metavar=('MIN', 'MAX'),
                        help='Y 좌표 범위')
    parser.add_argument('--z-range', nargs=2, type=float, metavar=('MIN', 'MAX'),
                        help='Z 좌표 범위')
    
    # Turns, Milestones 방법용
    parser.add_argument('--count', type=int, default=10,
                        help='선택할 키프레임 개수 (기본: 10)')
    
    args = parser.parse_args()
    
    # 키프레임 데이터 로드 (manual 방법 제외)
    keyframes = []
    if args.method != 'manual':
        if not args.keyframe_data:
            print("오류: --keyframe-data 옵션이 필요합니다.", file=sys.stderr)
            sys.exit(1)
        
        try:
            with open(args.keyframe_data, 'r') as f:
                data = json.load(f)
            keyframes = data['keyframes']
            print(f"키프레임 데이터 로드: {len(keyframes)}개")
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다: {args.keyframe_data}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"오류: JSON 파싱 실패: {e}", file=sys.stderr)
            sys.exit(1)
    
    # 선별 방법 실행
    print(f"선별 방법: {args.method}")
    
    if args.method == 'manual':
        if not args.keyframe_ids:
            print("오류: --keyframe-ids 옵션이 필요합니다.", file=sys.stderr)
            sys.exit(1)
        selected = select_manual(args.keyframe_ids)
        print(f"수동 지정: {args.keyframe_ids}")
    
    elif args.method == 'interval':
        selected = select_interval(keyframes, args.interval)
        print(f"간격: {args.interval} 프레임")
    
    elif args.method == 'distance':
        selected = select_distance(keyframes, args.target_distance)
        print(f"거리 간격: {args.target_distance}m")
    
    elif args.method == 'region':
        x_range = tuple(args.x_range) if args.x_range else None
        y_range = tuple(args.y_range) if args.y_range else None
        z_range = tuple(args.z_range) if args.z_range else None
        
        if not any([x_range, y_range, z_range]):
            print("오류: 최소 하나의 범위 옵션이 필요합니다 (--x-range, --y-range, --z-range)", file=sys.stderr)
            sys.exit(1)
        
        selected = select_region(keyframes, x_range, y_range, z_range)
        print(f"영역 필터:")
        if x_range:
            print(f"  X: {x_range[0]} ~ {x_range[1]}")
        if y_range:
            print(f"  Y: {y_range[0]} ~ {y_range[1]}")
        if z_range:
            print(f"  Z: {z_range[0]} ~ {z_range[1]}")
    
    elif args.method == 'turns':
        selected = select_turns(keyframes, args.count)
        print(f"회전 구간 상위 {args.count}개")
    
    elif args.method == 'milestones':
        selected = select_milestones(keyframes, args.count)
        print(f"마일스톤 {args.count}개")
    
    # 결과 저장
    output = {"selected_keyframes": selected}
    
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ 선별 완료: {len(selected)}개 키프레임")
    print(f"✓ 저장 완료: {args.output}")
    
    # 샘플 출력
    if selected:
        print("\n선별된 키프레임 ID (처음 10개):")
        sample_ids = [kf['keyframe_id'] for kf in selected[:10]]
        print(f"  {sample_ids}")
        if len(selected) > 10:
            print(f"  ... (총 {len(selected)}개)")


if __name__ == '__main__':
    main()
