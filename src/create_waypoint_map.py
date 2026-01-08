#!/usr/bin/env python3
"""
웨이포인트 맵 생성기

원본 map.msg 파일에서 선택된 웨이포인트 키프레임만 추출하여
새로운 map.msg 파일을 생성합니다.

stella_vslam 뷰어로 열어서 웨이포인트 위치를 시각적으로 확인할 수 있습니다.
"""

import json
import argparse
import msgpack


def load_map_file(map_file):
    """
    map.msg 파일을 로드합니다.
    
    Args:
        map_file (str): 맵 파일 경로
    
    Returns:
        dict: 맵 데이터
    """
    print(f"맵 파일 로드 중: {map_file}")
    with open(map_file, 'rb') as f:
        map_data = msgpack.unpackb(f.read(), strict_map_key=False)
    print(f"✓ 맵 로드 완료")
    return map_data


def load_waypoints(waypoints_file):
    """
    웨이포인트 JSON 파일을 로드합니다.
    
    Args:
        waypoints_file (str): 웨이포인트 JSON 파일 경로
    
    Returns:
        list: 선택된 키프레임 ID 리스트
    """
    print(f"\n웨이포인트 파일 로드 중: {waypoints_file}")
    with open(waypoints_file, 'r') as f:
        data = json.load(f)
    
    selected_ids = [wp['selected_keyframe_id'] for wp in data['waypoints']]
    print(f"✓ {len(selected_ids)}개의 웨이포인트 로드")
    return selected_ids


def filter_keyframes(map_data, selected_ids):
    """
    선택된 키프레임만 남기고 나머지 제거합니다.
    
    Args:
        map_data (dict): 원본 맵 데이터
        selected_ids (list): 선택된 키프레임 ID 리스트
    
    Returns:
        dict: 필터링된 맵 데이터
    """
    print(f"\n키프레임 필터링 중...")
    
    # 원본 키프레임 개수
    original_keyframes = map_data.get('keyframes', {})
    original_count = len(original_keyframes)
    print(f"  원본 키프레임: {original_count}개")
    
    # 선택된 키프레임만 추출
    filtered_keyframes = {}
    for kf_id_str, kf_data in original_keyframes.items():
        kf_id = int(kf_id_str)
        if kf_id in selected_ids:
            filtered_keyframes[kf_id_str] = kf_data
    
    print(f"  필터링 후: {len(filtered_keyframes)}개")
    print(f"  제거됨: {original_count - len(filtered_keyframes)}개")
    
    # 필터링된 맵 데이터 생성
    filtered_map = map_data.copy()
    filtered_map['keyframes'] = filtered_keyframes
    
    # 연결 정보 업데이트 (span_parent, span_children, loop_edges)
    print(f"\n연결 정보 업데이트 중...")
    for kf_id_str, kf_data in filtered_keyframes.items():
        # span_parent: 부모가 제거되었으면 무효화
        if 'span_parent' in kf_data:
            parent_id = kf_data['span_parent']
            if parent_id != 4294967295 and str(parent_id) not in filtered_keyframes:
                kf_data['span_parent'] = 4294967295  # 무효값
        
        # span_children: 제거된 자식 제외
        if 'span_children' in kf_data:
            valid_children = [
                child_id for child_id in kf_data['span_children']
                if str(child_id) in filtered_keyframes
            ]
            kf_data['span_children'] = valid_children
        
        # loop_edges: 제거된 키프레임과의 엣지 제외
        if 'loop_edges' in kf_data:
            valid_edges = [
                edge_id for edge_id in kf_data['loop_edges']
                if str(edge_id) in filtered_keyframes
            ]
            kf_data['loop_edges'] = valid_edges
    
    print(f"✓ 연결 정보 업데이트 완료")
    
    # 랜드마크 필터링 (선택사항)
    # 웨이포인트 키프레임이 관측하는 랜드마크만 남김
    if 'landmarks' in map_data:
        print(f"\n랜드마크 필터링 중...")
        original_landmarks = map_data['landmarks']
        print(f"  원본 랜드마크: {len(original_landmarks)}개")
        
        # 웨이포인트가 관측하는 랜드마크 ID 수집
        observed_landmark_ids = set()
        for kf_id_str, kf_data in filtered_keyframes.items():
            if 'lm_ids' in kf_data:
                observed_landmark_ids.update(kf_data['lm_ids'])
        
        # 관측되는 랜드마크만 남김
        filtered_landmarks = {}
        for lm_id_str, lm_data in original_landmarks.items():
            lm_id = int(lm_id_str)
            if lm_id in observed_landmark_ids:
                filtered_landmarks[lm_id_str] = lm_data
        
        filtered_map['landmarks'] = filtered_landmarks
        print(f"  필터링 후: {len(filtered_landmarks)}개")
        print(f"  제거됨: {len(original_landmarks) - len(filtered_landmarks)}개")
    
    return filtered_map


