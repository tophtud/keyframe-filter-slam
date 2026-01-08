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
        tuple: (그리드 셀 ID → 키프레임 리스트 매핑, 맵 최소 좌표)
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


def select_best_keyframe_per_cell(grid, grid_min, grid_size, selection_method='balanced'):
    """
    각 그리드 셀에서 최적의 키프레임을 선택하고, 그리드 중심 좌표를 계산합니다.
    
    Args:
        grid (dict): 그리드 셀 ID → 키프레임 리스트 매핑
        grid_min (tuple): 맵 최소 좌표 (x_min, y_min, z_min)
        grid_size (float): 그리드 셀 크기
        selection_method (str): 선택 방법 ('balanced', 'quality', 'direction')
    
    Returns:
        list: 선택된 웨이포인트 리스트
    """
    waypoints = []
    x_min, y_min, z_min = grid_min
    
    for cell_id, keyframes_in_cell in grid.items():
        if not keyframes_in_cell:
            continue
        
        # 각 키프레임의 선택 점수 계산
        candidates_with_scores = []
        for kf in keyframes_in_cell:
            if selection_method == 'balanced':
                selection_score = 0.6 * kf['scores']['direction'] + 0.4 * kf['scores']['quality']
            elif selection_method == 'quality':
                selection_score = kf['scores']['quality']
            elif selection_method == 'direction':
                selection_score = kf['scores']['direction']
            else:
                selection_score = kf['scores']['final']
            
            candidates_with_scores.append({
                'keyframe_id': kf['id'],
                'position': kf['position'],
                'scores': kf['scores'],
                'selection_score': selection_score,
                'num_landmarks': kf['num_landmarks']
            })
        
        # 선택 점수 기준으로 정렬 (높은 순)
        candidates_with_scores.sort(key=lambda c: c['selection_score'], reverse=True)
        
        # 최고 점수 키프레임 선택
        best_kf = candidates_with_scores[0]
        
        # 그리드 셀의 중심 좌표 계산
        grid_x, grid_y, grid_z = cell_id
        center_x = (grid_x + 0.5) * grid_size + x_min
        center_y = (grid_y + 0.5) * grid_size + y_min
        center_z = (grid_z + 0.5) * grid_size + z_min
        
        waypoints.append({
            'id': best_kf['keyframe_id'],
            'position': {
                'x': center_x,
                'y': center_y,
                'z': center_z
            },
            'grid_center_position': {
                'x': center_x,
                'y': center_y,
                'z': center_z
            },
            'selected_keyframe_id': best_kf['keyframe_id'],
            'selected_position': best_kf['position'],
            'selected_scores': best_kf['scores'],
            'selection_score': best_kf['selection_score'],
            'grid_cell': list(cell_id),
            'num_candidates': len(keyframes_in_cell),
            'all_candidates': candidates_with_scores
        })
    
    # 선택된 키프레임 ID 순으로 정렬
    waypoints.sort(key=lambda w: w['selected_keyframe_id'])
    
    return waypoints


def calculate_waypoint_statistics(waypoints):
    """
    웨이포인트 통계를 계산합니다.
    
    Args:
        waypoints (list): 웨이포인트 리스트
    
    Returns:
        dict: 통계 정보
    """
    if not waypoints:
        return {}
    
    # 웨이포인트 간 거리 계산
    distances = []
    for i in range(1, len(waypoints)):
        pos1 = np.array([waypoints[i-1]['grid_center_position']['x'],
                        waypoints[i-1]['grid_center_position']['y'],
                        waypoints[i-1]['grid_center_position']['z']])
        pos2 = np.array([waypoints[i]['grid_center_position']['x'],
                        waypoints[i]['grid_center_position']['y'],
                        waypoints[i]['grid_center_position']['z']])
        dist = np.linalg.norm(pos2 - pos1)
        distances.append(dist)
    
    # 점수 통계
    scores = [wp['selection_score'] for wp in waypoints]
    
    stats = {
        'num_waypoints': len(waypoints),
        'avg_distance': np.mean(distances) if distances else 0,
        'min_distance': np.min(distances) if distances else 0,
        'max_distance': np.max(distances) if distances else 0,
        'avg_score': np.mean(scores),
        'min_score': np.min(scores),
        'max_score': np.max(scores)
    }
    
    return stats


