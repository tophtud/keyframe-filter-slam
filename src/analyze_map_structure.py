#!/usr/bin/env python3
"""
map.msg 파일 구조 분석 스크립트

stella_vslam의 map.msg 파일 내부 구조를 분석하여
키프레임과 랜드마크 정보를 확인합니다.
"""

import msgpack
import sys


def analyze_map_structure(map_file_path):
    """
    map.msg 파일의 구조를 분석합니다.
    """
    print(f"=== map.msg 파일 구조 분석 ===")
    print(f"파일: {map_file_path}\n")
    
    # 파일 로드
    with open(map_file_path, 'rb') as f:
        data = msgpack.unpackb(f.read(), raw=False)
    
    # 최상위 키 확인
    print("1. 최상위 키:")
    for key in data.keys():
        print(f"   - {key}")
    
    # 키프레임 정보
    if 'keyframes' in data:
        keyframes = data['keyframes']
        print(f"\n2. 키프레임 개수: {len(keyframes)}")
        
        # 첫 번째 키프레임 구조 분석
        first_kf_id = list(keyframes.keys())[0]
        first_kf = keyframes[first_kf_id]
        
        print(f"\n3. 키프레임 구조 (ID {first_kf_id}):")
        for key, value in first_kf.items():
            if isinstance(value, list):
                print(f"   - {key}: list (길이 {len(value)})")
                if len(value) > 0 and len(value) <= 10:
                    print(f"      내용: {value}")
            elif isinstance(value, dict):
                print(f"   - {key}: dict (키 개수 {len(value)})")
            else:
                print(f"   - {key}: {type(value).__name__} = {value}")
        
        # 랜드마크 관련 키 찾기
        print(f"\n4. 랜드마크 관련 키:")
        landmark_keys = [k for k in first_kf.keys() if 'landmark' in k.lower()]
        if landmark_keys:
            for key in landmark_keys:
                value = first_kf[key]
                print(f"   - {key}: {type(value).__name__}")
                if isinstance(value, list):
                    print(f"      길이: {len(value)}")
                    if len(value) > 0:
                        print(f"      샘플: {value[:5]}")
        else:
            print("   (랜드마크 관련 키를 찾을 수 없습니다)")
        
        # 여러 키프레임의 랜드마크 개수 확인
        print(f"\n5. 키프레임별 랜드마크 개수 (처음 10개):")
        for i, (kf_id, kf) in enumerate(list(keyframes.items())[:10]):
            if landmark_keys:
                landmark_count = len(kf.get(landmark_keys[0], []))
                print(f"   ID {kf_id}: {landmark_count}개")
            else:
                print(f"   ID {kf_id}: 랜드마크 키를 찾을 수 없음")
    
    # 랜드마크 정보
    if 'landmarks' in data:
        landmarks = data['landmarks']
        print(f"\n6. 랜드마크 개수: {len(landmarks)}")
        
        # 첫 번째 랜드마크 구조 분석
        if len(landmarks) > 0:
            first_lm_id = list(landmarks.keys())[0]
            first_lm = landmarks[first_lm_id]
            
            print(f"\n7. 랜드마크 구조 (ID {first_lm_id}):")
            for key, value in first_lm.items():
                if isinstance(value, list):
                    print(f"   - {key}: list (길이 {len(value)})")
                    if len(value) <= 10:
                        print(f"      내용: {value}")
                else:
                    print(f"   - {key}: {type(value).__name__} = {value}")
    
    # 전체 데이터 구조 요약
    print(f"\n8. 전체 요약:")
    print(f"   - 키프레임: {len(data.get('keyframes', {}))}개")
    print(f"   - 랜드마크: {len(data.get('landmarks', {}))}개")
    
    return data


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 analyze_map_structure.py <map.msg 파일 경로>")
        sys.exit(1)
    
    map_file_path = sys.argv[1]
    analyze_map_structure(map_file_path)


if __name__ == "__main__":
    main()
