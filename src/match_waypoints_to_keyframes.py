import json
import numpy as np

def match_waypoints_to_keyframes(waypoints_path, keyframe_data_path, output_path, threshold=0.1):
    try:
        with open(waypoints_path, 'r') as f:
            wp_data = json.load(f)
        waypoints = wp_data.get('waypoints', [])
        
        with open(keyframe_data_path, 'r') as f:
            kf_data = json.load(f)
        keyframes = kf_data.get('keyframes', [])
        
        if not waypoints or not keyframes:
            print("Error: No waypoints or keyframes found!")
            return False
        
        print(f"Total Waypoints: {len(waypoints)}")
        print(f"Total Keyframes: {len(keyframes)}")
        print(f"Distance Threshold: {threshold}m\n")
        
        kf_dict = {kf['id']: np.array([kf['x'], kf['y'], kf['z']]) for kf in keyframes}
        
        selected_keyframes = []
        matched_count = 0
        
        print("=== Waypoint-Keyframe Matching ===")
        for i, wp in enumerate(waypoints):
            wp_pos = np.array(wp['position'])
            min_dist = float('inf')
            closest_kf_id = None
            
            for kf_id, kf_pos in kf_dict.items():
                dist = np.linalg.norm(wp_pos - kf_pos)
                if dist < min_dist:
                    min_dist = dist
                    closest_kf_id = kf_id
            
            if min_dist <= threshold:
                selected_keyframes.append(closest_kf_id)
                matched_count += 1
                print(f"  Waypoint {i+1}: Matched to Keyframe {closest_kf_id} (distance: {min_dist:.4f}m)")
            else:
                print(f"  Waypoint {i+1}: No match found (closest: Keyframe {closest_kf_id}, distance: {min_dist:.4f}m)")
        
        unique_keyframes = sorted(set(selected_keyframes))
        
        print("\n=== Matching Results ===")
        print(f"Matched Waypoints: {matched_count}/{len(waypoints)}")
        print(f"Success Rate: {matched_count / len(waypoints) * 100:.1f}%")
        print(f"Unique Keyframes: {len(unique_keyframes)}")
        print(f"Selected Keyframe IDs: {unique_keyframes}")
        
        output_data = {"selected_keyframes": unique_keyframes}
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n✓ Successfully saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--waypoints", required=True)
    parser.add_argument("--keyframe-data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=float, default=0.1)
    
    args = parser.parse_args()
    match_waypoints_to_keyframes(args.waypoints, args.keyframe_data, args.output, args.threshold)
