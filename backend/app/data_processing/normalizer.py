from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler


class DataNormalizer:
    """
    Handles normalization and standardization of data.
    """

    @staticmethod
    def normalize_image(image: np.ndarray, target_range: tuple = (0, 1)) -> np.ndarray:
        """
        Normalize image pixel values to a target range (e.g., [0, 1] or [-1, 1]).

        Args:
            image: Input image array (H, W, C) or (H, W).
            target_range: Tuple indicating min and max values.

        Returns:
            Normalized image array.
        """
        if image.size == 0:
            return image

        image = image.astype(np.float32)
        min_val, max_val = target_range

        # Assuming input is 0-255 uint8 usually, but we handle general case
        # If we want strict 0-255 to 0-1:
        return image / 255.0 * (max_val - min_val) + min_val

    @staticmethod
    def standardize_labels(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        columns: List[str],
    ) -> pd.DataFrame:
        """
        Standardize numerical labels (Z-Score normalization).

        Args:
            data: Input data.
            columns: Columns to standardize.

        Returns:
            DataFrame with standardized columns.
        """
        df = pd.DataFrame(data) if isinstance(data, list) else data.copy()
        scaler = StandardScaler()

        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                # Reshape for sklearn
                values = df[col].values.reshape(-1, 1)
                df[col] = scaler.fit_transform(values).flatten()

        return df

    @staticmethod
    def minmax_scale_labels(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        columns: List[str],
        feature_range: tuple = (0, 1),
    ) -> pd.DataFrame:
        """
        Min-Max scale numerical labels.

        Args:
            data: Input data.
            columns: Columns to scale.
            feature_range: Target range.

        Returns:
            DataFrame with scaled columns.
        """
        df = pd.DataFrame(data) if isinstance(data, list) else data.copy()
        scaler = MinMaxScaler(feature_range=feature_range)

        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                values = df[col].values.reshape(-1, 1)
                df[col] = scaler.fit_transform(values).flatten()

        return df
