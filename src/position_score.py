"""
Position Score Module

가우시안 함수를 이용하여 키프레임 간 거리를 평가합니다.
출력 범위: 0~1 (정규화 불필요)
"""

import numpy as np


def calculate_position_score(current_position, last_selected_position, sigma=2.0):
    """
    마지막으로 선택된 키프레임과의 거리를 기반으로 위치 점수를 계산합니다.
    
    Args:
        current_position (np.ndarray): 현재 키프레임의 3D 위치 [x, y, z]
        last_selected_position (np.ndarray): 마지막 선택된 키프레임의 3D 위치 [x, y, z]
        sigma (float): 가우시안 함수의 표준편차 (기본값: 2.0m)
    
    Returns:
        float: 위치 점수 (0~1 범위)
        
    Note:
        - 거리가 0m일 때: 점수 = 1.0 (완전 중복)
        - 거리가 sigma(2.0m)일 때: 점수 ≈ 0.61
        - 거리가 2*sigma(4.0m)일 때: 점수 ≈ 0.14
        - 거리가 3*sigma(6.0m) 이상일 때: 점수 ≈ 0.01 (거의 무관)
    """
    # 유클리드 거리 계산
    distance = np.linalg.norm(current_position - last_selected_position)
    
    # 가우시안 함수 (정규화 상수 제거)
    score = np.exp(-distance**2 / (2 * sigma**2))
    
    return float(score)


def calculate_position_scores_batch(positions, last_selected_position, sigma=2.0):
    """
    여러 키프레임의 위치 점수를 일괄 계산합니다.
    
    Args:
        positions (np.ndarray): 키프레임들의 3D 위치 배열 (N, 3)
        last_selected_position (np.ndarray): 마지막 선택된 키프레임의 3D 위치 [x, y, z]
        sigma (float): 가우시안 함수의 표준편차
    
    Returns:
        np.ndarray: 위치 점수 배열 (N,)
    """
    # 거리 계산 (벡터화)
    distances = np.linalg.norm(positions - last_selected_position, axis=1)
    
    # 가우시안 함수
    scores = np.exp(-distances**2 / (2 * sigma**2))
    
    return scores


def get_distance_score_table(sigma=2.0):
    """
    거리별 점수 예시 테이블을 반환합니다 (논문용).
    
    Args:
        sigma (float): 가우시안 함수의 표준편차
    
    Returns:
        dict: {거리(m): 점수} 딕셔너리
    """
    distances = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
    table = {}
    
    for d in distances:
        score = np.exp(-d**2 / (2 * sigma**2))
        table[d] = round(score, 4)
    
    return table


if __name__ == "__main__":
    # 테스트
    print("=== Position Score Module Test ===\n")
    
    # 예시 위치
    last_pos = np.array([0.0, 0.0, 0.0])
    current_pos = np.array([2.0, 0.0, 0.0])
    
    score = calculate_position_score(current_pos, last_pos, sigma=2.0)
    print(f"마지막 위치: {last_pos}")
    print(f"현재 위치: {current_pos}")
    print(f"거리: {np.linalg.norm(current_pos - last_pos):.2f}m")
    print(f"위치 점수: {score:.4f}\n")
    
    # 거리별 점수 테이블
    print("=== 거리별 점수 테이블 (σ=2.0m) ===")
    table = get_distance_score_table(sigma=2.0)
    print("거리(m) | 점수")
    print("--------|------")
    for dist, score in table.items():
        print(f"{dist:6.1f}  | {score:.4f}")
