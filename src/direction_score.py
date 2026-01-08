"""
Direction Score Module

코사인 유사도를 이용하여 키프레임 간 방향 일치도를 평가합니다.
출력 범위: 0~1 (정규화 적용)
"""

import numpy as np


def quaternion_to_rotation_matrix(q):
    """
    쿼터니언을 회전 행렬로 변환합니다.
    
    Args:
        q (np.ndarray): 쿼터니언 [qx, qy, qz, qw]
    
    Returns:
        np.ndarray: 3x3 회전 행렬
    """
    qx, qy, qz, qw = q
    
    R = np.array([
        [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qz*qw), 2*(qx*qz + qy*qw)],
        [2*(qx*qy + qz*qw), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qx*qw)],
        [2*(qx*qz - qy*qw), 2*(qy*qz + qx*qw), 1 - 2*(qx**2 + qy**2)]
    ])
    
    return R


def get_forward_vector_from_quaternion(q):
    """
    쿼터니언으로부터 전방 벡터(카메라가 바라보는 방향)를 추출합니다.
    
    Args:
        q (np.ndarray): 쿼터니언 [qx, qy, qz, qw]
    
    Returns:
        np.ndarray: 정규화된 전방 벡터 [x, y, z]
    
    Note:
        카메라 좌표계에서 Z축이 전방 방향이라고 가정합니다.
    """
    R = quaternion_to_rotation_matrix(q)
    # Z축 방향 벡터 (카메라 전방)
    forward = R[:, 2]
    return forward / np.linalg.norm(forward)


def get_direction_from_positions(pos1, pos2):
    """
    두 위치 사이의 이동 방향 벡터를 계산합니다.
    
    Args:
        pos1 (np.ndarray): 시작 위치 [x, y, z]
        pos2 (np.ndarray): 끝 위치 [x, y, z]
    
    Returns:
        np.ndarray: 정규화된 방향 벡터 [x, y, z]
    """
    direction = pos2 - pos1
    norm = np.linalg.norm(direction)
    
    if norm < 1e-6:  # 거의 같은 위치
        return np.array([0.0, 0.0, 1.0])  # 기본 전방 방향
    
    return direction / norm


def calculate_direction_score(current_quaternion, reference_direction):
    """
    현재 키프레임의 방향과 참조 방향의 일치도를 계산합니다.
    
    Args:
        current_quaternion (np.ndarray): 현재 키프레임의 쿼터니언 [qx, qy, qz, qw]
        reference_direction (np.ndarray): 참조 방향 벡터 [x, y, z] (정규화됨)
    
    Returns:
        float: 방향 점수 (0~1 범위)
        
    Note:
        - 코사인 유사도 범위: -1 ~ 1
        - 정규화 공식: (cos_sim + 1) / 2
        - 완전 일치(0도): 점수 = 1.0
        - 직각(90도): 점수 = 0.5
        - 반대 방향(180도): 점수 = 0.0
    """
    # 현재 키프레임의 전방 벡터
    current_forward = get_forward_vector_from_quaternion(current_quaternion)
    
    # 코사인 유사도 계산
    cos_sim = np.dot(current_forward, reference_direction)
    
    # 0~1 범위로 정규화
    score = (cos_sim + 1.0) / 2.0
    
    return float(score)


def calculate_direction_score_between_keyframes(kf1_quat, kf1_pos, kf2_pos):
    """
    두 키프레임 사이의 방향 점수를 계산합니다.
    
    Args:
        kf1_quat (np.ndarray): 첫 번째 키프레임의 쿼터니언
        kf1_pos (np.ndarray): 첫 번째 키프레임의 위치
        kf2_pos (np.ndarray): 두 번째 키프레임의 위치
    
    Returns:
        float: 방향 점수 (0~1 범위)
    """
    # 이동 방향 계산
    movement_direction = get_direction_from_positions(kf1_pos, kf2_pos)
    
    # 방향 점수 계산
    score = calculate_direction_score(kf1_quat, movement_direction)
    
    return score


def calculate_direction_scores_batch(quaternions, reference_direction):
    """
    여러 키프레임의 방향 점수를 일괄 계산합니다.
    
    Args:
        quaternions (np.ndarray): 키프레임들의 쿼터니언 배열 (N, 4)
        reference_direction (np.ndarray): 참조 방향 벡터 [x, y, z]
    
    Returns:
        np.ndarray: 방향 점수 배열 (N,)
    """
    scores = np.array([
        calculate_direction_score(q, reference_direction)
        for q in quaternions
    ])
    
    return scores


if __name__ == "__main__":
    # 테스트
    print("=== Direction Score Module Test ===\n")
    
    # 예시 쿼터니언 (단위 쿼터니언: 회전 없음)
    quat = np.array([0.0, 0.0, 0.0, 1.0])
    
    # 참조 방향 (전방)
    ref_direction = np.array([0.0, 0.0, 1.0])
    
    score = calculate_direction_score(quat, ref_direction)
    print(f"쿼터니언: {quat}")
    print(f"참조 방향: {ref_direction}")
    print(f"방향 점수: {score:.4f}\n")
    
    # 다양한 각도에서의 점수
    print("=== 각도별 점수 테이블 ===")
    print("각도(도) | 코사인 유사도 | 정규화 점수")
    print("---------|---------------|-------------")
    
    angles = [0, 30, 60, 90, 120, 150, 180]
    for angle in angles:
        rad = np.radians(angle)
        cos_sim = np.cos(rad)
        normalized_score = (cos_sim + 1.0) / 2.0
        print(f"{angle:7d}  | {cos_sim:13.4f} | {normalized_score:.4f}")