def save_map_file(map_data, output_file):
    """
    맵 데이터를 파일로 저장합니다.
    
    Args:
        map_data (dict): 맵 데이터
        output_file (str): 출력 파일 경로
    """
    print(f"\n맵 파일 저장 중: {output_file}")
    with open(output_file, 'wb') as f:
        packed = msgpack.packb(map_data, use_bin_type=True)
        f.write(packed)
    print(f"✓ 저장 완료")


def print_summary(original_map, filtered_map, selected_ids):
    """
    필터링 결과 요약을 출력합니다.
    """
    print(f"\n{'='*60}")
    print(f"=== 필터링 결과 요약 ===")
    print(f"{'='*60}")
    
    print(f"\n키프레임:")
    print(f"  원본: {len(original_map.get('keyframes', {}))}개")
    print(f"  웨이포인트: {len(filtered_map.get('keyframes', {}))}개")
    print(f"  압축률: {len(filtered_map.get('keyframes', {})) / len(original_map.get('keyframes', {})) * 100:.1f}%")
    
    if 'landmarks' in original_map:
        print(f"\n랜드마크:")
        print(f"  원본: {len(original_map.get('landmarks', {}))}개")
        print(f"  필터링 후: {len(filtered_map.get('landmarks', {}))}개")
        print(f"  압축률: {len(filtered_map.get('landmarks', {})) / len(original_map.get('landmarks', {})) * 100:.1f}%")
    
    print(f"\n선택된 키프레임 ID (처음 20개):")
    print(f"  {sorted(selected_ids)[:20]}")
    if len(selected_ids) > 20:
        print(f"  ... (나머지 {len(selected_ids) - 20}개)")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="웨이포인트 키프레임만 포함하는 새 map.msg 파일 생성"
    )
    parser.add_argument('--map', required=True,
                       help='원본 map.msg 파일 경로')
    parser.add_argument('--waypoints', required=True,
                       help='waypoint_generator.py에서 생성한 JSON 파일')
    parser.add_argument('--output', required=True,
                       help='출력 map.msg 파일 경로')
    parser.add_argument('--keep-all-landmarks', action='store_true',
                       help='모든 랜드마크 유지 (기본값: 웨이포인트가 관측하는 것만)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("=== 웨이포인트 맵 생성기 ===")
    print("="*60)
    print(f"원본 맵: {args.map}")
    print(f"웨이포인트: {args.waypoints}")
    print(f"출력 파일: {args.output}")
    print(f"랜드마크 필터링: {'아니오' if args.keep_all_landmarks else '예'}")
    
    # 1. 원본 맵 로드
    original_map = load_map_file(args.map)
    
    # 2. 웨이포인트 로드
    selected_ids = load_waypoints(args.waypoints)
    
    # 3. 키프레임 필터링
    filtered_map = filter_keyframes(original_map, selected_ids)
    
    # 4. 랜드마크 복원 (옵션)
    if args.keep_all_landmarks and 'landmarks' in original_map:
        print(f"\n모든 랜드마크 유지 (--keep-all-landmarks)")
        filtered_map['landmarks'] = original_map['landmarks']
    
    # 5. 결과 저장
    save_map_file(filtered_map, args.output)
    
    # 6. 요약 출력
    print_summary(original_map, filtered_map, selected_ids)
    
    print(f"\n✓ 완료!")
    print(f"\nstella_vslam 뷰어로 확인:")
    print(f"  ./run_map_viewer -v /path/to/vocab.fbow -m {args.output}")


if __name__ == "__main__":
    main()
