import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict


def detect_copy_move(image_path: Path, output_path: Path):
    """
    Copy-Move Forgery Detection

    Uses:
    1. SIFT feature extraction
    2. Matching descriptors while explicitly removing self-matches
    3. Spatial displacement clustering
    4. Local patch verification

    Compatible with the existing main.py:
        copy_result, copy_file = detect_copy_move(...)
    """

    # --------------------------------------------------
    # 1. READ IMAGE
    # --------------------------------------------------

    img = cv2.imread(str(image_path))

    if img is None:
        raise ValueError("Could not read image.")

    # Keep processing reasonably fast
    max_dimension = 1400

    h, w = img.shape[:2]

    scale = min(
        1.0,
        max_dimension / max(h, w)
    )

    if scale < 1.0:
        img = cv2.resize(
            img,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA
        )

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------
    # 2. SIFT FEATURE EXTRACTION
    # --------------------------------------------------

    sift = cv2.SIFT_create(
        nfeatures=6000,
        contrastThreshold=0.02,
        edgeThreshold=10,
        sigma=1.6
    )

    keypoints, descriptors = sift.detectAndCompute(
        gray,
        None
    )

    if descriptors is None or len(keypoints) < 20:

        cv2.imwrite(
            str(output_path),
            img
        )

        return {
            "possible_forgery": False,
            "matches": 0,
            "message": (
                "Not enough visual features were found "
                "for copy-move analysis."
            )
        }, output_path

    # --------------------------------------------------
    # 3. MATCH DESCRIPTORS
    #
    # IMPORTANT:
    # Do NOT accept the descriptor matching itself.
    # We explicitly remove self-matches first.
    # --------------------------------------------------

    matcher = cv2.BFMatcher(
        cv2.NORM_L2
    )

    raw_matches = matcher.knnMatch(
        descriptors,
        descriptors,
        k=8
    )

    candidate_matches = []

    for match_list in raw_matches:

        # Remove the descriptor matching itself
        non_self = [
            m for m in match_list
            if m.queryIdx != m.trainIdx
        ]

        if len(non_self) < 2:
            continue

        best = non_self[0]
        second = non_self[1]

        # Lowe ratio test
        if best.distance < 0.90 * second.distance:

            p1 = np.array(
                keypoints[best.queryIdx].pt,
                dtype=np.float32
            )

            p2 = np.array(
                keypoints[best.trainIdx].pt,
                dtype=np.float32
            )

            spatial_distance = np.linalg.norm(
                p1 - p2
            )

            # Source and destination must be separated
            if spatial_distance > 40:

                candidate_matches.append(
                    (best, p1, p2)
                )

    # --------------------------------------------------
    # 4. REMOVE DUPLICATE MATCH PAIRS
    # --------------------------------------------------

    unique_pairs = {}

    for match, p1, p2 in candidate_matches:

        a = match.queryIdx
        b = match.trainIdx

        pair_key = tuple(
            sorted((a, b))
        )

        unique_pairs[pair_key] = (
            match,
            p1,
            p2
        )

    candidate_matches = list(
        unique_pairs.values()
    )

    # --------------------------------------------------
    # 5. DISPLACEMENT CLUSTERING
    #
    # Copy-moved regions have approximately the same
    # displacement from source → destination.
    # --------------------------------------------------

    displacement_groups = defaultdict(list)

    for match, p1, p2 in candidate_matches:

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        # 10-pixel bins
        key = (
            int(round(dx / 10)),
            int(round(dy / 10))
        )

        displacement_groups[key].append(
            (match, p1, p2)
        )

    if displacement_groups:

        largest_group = max(
            displacement_groups.values(),
            key=len
        )

    else:

        largest_group = []

    # --------------------------------------------------
    # 6. LOCAL PATCH VERIFICATION
    #
    # This checks whether the image content around
    # the two matched points is actually similar.
    # --------------------------------------------------

    verified_matches = []

    patch_radius = 12

    for match, p1, p2 in largest_group:

        x1, y1 = map(
            int,
            p1
        )

        x2, y2 = map(
            int,
            p2
        )

        # Check boundaries
        if (
            x1 - patch_radius < 0
            or y1 - patch_radius < 0
            or x1 + patch_radius >= gray.shape[1]
            or y1 + patch_radius >= gray.shape[0]
            or x2 - patch_radius < 0
            or y2 - patch_radius < 0
            or x2 + patch_radius >= gray.shape[1]
            or y2 + patch_radius >= gray.shape[0]
        ):
            continue

        patch1 = gray[
            y1 - patch_radius:y1 + patch_radius + 1,
            x1 - patch_radius:x1 + patch_radius + 1
        ]

        patch2 = gray[
            y2 - patch_radius:y2 + patch_radius + 1,
            x2 - patch_radius:x2 + patch_radius + 1
        ]

        # Normalized correlation
        correlation = cv2.matchTemplate(
            patch1,
            patch2,
            cv2.TM_CCOEFF_NORMED
        )[0][0]

        # Strong local similarity
        if correlation >= 0.75:

            verified_matches.append(
                (
                    match,
                    p1,
                    p2,
                    correlation
                )
            )

    # --------------------------------------------------
    # 7. FINAL COUNT
    # --------------------------------------------------

    match_count = len(
        verified_matches
    )

    # A cluster with several verified points is
    # considered a possible copy-move region.
    possible_forgery = (
        match_count >= 6
    )

    # --------------------------------------------------
    # 8. CREATE RESULT IMAGE
    # --------------------------------------------------

    result_img = img.copy()

    for (
        match,
        p1,
        p2,
        correlation
    ) in verified_matches[:60]:

        point1 = tuple(
            map(
                int,
                p1
            )
        )

        point2 = tuple(
            map(
                int,
                p2
            )
        )

        # Source point
        cv2.circle(
            result_img,
            point1,
            6,
            (0, 0, 255),
            2
        )

        # Destination point
        cv2.circle(
            result_img,
            point2,
            6,
            (0, 255, 0),
            2
        )

        # Connection
        cv2.line(
            result_img,
            point1,
            point2,
            (255, 0, 0),
            1
        )

    # --------------------------------------------------
    # 9. RESULT LABEL
    # --------------------------------------------------

    if possible_forgery:

        label = "COPY-MOVE DETECTED"

        message = (
            "Possible copy-move manipulation detected. "
            f"{match_count} verified matching feature pairs found."
        )

    else:

        label = "NO STRONG COPY-MOVE DETECTED"

        message = (
            "No strong copy-move indicator detected. "
            f"{match_count} verified matching feature pairs found."
        )

    cv2.rectangle(
        result_img,
        (10, 10),
        (650, 65),
        (30, 30, 30),
        -1
    )

    cv2.putText(
        result_img,
        label,
        (25, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------
    # 10. SAVE RESULT
    # --------------------------------------------------

    cv2.imwrite(
        str(output_path),
        result_img
    )

    # --------------------------------------------------
    # 11. RETURN EXACT FORMAT EXPECTED BY main.py
    # --------------------------------------------------

    return {
        "possible_forgery": possible_forgery,
        "matches": match_count,
        "message": message
    }, output_path