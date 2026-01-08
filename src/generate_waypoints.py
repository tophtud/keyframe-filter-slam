import json
import numpy as np


def _get_position(kf):
    # supports: (x,y,z) or position:[x,y,z]
    if all(k in kf for k in ("x", "y", "z")):
        return np.array([kf["x"], kf["y"], kf["z"]], dtype=float)
    if "position" in kf and isinstance(kf["position"], (list, tuple)) and len(kf["position"]) >= 3:
        return np.array(kf["position"][:3], dtype=float)
    raise KeyError("Keyframe has no position fields: expected x,y,z or position:[x,y,z]")


def _normalize_quat(q):
    n = float(np.linalg.norm(q))
    if n < 1e-12:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=float)
    return q / n


def _get_orientation_quat(kf):
    # supports: qx,qy,qz,qw or orientation:[qx,qy,qz,qw] or orientation:{x,y,z,w}
    if all(k in kf for k in ("qx", "qy", "qz", "qw")):
        return _normalize_quat(np.array([kf["qx"], kf["qy"], kf["qz"], kf["qw"]], dtype=float))

    if "orientation" in kf:
        o = kf["orientation"]
        if isinstance(o, (list, tuple)) and len(o) >= 4:
            return _normalize_quat(np.array(o[:4], dtype=float))
        if isinstance(o, dict) and all(k in o for k in ("x", "y", "z", "w")):
            return _normalize_quat(np.array([o["x"], o["y"], o["z"], o["w"]], dtype=float))

    return np.array([0.0, 0.0, 0.0, 1.0], dtype=float)


def _sample_indices_linspace(total_kf, num_waypoints):
    if total_kf <= 0:
        return []
    m = int(min(num_waypoints, total_kf))
    idx = np.linspace(0, total_kf - 1, m).round().astype(int)
    idx = np.unique(idx)  # avoid duplicates
    return idx.tolist()


def _sample_by_arclength(keyframes, num_waypoints):
    N = len(keyframes)
    if N == 0:
        return []

    positions = np.vstack([_get_position(kf) for kf in keyframes])  # (N,3)
    seg = np.linalg.norm(positions[1:] - positions[:-1], axis=1)    # (N-1,)
    s = np.concatenate([[0.0], np.cumsum(seg)])                      # (N,)
    total = float(s[-1])

    m = int(min(num_waypoints, N))
    if total < 1e-9:
        # all same position -> fallback
        out = []
        for i in _sample_indices_linspace(N, m):
            out.append((positions[i], _get_orientation_quat(keyframes[i]), i))
        return out

    targets = np.linspace(0.0, total, m)
    out = []
    for t in targets:
        j = int(np.searchsorted(s, t, side="right") - 1)
        j = max(0, min(j, N - 2))

        s0, s1 = s[j], s[j + 1]
        alpha = 0.0 if (s1 - s0) < 1e-12 else float((t - s0) / (s1 - s0))

        p = (1 - alpha) * positions[j] + alpha * positions[j + 1]

        # orientation: nearest endpoint (robust). can upgrade to SLERP later.
        qj = _get_orientation_quat(keyframes[j])
        qk = _get_orientation_quat(keyframes[j + 1])
        q = qj if alpha < 0.5 else qk

        out.append((p, q, j))
    return out


def generate_waypoints_from_keyframe_data(keyframe_data_path, output_path, num_waypoints=20, mode="arclength"):
    try:
        with open(keyframe_data_path, "r") as f:
            kf_data = json.load(f)

        keyframes = kf_data.get("keyframes", [])
        if not keyframes:
            print("Error: No keyframes found! (expected JSON key: 'keyframes')")
            return False

        total_kf = len(keyframes)
        print(f"Total Keyframes: {total_kf}")

        waypoints = []

        if mode == "index":
            indices = _sample_indices_linspace(total_kf, num_waypoints)
            print(f"\n=== Generating {len(indices)} Waypoints (mode=index) ===")
            for wp_id, idx in enumerate(indices, start=1):
                kf = keyframes[idx]
                kf_id = kf.get("id", idx)
                pos = _get_position(kf)
                quat = _get_orientation_quat(kf)

                waypoints.append({
                    "id": wp_id,
                    "position": pos.tolist(),
                    "orientation": quat.tolist(),
                    "source_keyframe_id": kf_id,
                    "source_keyframe_index": idx,
                })
                print(f"  WP{wp_id:02d}: KF {kf_id} idx={idx} pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})")

        else:
            samples = _sample_by_arclength(keyframes, num_waypoints)
            print(f"\n=== Generating {len(samples)} Waypoints (mode=arclength) ===")
            for wp_id, (pos, quat, src_idx) in enumerate(samples, start=1):
                kf = keyframes[src_idx]
                kf_id = kf.get("id", src_idx)

                waypoints.append({
                    "id": wp_id,
                    "position": pos.tolist(),
                    "orientation": quat.tolist(),
                    "source_keyframe_id": kf_id,
                    "source_keyframe_index": src_idx,
                })
                print(f"  WP{wp_id:02d}: near KF {kf_id} idx={src_idx} pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})")

        with open(output_path, "w") as f:
            json.dump({"waypoints": waypoints, "meta": {"mode": mode, "num_waypoints": len(waypoints)}}, f, indent=2)

        print(f"\n✓ Successfully generated {len(waypoints)} waypoints")
        print(f"  Saved to: {output_path}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyframe-data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--num-waypoints", type=int, default=20)
    parser.add_argument("--mode", choices=["index", "arclength"], default="arclength")
    args = parser.parse_args()

    generate_waypoints_from_keyframe_data(args.keyframe_data, args.output, args.num_waypoints, args.mode)

