from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


class DataCleaner:
    """
    Handles missing values and outliers in the dataset.
    """

    @staticmethod
    def handle_missing_values(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        strategy: str = "mean",
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Handle missing values in the data.

        Args:
            data: Input data (DataFrame or list of dicts).
            strategy: Strategy to handle missing values ('mean', 'median', 'mode', 'drop').
            columns: Specific columns to apply the strategy to. If None, applies to all.

        Returns:
            Cleaned DataFrame.
        """
        df = pd.DataFrame(data) if isinstance(data, list) else data.copy()

        if columns is None:
            columns = df.columns.tolist()

        for col in columns:
            if col not in df.columns:
                continue

            if strategy == "drop":
                df.dropna(subset=[col], inplace=True)
            elif strategy == "mean":
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
            elif strategy == "median":
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
            elif strategy == "mode":
                if not df[col].mode().empty:
                    df[col] = df[col].fillna(df[col].mode()[0])

        return df

    @staticmethod
    def remove_outliers(
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        column: str,
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> pd.DataFrame:
        """
        Remove outliers from the data based on a specific column.

        Args:
            data: Input data.
            column: Column to check for outliers.
            method: Method to detect outliers ('iqr', 'z-score').
            threshold: Threshold for detection (1.5 for IQR, 3 for Z-Score).

        Returns:
            DataFrame with outliers removed.
        """
        df = pd.DataFrame(data) if isinstance(data, list) else data.copy()

        if column not in df.columns:
            return df

        if not pd.api.types.is_numeric_dtype(df[column]):
            return df

        if method == "iqr":
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

        elif method == "z-score":
            mean = df[column].mean()
            std = df[column].std()
            if std > 0:
                z_scores = (df[column] - mean) / std
                df = df[abs(z_scores) <= threshold]

        return df
