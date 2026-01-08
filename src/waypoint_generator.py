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
        
        # 모든 후보에 대해 선택 점수 계산
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
        
        waypoints.append({
            'selected_keyframe_id': best_kf['keyframe_id'],
            'selected_position': best_kf['position'],
            'selected_scores': best_kf['scores'],
            'selection_score': best_kf['selection_score'],
            'grid_cell': cell_id,
            'num_candidates': len(keyframes_in_cell),
            'all_candidates': candidates_with_scores  # 모든 후보 정보 포함
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
    if len(waypoints) == 0:
        return {}
    
    # 웨이포인트 간 거리 계산
    distances = []
    for i in range(1, len(waypoints)):
        pos1 = np.array([waypoints[i-1]['selected_position']['x'],
                        waypoints[i-1]['selected_position']['y'],
                        waypoints[i-1]['selected_position']['z']])
        pos2 = np.array([waypoints[i]['selected_position']['x'],
                        waypoints[i]['selected_position']['y'],
                        waypoints[i]['selected_position']['z']])
        dist = np.linalg.norm(pos2 - pos1)
        distances.append(dist)
    
    # 점수 통계
    direction_scores = [w['selected_scores']['direction'] for w in waypoints]
    quality_scores = [w['selected_scores']['quality'] for w in waypoints]
    final_scores = [w['selected_scores']['final'] for w in waypoints]
    
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
    # 저장용 데이터 준비 (간결한 버전과 상세 버전 모두 포함)
    output_data = {
        'waypoints': waypoints,
        'statistics': stats,
        'summary': {
            'total_waypoints': len(waypoints),
            'selection_method': 'See statistics for details'
        }
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
    print(f"\n=== 웨이포인트 샘플 (처음 5개) ===")
    for i, wp in enumerate(waypoints[:5]):
        print(f"\n[웨이포인트 #{i+1}] 그리드 셀: {wp['grid_cell']}")
        print(f"  선택된 키프레임: ID {wp['selected_keyframe_id']}")
        print(f"  위치: ({wp['selected_position']['x']:.2f}, {wp['selected_position']['y']:.2f}, {wp['selected_position']['z']:.2f})")
        print(f"  선택 점수: {wp['selection_score']:.4f}")
        print(f"  후보 키프레임 개수: {wp['num_candidates']}")
        print(f"\n  모든 후보:")
        print(f"  ID   | 위치 (x, y, z)          | 선택점수 | 방향   | 품질   | 랜드마크")
        print(f"  -----|---------------------------|----------|--------|--------|----------")
        for cand in wp['all_candidates'][:10]:  # 최대 10개만 표시
            pos = cand['position']
            selected_marker = "*" if cand['keyframe_id'] == wp['selected_keyframe_id'] else " "
            print(f"{selected_marker} {cand['keyframe_id']:4d} | "
                  f"({pos['x']:5.2f},{pos['y']:5.2f},{pos['z']:5.2f}) | "
                  f"{cand['selection_score']:8.4f} | "
                  f"{cand['scores']['direction']:6.4f} | "
                  f"{cand['scores']['quality']:6.4f} | "
                  f"{cand['num_landmarks']:9d}")
        if wp['num_candidates'] > 10:
            print(f"  ... (나머지 {wp['num_candidates'] - 10}개 생략)")
    
    print(f"\n✓ 완료!")


if __name__ == "__main__":
    main()
