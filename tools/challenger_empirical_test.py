#!/usr/bin/env python3
"""
Empirical Challenger Test Suite: Taste Profiler & Sensory Wheel
==============================================================
Role: Algorithm & Widget Empirical Challenger (Milestone M6)
Target: Innokafe Specialty Coffee Platform (innokafe.insilos.com)

Conducts adversarial stress-testing across:
1. 144 Cartesian combinations of Taste Profiler quiz answers.
2. Geometry & non-degeneracy of 6-axis Sensory Wheel polygons.
3. Live / Offline JSON-RPC endpoint contracts for /taste-profiler/match and /shop/cart/add.
"""

import sys
import os
import math
import json
import urllib.request
import urllib.error
from pathlib import Path

# Add controllers path
CONTROLLERS_DIR = Path("/home/zen/O20/enterprise/innokafe_website/controllers")
sys.path.insert(0, str(CONTROLLERS_DIR))

from main import (
    WEIGHTS,
    D_MAX,
    SIGNATURE_SKUS,
    compute_radar_points,
    calculate_match_scores,
)

BASE_URL = os.environ.get("INNOKAFE_BASE_URL", "http://localhost:28071")


def shoelace_area(points):
    """
    Computes area of a 2D polygon using the Shoelace formula.
    points: list of (x, y) tuples.
    """
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0


def parse_point_string(point_str):
    """Parses 'x1,y1 x2,y2 ...' into list of (float, float)."""
    pts = []
    for pair in point_str.strip().split():
        x, y = pair.split(",")
        pts.append((float(x), float(y)))
    return pts


# ==============================================================================
# TEST 1: QUIZ COMBINATORIAL EXPLORATION & SCORE BOUNDS
# ==============================================================================

def test_quiz_combinations():
    print("\n" + "=" * 70)
    print("TEST 1: TASTE PROFILER QUIZ COMBINATORIAL COVERAGE & SCORE BOUNDS")
    print("=" * 70)

    habits = ["phin_dam", "sua_da", "den_thanh", "coldbrew_sangtao"]
    gears = ["phin", "espresso", "dripbag", "pourover"]
    flavors = ["nutty_choco", "fruity_floral", "honey_balanced"]
    caffeines = ["high", "medium", "low"]

    total_combinations = len(habits) * len(gears) * len(flavors) * len(caffeines)
    print(f"Total valid Cartesian combinations: {total_combinations}")

    out_of_bounds_top1 = []
    out_of_bounds_top2 = []
    empty_recommendations = []
    top1_scores = []
    top2_scores = []
    all_scores = []

    for h in habits:
        for g in gears:
            for f in flavors:
                for c in caffeines:
                    ranked, u_vec = calculate_match_scores(h, g, f, c)
                    
                    if not ranked or len(ranked) == 0:
                        empty_recommendations.append((h, g, f, c))
                        continue
                    
                    top1 = ranked[0]
                    top2 = ranked[1] if len(ranked) > 1 else ranked[0]
                    
                    s1 = top1["match_score"]
                    s2 = top2["match_score"]
                    
                    top1_scores.append(s1)
                    top2_scores.append(s2)
                    for r in ranked:
                        all_scores.append(r["match_score"])

                    # Boundary check for [85.0%, 94.0%]
                    if s1 < 85.0 or s1 > 94.0:
                        out_of_bounds_top1.append((h, g, f, c, s1, top1["name"]))
                    if s2 < 85.0 or s2 > 94.0:
                        out_of_bounds_top2.append((h, g, f, c, s2, top2["name"]))

    print(f"Empty recommendations count: {len(empty_recommendations)}")
    print(f"Top 1 score range: [{min(top1_scores):.1f}%, {max(top1_scores):.1f}%]")
    print(f"Top 2 score range: [{min(top2_scores):.1f}%, {max(top2_scores):.1f}%]")
    print(f"All ranked score range: [{min(all_scores):.1f}%, {max(all_scores):.1f}%]")
    print(f"Top 1 out-of-bounds ([85.0%, 94.0%]): {len(out_of_bounds_top1)} / {total_combinations} ({len(out_of_bounds_top1)/total_combinations*100:.1f}%)")

    if out_of_bounds_top1:
        print("\n[FINDING] Sample combinations violating [85.0%, 94.0%] in Top 1:")
        for entry in out_of_bounds_top1[:8]:
            print(f"  Inputs: habit={entry[0]}, gear={entry[1]}, flavor={entry[2]}, caffeine={entry[3]} -> Score: {entry[4]}% (SKU: {entry[5]})")

    return {
        "total": total_combinations,
        "empty_count": len(empty_recommendations),
        "top1_min": min(top1_scores),
        "top1_max": max(top1_scores),
        "top1_oob_count": len(out_of_bounds_top1),
        "top1_oob_samples": out_of_bounds_top1[:10],
    }


