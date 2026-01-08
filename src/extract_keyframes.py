#!/usr/bin/env python3
import msgpack
import numpy as np
import json
import os

def quaternion_to_rotation_matrix(q):
    """쿼터니언 [x, y, z, w]를 3x3 회전 행렬로 변환"""
    x, y, z, w = q
    R = np.array([
        [1 - 2*(y**2 + z**2),     2*(x*y - w*z),     2*(x*z + w*y)],
        [    2*(x*y + w*z), 1 - 2*(x**2 + z**2),     2*(y*z - w*x)],
        [    2*(x*z - w*y),     2*(y*z + w*x), 1 - 2*(x**2 + y**2)]
    ])
    return R

def extract_keyframes_from_map(map_file_path, output_json_path):
    try:
        print(f"맵 파일 로드 중: {map_file_path}")
        with open(map_file_path, 'rb') as f:
            data = msgpack.unpackb(f.read(), raw=False)
        print(f"맵 데이터 로드 완료")
        keyframes_dict = data.get('keyframes', {})
        if not keyframes_dict:
            print("오류: 맵 파일에 keyframe 데이터가 없습니다!")
            return False
        print(f"총 {len(keyframes_dict)}개의 Keyframe을 발견했습니다.")
        keyframes = []
        for kf_id_str, kf in keyframes_dict.items():
            kf_id = int(kf_id_str)
            trans_cw = np.array(kf['trans_cw'])
            quat_cw = np.array(kf['rot_cw'])
            rot_cw = quaternion_to_rotation_matrix(quat_cw)
            pose_cw = np.eye(4)
            pose_cw[:3, :3] = rot_cw
            pose_cw[:3, 3] = trans_cw
            pose_wc = np.linalg.inv(pose_cw)
            position = pose_wc[:3, 3]
            keyframes.append({
                "id": kf_id,
                "x": float(position[0]),
                "y": float(position[1]),
                "z": float(position[2])
            })
            if len(keyframes) % 50 == 0:
                print(f"  - {len(keyframes)}개 처리 완료...")
        keyframes.sort(key=lambda k: k['id'])
        output_data = {"keyframes": keyframes}
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n✓ 성공! {len(keyframes)}개의 Keyframe 데이터를 저장했습니다:")
        print(f"  {output_json_path}")
        print(f"\n처음 3개 Keyframe 샘플:")
        for kf in keyframes[:3]:
            print(f"  ID {kf['id']}: ({kf['x']:.3f}, {kf['y']:.3f}, {kf['z']:.3f})")
        return True
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SLAM Map 파일에서 Keyframe 좌표를 추출합니다.")
    parser.add_argument("--map", required=True, help="입력 SLAM Map 파일 경로 (.msg)")
    parser.add_argument("--output-json", required=True, help="출력 keyframe_data.json 파일 경로")
    args = parser.parse_args()
    extract_keyframes_from_map(args.map, args.output_json)
