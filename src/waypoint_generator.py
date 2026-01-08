#!/usr/bin/env python3
"""
공간 그리드 기반 웨이포인트 자동 생성

3D 공간을 그리드로 나누고, 각 셀에서 최적의 키프레임을 선택하여
웨이포인트를 자동으로 생성합니다.
"""

import json
import argparse
import numpy as np
from collections import defaultdict


def load_keyframe_scores(scores_file):
    """
    filter.py에서 생성한 점수 파일을 로드합니다.
    
    Args:
        scores_file (str): 점수 JSON 파일 경로
    
    Returns:
        list: 키프레임 정보 리스트
    """
    with open(scores_file, 'r') as f:
        data = json.load(f)
    return data['keyframes']


def create_3d_grid(keyframes, grid_size):
    """
    3D 공간을 그리드로 나누고, 각 셀에 키프레임을 할당합니다.
    
    Args:
        keyframes (list): 키프레임 리스트
        grid_size (float): 그리드 셀 크기 (미터)
    
    Returns:
        dict: 그리드 셀 ID → 키프레임 리스트 매핑
    """
    # 맵 전체 범위 계산
    positions = np.array([[kf['position']['x'], kf['position']['y'], kf['position']['z']] 
                          for kf in keyframes])
    
    x_min, y_min, z_min = positions.min(axis=0)
    x_max, y_max, z_max = positions.max(axis=0)
    
    print(f"\n=== 맵 범위 ===")
    print(f"X: {x_min:.2f} ~ {x_max:.2f} (범위: {x_max - x_min:.2f}m)")
    print(f"Y: {y_min:.2f} ~ {y_max:.2f} (범위: {y_max - y_min:.2f}m)")
    print(f"Z: {z_min:.2f} ~ {z_max:.2f} (범위: {z_max - z_min:.2f}m)")
    
    # 그리드 생성
    grid = defaultdict(list)
    
    for kf in keyframes:
        x = kf['position']['x']
        y = kf['position']['y']
        z = kf['position']['z']
        
        # 그리드 셀 인덱스 계산
        cell_x = int((x - x_min) / grid_size)
        cell_y = int((y - y_min) / grid_size)
        cell_z = int((z - z_min) / grid_size)
        
        cell_id = (cell_x, cell_y, cell_z)
        grid[cell_id].append(kf)
    
    print(f"\n=== 그리드 정보 ===")
    print(f"그리드 크기: {grid_size}m")
    print(f"총 셀 개수: {len(grid)}")
    print(f"키프레임이 있는 셀: {len([c for c in grid.values() if len(c) > 0])}")
    
    return grid, (x_min, y_min, z_min)


def select_best_keyframe_per_cell(grid, selection_method='balanced'):
    """
    각 그리드 셀에서 최적의 키프레임을 선택합니다.
    
    Args:
        grid (dict): 그리드 셀 → 키프레임 리스트
        selection_method (str): 선택 방법
            - 'balanced': 방향 + 품질 균형
            - 'quality': 품질 우선
            - 'direction': 방향 우선
    
    Returns:
        list: 선택된 웨이포인트 리스트
    """
    waypoints = []
    
    for cell_id, keyframes_in_cell in grid.items():
        if len(keyframes_in_cell) == 0:
            continue
        
        # 선택 방법에 따라 점수 계산
        if selection_method == 'balanced':
            # 방향 60% + 품질 40%
            best_kf = max(keyframes_in_cell, 
                         key=lambda kf: 0.6 * kf['scores']['direction'] + 
                                       0.4 * kf['scores']['quality'])
        elif selection_method == 'quality':
            # 품질 우선
            best_kf = max(keyframes_in_cell, 
                         key=lambda kf: kf['scores']['quality'])
        elif selection_method == 'direction':
            # 방향 우선
            best_kf = max(keyframes_in_cell, 
                         key=lambda kf: kf['scores']['direction'])
        else:
            # 최종 점수 사용
            best_kf = max(keyframes_in_cell, 
                         key=lambda kf: kf['scores']['final'])
        
        waypoints.append({
            'keyframe_id': best_kf['id'],
            'position': best_kf['position'],
            'grid_cell': cell_id,
            'num_candidates': len(keyframes_in_cell),
            'scores': best_kf['scores']
        })
    
    # 키프레임 ID 순으로 정렬
    waypoints.sort(key=lambda w: w['keyframe_id'])
    
    return waypoints