# ==============================================================================
# TEST 2: SENSORY WHEEL RADAR CHART GEOMETRY & NON-DEGENERACY
# ==============================================================================

def test_sensory_wheel_geometry():
    print("\n" + "=" * 70)
    print("TEST 2: SENSORY WHEEL 6-AXIS RADAR CHART GEOMETRY & NON-DEGENERACY")
    print("=" * 70)

    # 1. Test signature catalogue SKUs
    print("Testing 6 signature SKUs pre-computed radar points:")
    sku_results = []
    for sku in SIGNATURE_SKUS:
        pts_str = sku.get("radar_points") or compute_radar_points(sku["sensory_scores"])
        pts = parse_point_string(pts_str)
        area = shoelace_area(pts)
        
        # Check coordinate bounds [0, 300]
        x_coords = [p[0] for p in pts]
        y_coords = [p[1] for p in pts]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        bounded = (0.0 <= x_min and x_max <= 300.0 and 0.0 <= y_min and y_max <= 300.0)
        non_degenerate = (len(pts) == 6 and area > 100.0)

        sku_results.append({
            "sku": sku["sku_code"],
            "area": round(area, 2),
            "x_bounds": (x_min, x_max),
            "y_bounds": (y_min, y_max),
            "bounded": bounded,
            "non_degenerate": non_degenerate,
        })
        print(f"  SKU {sku['sku_code']}: Area = {area:.1f} px², X in [{x_min}, {x_max}], Y in [{y_min}, {y_max}], Valid = {bounded and non_degenerate}")

    # 2. Test boundary and extreme vectors
    print("\nTesting extreme & adversarial sensory score vectors:")
    test_vectors = [
        ("All Minimum (1.0)", {"aroma": 1.0, "acidity": 1.0, "body": 1.0, "sweetness": 1.0, "cleancup": 1.0, "aftertaste": 1.0}),
        ("All Maximum (10.0)", {"aroma": 10.0, "acidity": 10.0, "body": 10.0, "sweetness": 10.0, "cleancup": 10.0, "aftertaste": 10.0}),
        ("All Zero (0.0)", {"aroma": 0.0, "acidity": 0.0, "body": 0.0, "sweetness": 0.0, "cleancup": 0.0, "aftertaste": 0.0}),
        ("Asymmetric Extremum", {"aroma": 10.0, "acidity": 1.0, "body": 10.0, "sweetness": 1.0, "cleancup": 10.0, "aftertaste": 1.0}),
        ("Negative Out-of-Bounds (-5.0)", {"aroma": -5.0, "acidity": 5.0, "body": 5.0, "sweetness": 5.0, "cleancup": 5.0, "aftertaste": 5.0}),
        ("Excessive Out-of-Bounds (25.0)", {"aroma": 25.0, "acidity": 5.0, "body": 5.0, "sweetness": 5.0, "cleancup": 5.0, "aftertaste": 5.0}),
    ]

    vector_results = []
    for name, vec in test_vectors:
        pts_str = compute_radar_points(vec)
        pts = parse_point_string(pts_str)
        area = shoelace_area(pts)
        x_coords = [p[0] for p in pts]
        y_coords = [p[1] for p in pts]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        bounded = (0.0 <= x_min and x_max <= 300.0 and 0.0 <= y_min and y_max <= 300.0)
        non_degenerate = (area > 0.0)
        
        print(f"  {name}: Area = {area:.1f} px², X in [{x_min}, {x_max}], Y in [{y_min}, {y_max}], Bounded = {bounded}, Non-Degenerate = {non_degenerate}")
        vector_results.append({
            "name": name,
            "area": area,
            "bounded": bounded,
            "non_degenerate": non_degenerate,
        })

    return {
        "sku_results": sku_results,
        "vector_results": vector_results,
    }


