"""
Quality Score Module

라플라시안 분산을 이용하여 이미지 선명도를 평가합니다.
출력 범위: 0~1 (Min-Max 정규화 적용)
"""

import numpy as np
import cv2


def calculate_laplacian_variance(image):
    """
    이미지의 라플라시안 분산을 계산합니다.
    
    Args:
        image (np.ndarray): 입력 이미지 (그레이스케일 또는 컬러)
    
    Returns:
        float: 라플라시안 분산 값 (높을수록 선명함)
    
    Note:
        - 라플라시안 연산자는 이미지의 2차 미분을 계산합니다.
        - 분산이 높을수록 엣지가 많고 선명한 이미지입니다.
        - 분산이 낮을수록 블러가 심하거나 평탄한 이미지입니다.
    """
    # 그레이스케일 변환 (컬러 이미지인 경우)
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # 라플라시안 연산
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    
    # 분산 계산
    variance = laplacian.var()
    
    return float(variance)


def normalize_quality_scores(laplacian_variances):
    """
    라플라시안 분산 값들을 Min-Max 정규화하여 0~1 범위로 변환합니다.
    
    Args:
        laplacian_variances (np.ndarray): 라플라시안 분산 값 배열
    
    Returns:
        np.ndarray: 정규화된 품질 점수 배열 (0~1 범위)
    
    Note:
        정규화 공식: (값 - 최소값) / (최대값 - 최소값)
    """
    variances = np.array(laplacian_variances)
    
    min_var = variances.min()
    max_var = variances.max()
    
    # 모든 값이 같은 경우 (분모가 0)
    if max_var - min_var < 1e-6:
        return np.ones_like(variances)
    
    # Min-Max 정규화
    normalized = (variances - min_var) / (max_var - min_var)
    
    return normalized


def calculate_quality_score(image, min_variance, max_variance):
    """
    단일 이미지의 정규화된 품질 점수를 계산합니다.
    
    Args:
        image (np.ndarray): 입력 이미지
        min_variance (float): 전체 키프레임 중 최소 라플라시안 분산
        max_variance (float): 전체 키프레임 중 최대 라플라시안 분산
    
    Returns:
        float: 정규화된 품질 점수 (0~1 범위)
    """
    variance = calculate_laplacian_variance(image)
    
    # 분모가 0인 경우
    if max_variance - min_variance < 1e-6:
        return 1.0
    
    # Min-Max 정규화
    score = (variance - min_variance) / (max_variance - min_variance)
    
    # 0~1 범위로 클리핑
    score = np.clip(score, 0.0, 1.0)
    
    return float(score)


def calculate_quality_scores_batch(images):
    """
    여러 이미지의 품질 점수를 일괄 계산합니다.
    
    Args:
        images (list): 이미지 배열 리스트
    
    Returns:
        tuple: (정규화된 점수 배열, 최소 분산, 최대 분산)
    """
    # 모든 이미지의 라플라시안 분산 계산
    variances = np.array([calculate_laplacian_variance(img) for img in images])
    
    # 정규화
    normalized_scores = normalize_quality_scores(variances)
    
    return normalized_scores, variances.min(), variances.max()


def assess_image_quality(variance):
    """
    라플라시안 분산 값을 기반으로 이미지 품질을 평가합니다 (참고용).
    
    Args:
        variance (float): 라플라시안 분산 값
    
    Returns:
        str: 품질 평가 ("매우 선명", "선명", "보통", "흐림", "매우 흐림")
    """
    if variance > 500:
        return "매우 선명"
    elif variance > 200:
        return "선명"
    elif variance > 100:
        return "보통"
    elif variance > 50:
        return "흐림"
    else:
        return "매우 흐림"


if __name__ == "__main__":
    # 테스트
    print("=== Quality Score Module Test ===\n")
    
    # 테스트 이미지 생성 (실제로는 파일에서 로드)
    # 선명한 이미지 (체커보드 패턴)
    sharp_image = np.zeros((100, 100), dtype=np.uint8)
    sharp_image[::10, :] = 255
    sharp_image[:, ::10] = 255
    
    # 흐린 이미지 (가우시안 블러)
    blurry_image = cv2.GaussianBlur(sharp_image, (15, 15), 0)
    
    # 라플라시안 분산 계산
    sharp_var = calculate_laplacian_variance(sharp_image)
    blurry_var = calculate_laplacian_variance(blurry_image)
    
    print(f"선명한 이미지 분산: {sharp_var:.2f} ({assess_image_quality(sharp_var)})")
    print(f"흐린 이미지 분산: {blurry_var:.2f} ({assess_image_quality(blurry_var)})\n")
    
    # 정규화 테스트
    variances = [blurry_var, sharp_var, (sharp_var + blurry_var) / 2]
    normalized = normalize_quality_scores(variances)
    
    print("=== 정규화 결과 ===")
    print("원본 분산 | 정규화 점수")
    print("----------|-------------")
    for var, score in zip(variances, normalized):
        print(f"{var:9.2f} | {score:.4f}")