def calculate_waypoint_statistics(waypoints):
    """
    웨이포인트 통계를 계산합니다.
    
    Args:
        waypoints (list): 웨이포인트 리스트
    
    Returns:
        dict: 통계 정보
    """
    if len(waypoints) == 0:
        return {}
    
    # 웨이포인트 간 거리 계산
    distances = []
    for i in range(1, len(waypoints)):
        pos1 = np.array([waypoints[i-1]['position']['x'],
                        waypoints[i-1]['position']['y'],
                        waypoints[i-1]['position']['z']])
        pos2 = np.array([waypoints[i]['position']['x'],
                        waypoints[i]['position']['y'],
                        waypoints[i]['position']['z']])
        dist = np.linalg.norm(pos2 - pos1)
        distances.append(dist)
    
    # 점수 통계
    direction_scores = [w['scores']['direction'] for w in waypoints]
    quality_scores = [w['scores']['quality'] for w in waypoints]
    final_scores = [w['scores']['final'] for w in waypoints]
    
    stats = {
        'num_waypoints': len(waypoints),
        'avg_distance': np.mean(distances) if distances else 0.0,
        'min_distance': np.min(distances) if distances else 0.0,
        'max_distance': np.max(distances) if distances else 0.0,
        'avg_direction_score': np.mean(direction_scores),
        'avg_quality_score': np.mean(quality_scores),
        'avg_final_score': np.mean(final_scores)
    }
    
    return stats


def print_statistics(stats):
    """
    통계를 출력합니다.
    """
    print(f"\n=== 웨이포인트 통계 ===")
    print(f"생성된 웨이포인트 개수: {stats['num_waypoints']}")
    print(f"\n웨이포인트 간 거리:")
    print(f"  평균: {stats['avg_distance']:.2f}m")
    print(f"  최소: {stats['min_distance']:.2f}m")
    print(f"  최대: {stats['max_distance']:.2f}m")
    print(f"\n평균 점수:")
    print(f"  방향: {stats['avg_direction_score']:.4f}")
    print(f"  품질: {stats['avg_quality_score']:.4f}")
    print(f"  최종: {stats['avg_final_score']:.4f}")


def save_waypoints(waypoints, output_file, stats):
    """
    웨이포인트를 JSON 파일로 저장합니다.
    """
    output_data = {
        'waypoints': waypoints,
        'statistics': stats
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ 웨이포인트 저장: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="공간 그리드 기반 웨이포인트 자동 생성"
    )
    parser.add_argument('--scores', required=True, 
                       help='filter.py에서 생성한 점수 JSON 파일')
    parser.add_argument('--grid-size', type=float, default=2.0,
                       help='그리드 셀 크기 (미터, 기본값: 2.0)')
    parser.add_argument('--method', default='balanced',
                       choices=['balanced', 'quality', 'direction', 'final'],
                       help='키프레임 선택 방법')
    parser.add_argument('--output', required=True,
                       help='출력 JSON 파일 경로')
    
    args = parser.parse_args()
    
    print("=== 공간 그리드 기반 웨이포인트 생성 ===")
    print(f"입력 파일: {args.scores}")
    print(f"그리드 크기: {args.grid_size}m")
    print(f"선택 방법: {args.method}")
    
    # 1. 키프레임 점수 로드
    keyframes = load_keyframe_scores(args.scores)
    print(f"\n총 {len(keyframes)}개의 키프레임 로드")
    
    # 2. 3D 그리드 생성
    grid, origin = create_3d_grid(keyframes, args.grid_size)
    
    # 3. 각 셀에서 최적 키프레임 선택
    waypoints = select_best_keyframe_per_cell(grid, args.method)
    
    # 4. 통계 계산
    stats = calculate_waypoint_statistics(waypoints)
    
    # 5. 통계 출력
    print_statistics(stats)
    
    # 6. 결과 저장
    save_waypoints(waypoints, args.output, stats)
    
    # 7. 샘플 출력
    print(f"\n=== 웨이포인트 샘플 (처음 10개) ===")
    print("ID   | 위치 (x, y, z)                    | 셀 후보 | 방향   | 품질")
    print("-----|-----------------------------------|---------|--------|--------")
    for wp in waypoints[:10]:
        pos = wp['position']
        scores = wp['scores']
        print(f"{wp['keyframe_id']:4d} | "
              f"({pos['x']:6.2f}, {pos['y']:6.2f}, {pos['z']:6.2f}) | "
              f"{wp['num_candidates']:7d} | "
              f"{scores['direction']:.4f} | "
              f"{scores['quality']:.4f}")
    
    print(f"\n✓ 완료!")


if __name__ == "__main__":
    main()