# ==============================================================================
# TEST 3: LIVE JSON-RPC ENDPOINTS TESTING (/taste-profiler/match & /shop/cart/add)
# ==============================================================================

def test_json_rpc_endpoints():
    print("\n" + "=" * 70)
    print("TEST 3: LIVE JSON-RPC ENDPOINTS VERIFICATION")
    print("=" * 70)

    # 1. Test /taste-profiler/match
    match_url = f"{BASE_URL}/taste-profiler/match"
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "habit": "phin_dam",
            "gear": "phin",
            "flavor": "nutty_choco",
            "caffeine": "high",
        },
        "id": 1,
    }
    print(f"Testing POST {match_url} ...")
    req = urllib.request.Request(
        match_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    match_result = {}
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            match_result["status"] = resp.status
            match_result["body"] = resp.read().decode("utf-8")
            print(f"  Response Status: {resp.status}")
    except urllib.error.HTTPError as e:
        match_result["status"] = e.code
        match_result["error_body"] = e.read().decode("utf-8")[:400]
        print(f"  [ERROR] HTTPError: {e.code}")
        print(f"  Snippet: {match_result['error_body'][:200]}...")
    except Exception as ex:
        match_result["error"] = str(ex)
        print(f"  [ERROR] Connection error: {ex}")

    # 2. Test /shop/cart/add with Taste Profiler payload
    cart_url = f"{BASE_URL}/shop/cart/add"
    cart_payload_profiler = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "product_id": 1,
            "add_qty": 1,
        },
        "id": 2,
    }
    print(f"\nTesting POST {cart_url} with Taste Profiler payload {cart_payload_profiler['params']} ...")
    req_cart1 = urllib.request.Request(
        cart_url,
        data=json.dumps(cart_payload_profiler).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    cart1_result = {}
    try:
        with urllib.request.urlopen(req_cart1, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            cart1_result["status"] = resp.status
            cart1_result["data"] = data
            if "error" in data:
                print(f"  Server returned JSON-RPC Error: {data['error']['message']}")
                print(f"  Detail: {data['error'].get('data', {}).get('message')}")
            else:
                print(f"  Success: {data}")
    except Exception as ex:
        cart1_result["error"] = str(ex)
        print(f"  [ERROR] {ex}")

    # 3. Test /shop/cart/add with required parameters
    cart_payload_standard = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "product_template_id": 1,
            "product_id": 1,
            "quantity": 1,
        },
        "id": 3,
    }
    print(f"\nTesting POST {cart_url} with full positional params {cart_payload_standard['params']} ...")
    req_cart2 = urllib.request.Request(
        cart_url,
        data=json.dumps(cart_payload_standard).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    cart2_result = {}
    try:
        with urllib.request.urlopen(req_cart2, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            cart2_result["status"] = resp.status
            cart2_result["data"] = data
            if "error" in data:
                print(f"  Server returned JSON-RPC Error: {data['error']['message']}")
                print(f"  Exception: {data['error'].get('data', {}).get('name')}")
                print(f"  Detail: {data['error'].get('data', {}).get('message')[:200]}")
            else:
                print(f"  Success: {data}")
    except Exception as ex:
        cart2_result["error"] = str(ex)
        print(f"  [ERROR] {ex}")

    return {
        "match": match_result,
        "cart_profiler": cart1_result,
        "cart_standard": cart2_result,
    }


def main():
    res1 = test_quiz_combinations()
    res2 = test_sensory_wheel_geometry()
    res3 = test_json_rpc_endpoints()

    print("\n" + "=" * 70)
    print("CHALLENGER EMPIRICAL VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