def print_waypoint_summary(waypoints, stats):
    """
    웨이포인트 요약 정보를 출력합니다.
    """
    print(f"\n=== 웨이포인트 생성 완료 ===")
    print(f"총 웨이포인트 개수: {stats['num_waypoints']}")
    print(f"\n거리 통계:")
    print(f"  평균 간격: {stats['avg_distance']:.2f}m")
    print(f"  최소 간격: {stats['min_distance']:.2f}m")
    print(f"  최대 간격: {stats['max_distance']:.2f}m")
    print(f"\n점수 통계:")
    print(f"  평균 점수: {stats['avg_score']:.4f}")
    print(f"  최소 점수: {stats['min_score']:.4f}")
    print(f"  최대 점수: {stats['max_score']:.4f}")


def print_detailed_waypoints(waypoints):
    """
    웨이포인트 상세 정보를 출력합니다.
    """
    print(f"\n=== 웨이포인트 상세 정보 ===")
    for i, wp in enumerate(waypoints):
        print(f"\n[웨이포인트 {i+1}]")
        print(f"  선택된 키프레임: ID {wp['selected_keyframe_id']}")
        print(f"  그리드 중심 위치: ({wp['grid_center_position']['x']:.2f}, {wp['grid_center_position']['y']:.2f}, {wp['grid_center_position']['z']:.2f})")
        print(f"  키프레임 원래 위치: ({wp['selected_position']['x']:.2f}, {wp['selected_position']['y']:.2f}, {wp['selected_position']['z']:.2f})")
        print(f"  선택 점수: {wp['selection_score']:.4f}")
        print(f"  그리드 셀: {wp['grid_cell']}")
        print(f"  후보 개수: {wp['num_candidates']}")
        
        if wp['num_candidates'] > 1:
            print(f"  다른 후보들:")
            for cand in wp['all_candidates'][:3]:  # 상위 3개만
                selected_marker = "*" if cand['keyframe_id'] == wp['selected_keyframe_id'] else " "
                print(f"    {selected_marker} ID {cand['keyframe_id']}: 점수 {cand['selection_score']:.4f}")


def main():
    parser = argparse.ArgumentParser(description='공간 그리드 기반 웨이포인트 자동 생성')
    parser.add_argument('--scores', required=True, help='키프레임 점수 JSON 파일')
    parser.add_argument('--grid-size', type=float, default=2.0, help='그리드 셀 크기 (미터)')
    parser.add_argument('--selection-method', default='balanced',
                       choices=['balanced', 'quality', 'direction', 'final'],
                       help='키프레임 선택 방법')
    parser.add_argument('--output', required=True, help='출력 JSON 파일')
    parser.add_argument('--verbose', action='store_true', help='상세 정보 출력')
    
    args = parser.parse_args()
    
    # 키프레임 점수 로드
    print(f"키프레임 점수 로드 중: {args.scores}")
    keyframes = load_keyframe_scores(args.scores)
    print(f"총 {len(keyframes)}개의 키프레임 로드됨")
    
    # 3D 그리드 생성
    grid, grid_min = create_3d_grid(keyframes, args.grid_size)
    
    # 각 셀에서 최적 키프레임 선택
    print(f"\n=== 웨이포인트 선택 중 (방법: {args.selection_method}) ===")
    waypoints = select_best_keyframe_per_cell(grid, grid_min, args.grid_size, args.selection_method)
    
    # 통계 계산
    stats = calculate_waypoint_statistics(waypoints)
    
    # 결과 출력
    print_waypoint_summary(waypoints, stats)
    
    if args.verbose:
        print_detailed_waypoints(waypoints)
    
    # JSON 저장
    output_data = {
        'waypoints': waypoints,
        'statistics': stats,
        'parameters': {
            'grid_size': args.grid_size,
            'selection_method': args.selection_method,
            'num_total_keyframes': len(keyframes)
        }
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n웨이포인트 저장 완료: {args.output}")


if __name__ == '__main__':
    main()
