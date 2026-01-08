#!/usr/bin/env python3
"""
Main Keyframe Filtering Script

stella_vslam의 map.msg 파일을 읽어서 각 키프레임의 위치, 방향, 품질 점수를 계산합니다.
교수님 피드백 반영: 모든 점수를 0-1로 정규화하여 가중 합산
"""

import msgpack
import numpy as np
import json
import argparse
import os
from position_score import calculate_position_scores_batch
from direction_score import quaternion_to_rotation_matrix, get_direction_from_positions
from quality_score import normalize_quality_scores


def load_map_file(map_file_path):
    """
    stella_vslam의 map.msg 파일을 로드합니다.
    
    Args:
        map_file_path (str): map.msg 파일 경로
    
    Returns:
        dict: 맵 데이터
    """
    print(f"맵 파일 로드 중: {map_file_path}")
    with open(map_file_path, 'rb') as f:
        data = msgpack.unpackb(f.read(), raw=False)
    print(f"맵 데이터 로드 완료")
    return data


def extract_keyframe_data(map_data):
    """
    맵 데이터에서 키프레임 정보를 추출합니다.
    
    Args:
        map_data (dict): 맵 데이터
    
    Returns:
        list: 키프레임 정보 리스트
    """
    keyframes_dict = map_data.get('keyframes', {})
    if not keyframes_dict:
        raise ValueError("맵 파일에 keyframe 데이터가 없습니다!")
    
    print(f"총 {len(keyframes_dict)}개의 Keyframe 발견")
    
    keyframes = []
    for kf_id_str, kf in keyframes_dict.items():
        kf_id = int(kf_id_str)
        
        # 위치 추출
        trans_cw = np.array(kf['trans_cw'])
        quat_cw = np.array(kf['rot_cw'])  # [qx, qy, qz, qw]
        
        # 회전 행렬 변환
        rot_cw = quaternion_to_rotation_matrix(quat_cw)
        
        # 카메라 포즈 (world to camera)
        pose_cw = np.eye(4)
        pose_cw[:3, :3] = rot_cw
        pose_cw[:3, 3] = trans_cw
        
        # 역변환 (camera to world)
        pose_wc = np.linalg.inv(pose_cw)
        position = pose_wc[:3, 3]
        
        # 랜드마크 개수 (품질 평가 보조 지표)
        num_landmarks = len(kf.get('lm_ids', []))
        
        keyframes.append({
            'id': kf_id,
            'position': position,
            'quaternion': quat_cw,
            'num_landmarks': num_landmarks
        })
    
    # ID 순으로 정렬
    keyframes.sort(key=lambda k: k['id'])
    
    return keyframes


def calculate_scores(keyframes, alpha=0.4, beta=0.4, gamma=0.2, sigma=2.0):
    """
    모든 키프레임의 점수를 계산합니다.
    
    Args:
        keyframes (list): 키프레임 정보 리스트
        alpha (float): 위치 점수 가중치
        beta (float): 방향 점수 가중치
        gamma (float): 품질 점수 가중치
        sigma (float): 가우시안 함수의 표준편차
    
    Returns:
        list: 점수가 추가된 키프레임 리스트
    """
    print("\n=== 점수 계산 시작 ===")
    
    n = len(keyframes)
    positions = np.array([kf['position'] for kf in keyframes])
    
    # 1. 위치 점수 계산 (첫 번째 키프레임 기준)
    print("1. 위치 점수 계산 중...")
    first_position = positions[0]
    position_scores = calculate_position_scores_batch(positions, first_position, sigma)
    
    # 2. 방향 점수 계산
    print("2. 방향 점수 계산 중...")
    direction_scores = np.zeros(n)
    
    for i in range(n):
        if i == 0:
            direction_scores[i] = 1.0  # 첫 번째는 기준이므로 만점
        else:
            # 이전 키프레임과의 이동 방향
            movement_dir = get_direction_from_positions(positions[i-1], positions[i])
            
            # 현재 키프레임의 전방 벡터
            R = quaternion_to_rotation_matrix(keyframes[i]['quaternion'])
            forward = R[:, 2]  # Z축 = 전방
            forward = forward / np.linalg.norm(forward)
            
            # 코사인 유사도 계산 및 정규화
            cos_sim = np.dot(forward, movement_dir)
            direction_scores[i] = (cos_sim + 1.0) / 2.0
    
    # 3. 품질 점수 계산 (랜드마크 개수 기반)
    print("3. 품질 점수 계산 중...")
    landmark_counts = np.array([kf['num_landmarks'] for kf in keyframes])
    quality_scores = normalize_quality_scores(landmark_counts)
    
    # 4. 최종 점수 계산 (가중 합산)
    print("4. 최종 점수 계산 중...")
    final_scores = alpha * position_scores + beta * direction_scores + gamma * quality_scores
    
    # 결과 저장
    for i, kf in enumerate(keyframes):
        kf['scores'] = {
            'position': float(position_scores[i]),
            'direction': float(direction_scores[i]),
            'quality': float(quality_scores[i]),
            'final': float(final_scores[i])
        }
    
    print("✓ 점수 계산 완료\n")
    
    return keyframes


