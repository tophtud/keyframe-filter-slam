#!/usr/bin/env python3
"""
SLAM 맵 파일에서 실제 관측 맵 포인트를 추출하여 커버리지 시각화

사용 방법:
python3 visualize_coverage_with_landmarks_fixed.py \
  --map /home/miix/lib/stella_vslam_examples/data/kyw_3_map.msg \
  --selected /home/miix/lib/stella_vslam_examples/data/waypoint_results_no_dup.json \
  --output-dir ./coverage_results_landmarks
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse
import os

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    print("Warning: msgpack not installed. Install with: sudo pip3 install msgpack")


def quat_to_rotation_matrix(q):
    """
    쿼터니언 [qx, qy, qz, qw]를 3x3 회전 행렬로 변환
    """
    qx, qy, qz, qw = q
    
    # 회전 행렬 계산
    R = np.array([
        [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
    ])
    
    return R


def load_slam_map(map_file):
    """
    SLAM 맵 파일 (.msg)에서 키프레임과 랜드마크 정보 로드
    
    실제 구조:
    - keyframes: 딕셔너리 {id_str: {cam, lm_ids, rot_cw, trans_cw, ...}}
    - landmarks: 딕셔너리 {id_str: {pos_w: [x,y,z], ...}}
    """
    if not MSGPACK_AVAILABLE:
        print("Error: msgpack is required to read SLAM map files")
        return None, None
    
    try:
        with open(map_file, 'rb') as f:
            data = msgpack.unpackb(f.read(), raw=False, strict_map_key=False)
        
        keyframes_dict = data.get('keyframes', {})
        landmarks_dict = data.get('landmarks', {})
        
        # 딕셔너리를 리스트로 변환하면서 ID 추가
        keyframes = []
        for kf_id_str, kf_data in keyframes_dict.items():
            kf_data['id'] = int(kf_id_str)
            keyframes.append(kf_data)
        
        landmarks = []
        for lm_id_str, lm_data in landmarks_dict.items():
            lm_data['id'] = int(lm_id_str)
            landmarks.append(lm_data)
        
        print(f"Loaded {len(keyframes)} keyframes and {len(landmarks)} landmarks from map")
        return keyframes, landmarks
    
    except Exception as e:
        print(f"Error loading map file: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def extract_keyframe_observations(keyframes, landmarks, selected_ids):
    """
    각 선별된 키프레임이 관측하는 실제 랜드마크(맵 포인트) 추출
    """
    # 키프레임 ID를 인덱스로 하는 딕셔너리
    kf_dict = {kf['id']: kf for kf in keyframes}
    
    # 랜드마크 ID를 인덱스로 하는 딕셔너리
    lm_dict = {}
    for lm in landmarks:
        lm_id = lm.get('id')
        pos = lm.get('pos_w')
        if lm_id is not None and pos is not None:
            lm_dict[lm_id] = np.array(pos)
    
    print(f"Valid landmarks with position: {len(lm_dict)}")
    
    observations = {}
    
    for selected_id in selected_ids:
        if selected_id not in kf_dict:
            print(f"Warning: Keyframe {selected_id} not found in map")
            continue
        
        kf = kf_dict[selected_id]
        
        # 키프레임 위치 계산 (올바른 방법)
        rot_cw = kf.get('rot_cw')
        trans_cw = kf.get('trans_cw')
        
        if rot_cw is None or trans_cw is None:
            print(f"Warning: Keyframe {selected_id} has no rotation or translation")
            continue
        
        # 쿼터니언을 회전 행렬로 변환
        R_cw = quat_to_rotation_matrix(np.array(rot_cw))
        
        # 카메라 위치 계산: -R_cw^T * trans_cw
        cam_center = -R_cw.T @ np.array(trans_cw)
        
        # 이 키프레임이 관측하는 랜드마크 ID
        observed_lm_ids = kf.get('lm_ids', [])
        
        # 관측된 랜드마크의 3D 위치
        observed_positions = []
        for lm_id in observed_lm_ids:
            if lm_id in lm_dict:
                observed_positions.append(lm_dict[lm_id])
        
        if len(observed_positions) == 0:
            print(f"Warning: Keyframe {selected_id} has no valid landmark observations")
            continue
        
        observed_positions = np.array(observed_positions)
        
        observations[selected_id] = {
            'camera_position': cam_center,
            'observed_landmarks': observed_positions,
            'num_observations': len(observed_positions)
        }
        
        print(f"  Keyframe {selected_id}: {len(observed_positions)} landmarks observed")
    
    return observations


def calculate_observation_radius(observations):
    """
    각 키프레임의 관측 반경 계산 (실제 랜드마크까지의 거리)
    """
    radius_info = {}
    
    for kf_id, data in observations.items():
        cam_pos = data['camera_position']
        landmarks = data['observed_landmarks']
        
        if len(landmarks) == 0:
            radius_info[kf_id] = {
                'position': cam_pos,
                'avg_radius': 0,
                'max_radius': 0,
                'min_radius': 0,
                'num_landmarks': 0
            }
            continue
        
        # 카메라 위치에서 각 랜드마크까지의 거리
        distances = np.linalg.norm(landmarks - cam_pos, axis=1)
        
        radius_info[kf_id] = {
            'position': cam_pos,
            'avg_radius': np.mean(distances),
            'p90_radius': np.percentile(distances, 90),
            'max_radius': np.max(distances),
            'min_radius': np.min(distances),
            'num_landmarks': len(landmarks),
            'landmarks': landmarks
        }
    
    return radius_info


def visualize_coverage_3d(all_landmarks, selected_ids, radius_info, radius_type='avg', output_file='coverage_3d.png'):
    """
    3D 공간 커버리지 시각화 (실제 랜드마크 포함)
    """
    fig = plt.figure(figsize=(16, 14))
    ax = fig.add_subplot(111, projection='3d')
    
    # 모든 랜드마크 표시 (맵 크기에 따라 동적 조정)
    if len(all_landmarks) > 0:
        # 3D는 너무 많으면 느리므로 적당히 샘플링
        if len(all_landmarks) > 15000:
            indices = np.random.choice(len(all_landmarks), 15000, replace=False)
            sampled_landmarks = all_landmarks[indices]
        else:
            sampled_landmarks = all_landmarks
        
        # 맵 범위 계산
        x_range = sampled_landmarks[:, 0].max() - sampled_landmarks[:, 0].min()
        y_range = sampled_landmarks[:, 1].max() - sampled_landmarks[:, 1].min()
        z_range = sampled_landmarks[:, 2].max() - sampled_landmarks[:, 2].min()
        map_range = max(x_range, y_range, z_range)
        
        # 맵 크기에 따라 포인트 크기 동적 조정 (3D는 2D보다 작게)
        if map_range < 10:  # 작은 맵 (10m 이하)
            point_size = 2
        elif map_range < 20:  # 중간 맵 (10~20m)
            point_size = 3
        elif map_range < 40:  # 큰 맵 (20~40m)
            point_size = 5
        else:  # 매우 큰 맵 (40m 이상)
            point_size = 8
        
        # 동적 크기로 표시
        ax.scatter(sampled_landmarks[:, 0], sampled_landmarks[:, 1], sampled_landmarks[:, 2],
                   c='dimgray', s=5, alpha=0.8, label='Map Points', edgecolors='none')
    
    # 선별된 키프레임과 커버리지 구 표시
    # 파란색 그라데이션 (SLAM 뷰어와 일관성)
    colors = plt.cm.Blues(np.linspace(0.5, 1.0, len(selected_ids)))
    
    for idx, selected_id in enumerate(selected_ids):
        if selected_id not in radius_info:
            continue
        
        info = radius_info[selected_id]
        pos = info['position']
        
        # 키프레임 위치 표시 (작게)
        ax.scatter(pos[0], pos[1], pos[2],
                   c=[colors[idx]], s=100, marker='o', 
                   edgecolors='black', linewidths=2,
                   label=f'KF {selected_id} ({info["num_landmarks"]} pts)' if idx < 5 else '',
                   zorder=10)
        
        # 반경 선택
        if radius_type == 'avg':
            radius = info['avg_radius']
        elif radius_type == 'p90':
            radius = info['p90_radius']
        elif radius_type == 'max':
            radius = info['max_radius']
        else:
            radius = info['min_radius']
        
        if radius == 0:
            continue
        
        # 구(sphere) 표면 생성
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 20)
        x = pos[0] + radius * np.outer(np.cos(u), np.sin(v))
        y = pos[1] + radius * np.outer(np.sin(u), np.sin(v))
        z = pos[2] + radius * np.outer(np.ones(np.size(u)), np.cos(v))
        
        # 투명한 구 표면 그리기
        ax.plot_surface(x, y, z, alpha=0.15, color=colors[idx], 
                        linewidth=0, antialiased=True)
    
    ax.set_xlabel('X (m)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Y (m)', fontsize=14, fontweight='bold')
    ax.set_zlabel('Z (m)', fontsize=14, fontweight='bold')
    ax.set_title(f'Spatial Coverage with Observed Landmarks)', 
                 fontsize=16, fontweight='bold')
    
    ax.legend(loc='upper left', fontsize=11)
    
    # 축 비율 조정
    if len(all_landmarks) > 0:
        max_range = np.array([
            all_landmarks[:, 0].max() - all_landmarks[:, 0].min(),
            all_landmarks[:, 1].max() - all_landmarks[:, 1].min(),
            all_landmarks[:, 2].max() - all_landmarks[:, 2].min()
        ]).max() / 2.0
        
        mid_x = (all_landmarks[:, 0].max() + all_landmarks[:, 0].min()) * 0.5
        mid_y = (all_landmarks[:, 1].max() + all_landmarks[:, 1].min()) * 0.5
        mid_z = (all_landmarks[:, 2].max() + all_landmarks[:, 2].min()) * 0.5
        
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def visualize_coverage_2d(all_landmarks, selected_ids, radius_info, radius_type='avg', output_file='coverage_2d.png'):
    """
    2D 평면도 (Top-down view) 커버리지 시각화
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # 모든 랜드마크 표시 (맵 크기에 따라 동적 조정)
    if len(all_landmarks) > 0:
        # 모든 포인트 표시 (샘플링 안 함)
        sampled_landmarks = all_landmarks
        
        # 맵 범위 계산
        x_range = sampled_landmarks[:, 0].max() - sampled_landmarks[:, 0].min()
        z_range = sampled_landmarks[:, 2].max() - sampled_landmarks[:, 2].min()
        map_range = max(x_range, z_range)
        
        # 맵 크기에 따라 포인트 크기 동적 조정
        if map_range < 10:  # 작은 맵 (10m 이하)
            point_size = 3
        elif map_range < 20:  # 중간 맵 (10~20m)
            point_size = 5
        elif map_range < 40:  # 큰 맵 (20~40m)
            point_size = 8
        else:  # 매우 큰 맵 (40m 이상)
            point_size = 12
        
        # 동적 크기로 표시
        ax.scatter(sampled_landmarks[:, 0], sampled_landmarks[:, 2],
                   c='dimgray', s=point_size, alpha=0.9, label='Map Points', edgecolors='none')
    
    # 선별된 키프레임과 커버리지 원 표시
    # 파란색 그라데이션 (SLAM 뷰어와 일관성)
    colors = plt.cm.Blues(np.linspace(0.5, 1.0, len(selected_ids)))
    
    for idx, selected_id in enumerate(selected_ids):
        if selected_id not in radius_info:
            continue
        
        info = radius_info[selected_id]
        pos = info['position']
        
        # 반경 선택
        if radius_type == 'avg':
            radius = info['avg_radius']
        elif radius_type == 'p90':
            radius = info['p90_radius']
        elif radius_type == 'max':
            radius = info['max_radius']
        else:
            radius = info['min_radius']
        
        if radius > 0:
            # 원 그리기
            circle = plt.Circle((pos[0], pos[2]), radius, 
                                color=colors[idx], alpha=0.2, 
                                linewidth=2, edgecolor=colors[idx], linestyle='--')
            ax.add_patch(circle)
        
        # 키프레임 위치 표시 (작게)
        ax.scatter(pos[0], pos[2],
                   c=[colors[idx]], s=80, marker='o', 
                   edgecolors='black', linewidths=1.5,
                   label=f'KF {selected_id}' if idx < 5 else '',
                   zorder=10)
        
        # 키프레임 ID 텍스트
        ax.text(pos[0], pos[2], f' {selected_id}', 
                fontsize=10, ha='left', va='bottom', fontweight='bold')
    
    ax.set_xlabel('X (m)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Z (m)', fontsize=14, fontweight='bold')
    ax.set_title(f'Spatial Coverage (Top-down View)', 
                 fontsize=16, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def print_statistics(radius_info):
    """
    커버리지 통계 출력
    """
    print("\n" + "="*80)
    print("키프레임 관측 반경 통계 (실제 랜드마크 기반)")
    print("="*80)
    
    
    for kf_id in sorted(radius_info.keys()):
        info = radius_info[kf_id]
        print(f"{kf_id:4d} | {info['num_landmarks']:10d} | "
              f"{info['min_radius']:8.2f} | "
              f"{info['avg_radius']:8.2f} | "
              f"{info['max_radius']:8.2f}")
    
    # 전체 통계
    all_avg = [info['avg_radius'] for info in radius_info.values() if info['avg_radius'] > 0]
    all_max = [info['max_radius'] for info in radius_info.values() if info['max_radius'] > 0]
    all_lm = [info['num_landmarks'] for info in radius_info.values()]
    
    if all_avg:
        print("-"*80)
        print(f"{'전체 평균':>4} | {int(np.mean(all_lm)):10d} | {'':<8} | "
              f"{np.mean(all_avg):8.2f} | {np.mean(all_max):8.2f}")
    print("="*80)


def save_statistics_table(radius_info, output_file='coverage_statistics_landmarks.txt'):
    """
    통계를 텍스트 파일로 저장
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("키프레임 관측 반경 통계 (실제 랜드마크 기반)\n")
        f.write("="*80 + "\n")
        f.write(f"{'ID':>4} | {'Landmarks':>10} | {'Min (m)':>8} | {'Avg (m)':>8} | {'Max (m)':>8}\n")
        f.write("-"*80 + "\n")
        
        for kf_id in sorted(radius_info.keys()):
            info = radius_info[kf_id]
            f.write(f"{kf_id:4d} | {info['num_landmarks']:10d} | "
                    f"{info['min_radius']:8.2f} | "
                    f"{info['avg_radius']:8.2f} | "
                    f"{info['max_radius']:8.2f}\n")
        
        all_avg = [info['avg_radius'] for info in radius_info.values() if info['avg_radius'] > 0]
        all_max = [info['max_radius'] for info in radius_info.values() if info['max_radius'] > 0]
        all_lm = [info['num_landmarks'] for info in radius_info.values()]
        
        if all_avg:
            f.write("-"*80 + "\n")
            f.write(f"{'전체 평균':>4} | {int(np.mean(all_lm)):10d} | {'':<8} | "
                    f"{np.mean(all_avg):8.2f} | {np.mean(all_max):8.2f}\n")
        f.write("="*80 + "\n")
    
    print(f"✓ Saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Visualize keyframe coverage with observed landmarks')
    
    parser.add_argument('--map', required=True,
                        help='Path to SLAM map file (.msg)')
    parser.add_argument('--selected', required=True,
                        help='Path to waypoint_results_no_dup.json file')
    parser.add_argument('--output-dir', default='./coverage_results_landmarks',
                        help='Output directory for visualizations')
    
    args = parser.parse_args()
    
    # 출력 디렉토리 생성
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("="*80)
    print("키프레임 공간 커버리지 시각화 (실제 관측 랜드마크 기반)")
    print("="*80)
    
    # 1. SLAM 맵 로드
    print("\n[1/6] SLAM 맵 파일 로드 중...")
    keyframes, landmarks = load_slam_map(args.map)
    
    if keyframes is None or landmarks is None:
        print("Error: Failed to load SLAM map file")
        return
    
    # 모든 랜드마크 위치 추출
    all_landmarks = []
    for lm in landmarks:
        pos = lm.get('pos_w')
        if pos is not None:
            all_landmarks.append(pos)
    
    if len(all_landmarks) == 0:
        print("Error: No valid landmarks found")
        return
    
    all_landmarks = np.array(all_landmarks)
    print(f"Valid landmarks with position: {len(all_landmarks)}")
    
    # 2. 선별된 키프레임 ID 로드
    print("\n[2/6] 선별된 키프레임 로드 중...")
    with open(args.selected) as f:
        data = json.load(f)
        selected_ids = data.get('selected_keyframes', [])
    
    print(f"  - 전체 키프레임: {len(keyframes)}개")
    print(f"  - 전체 랜드마크: {len(landmarks)}개")
    print(f"  - 선별된 키프레임: {len(selected_ids)}개")
    print(f"  - 선별 비율: {len(selected_ids)/len(keyframes)*100:.1f}%")
    
    # 3. 관측 데이터 추출
    print("\n[3/6] 각 키프레임의 관측 랜드마크 추출 중...")
    observations = extract_keyframe_observations(keyframes, landmarks, selected_ids)
    
    if len(observations) == 0:
        print("Error: No valid observations found")
        return
    
    # 4. 반경 계산
    print("\n[4/6] 관측 반경 계산 중...")
    radius_info = calculate_observation_radius(observations)
    
    # 5. 통계 출력
    print("\n[5/6] 통계 생성 중...")
    print_statistics(radius_info)
    save_statistics_table(radius_info, 
                          os.path.join(args.output_dir, 'coverage_statistics_landmarks.txt'))
    
    # 6. 시각화
    print("\n[6/6] 시각화 생성 중...")
    print("  - 3D 시각화 (평균 반경)...")
    visualize_coverage_3d(all_landmarks, selected_ids, radius_info, 
                          radius_type='avg',
                          output_file=os.path.join(args.output_dir, 'coverage_3d_avg_landmarks.png'))
    
    print("  - 3D 시각화 (P90 반경)...")
    visualize_coverage_3d(all_landmarks, selected_ids, radius_info, 
                          radius_type='p90',
                          output_file=os.path.join(args.output_dir, 'coverage_3d_p90_landmarks.png'))
    
    print("  - 2D 시각화 (평균 반경)...")
    visualize_coverage_2d(all_landmarks, selected_ids, radius_info, 
                          radius_type='avg',
                          output_file=os.path.join(args.output_dir, 'coverage_2d_avg_landmarks.png'))
    
    print("  - 2D 시각화 (P90 반경)...")
    visualize_coverage_2d(all_landmarks, selected_ids, radius_info, 
                          radius_type='p90',
                          output_file=os.path.join(args.output_dir, 'coverage_2d_p90_landmarks.png'))
    
    print("\n" + "="*80)
    print("✓ 모든 시각화 완료!")
    print(f"✓ 결과 저장 위치: {args.output_dir}")
    print("="*80)
    print("\n생성된 파일:")
    print(f"  - coverage_3d_avg_landmarks.png       (3D - 평균 반경)")
    print(f"  - coverage_3d_p90_landmarks.png       (3D - P90 반경)")
    print(f"  - coverage_2d_avg_landmarks.png       (2D - 평균 반경)")
    print(f"  - coverage_2d_p90_landmarks.png       (2D - P90 반경)")
    print(f"  - coverage_statistics_landmarks.txt   (통계 표)")
    print()


if __name__ == '__main__':
    main()
