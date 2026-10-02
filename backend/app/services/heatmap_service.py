from pathlib import Path

import cv2
import numpy as np


class HeatmapService:

    def create_debug_heatmap(
        self,
        frame: np.ndarray,
        output_path: Path,
    ):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY,
        )

        edges = cv2.Canny(
            gray,
            80,
            150,
        )

        heat = cv2.applyColorMap(
            edges,
            cv2.COLORMAP_JET,
        )

        overlay = cv2.addWeighted(
            frame,
            0.72,
            heat,
            0.28,
            0,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(
            str(output_path),
            overlay,
        )


heatmap_service = HeatmapService()