def save_results(keyframes, output_path):
    """
    결과를 JSON 파일로 저장합니다.
    
    Args:
        keyframes (list): 점수가 계산된 키프레임 리스트
        output_path (str): 출력 파일 경로
    """
    # NumPy 배열을 리스트로 변환
    output_data = []
    for kf in keyframes:
        output_data.append({
            'id': kf['id'],
            'position': {
                'x': float(kf['position'][0]),
                'y': float(kf['position'][1]),
                'z': float(kf['position'][2])
            },
            'num_landmarks': kf['num_landmarks'],
            'scores': kf['scores']
        })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'keyframes': output_data}, f, indent=2)
    
    print(f"✓ 결과 저장: {output_path}")


def print_statistics(keyframes):
    """
    점수 통계를 출력합니다.
    
    Args:
        keyframes (list): 점수가 계산된 키프레임 리스트
    """
    position_scores = [kf['scores']['position'] for kf in keyframes]
    direction_scores = [kf['scores']['direction'] for kf in keyframes]
    quality_scores = [kf['scores']['quality'] for kf in keyframes]
    final_scores = [kf['scores']['final'] for kf in keyframes]
    
    print("\n=== 점수 통계 ===")
    print(f"위치 점수   - 평균: {np.mean(position_scores):.4f}, 최소: {np.min(position_scores):.4f}, 최대: {np.max(position_scores):.4f}")
    print(f"방향 점수   - 평균: {np.mean(direction_scores):.4f}, 최소: {np.min(direction_scores):.4f}, 최대: {np.max(direction_scores):.4f}")
    print(f"품질 점수   - 평균: {np.mean(quality_scores):.4f}, 최소: {np.min(quality_scores):.4f}, 최대: {np.max(quality_scores):.4f}")
    print(f"최종 점수   - 평균: {np.mean(final_scores):.4f}, 최소: {np.min(final_scores):.4f}, 최대: {np.max(final_scores):.4f}")
    
    # 상위 10개 키프레임
    sorted_kfs = sorted(keyframes, key=lambda k: k['scores']['final'], reverse=True)
    print("\n=== 최종 점수 상위 10개 키프레임 ===")
    print("ID   | 위치    | 방향    | 품질    | 최종")
    print("-----|---------|---------|---------|--------")
    for kf in sorted_kfs[:10]:
        scores = kf['scores']
        print(f"{kf['id']:4d} | {scores['position']:.4f} | {scores['direction']:.4f} | {scores['quality']:.4f} | {scores['final']:.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="stella_vslam map.msg 파일에서 키프레임 점수를 계산합니다."
    )
    parser.add_argument('--map', required=True, help='입력 map.msg 파일 경로')
    parser.add_argument('--output', required=True, help='출력 JSON 파일 경로')
    parser.add_argument('--alpha', type=float, default=0.4, help='위치 점수 가중치 (기본값: 0.4)')
    parser.add_argument('--beta', type=float, default=0.4, help='방향 점수 가중치 (기본값: 0.4)')
    parser.add_argument('--gamma', type=float, default=0.2, help='품질 점수 가중치 (기본값: 0.2)')
    parser.add_argument('--sigma', type=float, default=2.0, help='가우시안 표준편차 (기본값: 2.0m)')
    
    args = parser.parse_args()
    
    # 가중치 합 검증
    weight_sum = args.alpha + args.beta + args.gamma
    if abs(weight_sum - 1.0) > 0.01:
        print(f"경고: 가중치 합이 1.0이 아닙니다 (현재: {weight_sum:.2f})")
    
    print(f"\n=== 키프레임 필터링 시작 ===")
    print(f"입력 파일: {args.map}")
    print(f"가중치: α={args.alpha}, β={args.beta}, γ={args.gamma}")
    print(f"σ={args.sigma}m\n")
    
    # 1. 맵 파일 로드
    map_data = load_map_file(args.map)
    
    # 2. 키프레임 데이터 추출
    keyframes = extract_keyframe_data(map_data)
    
    # 3. 점수 계산
    keyframes = calculate_scores(keyframes, args.alpha, args.beta, args.gamma, args.sigma)
    
    # 4. 결과 저장
    save_results(keyframes, args.output)
    
    # 5. 통계 출력
    print_statistics(keyframes)
    
    print(f"\n✓ 완료!")


if __name__ == "__main__":
    main()
