from __future__ import annotations

from typing import Any, Dict, List, Union

import pandas as pd
from sklearn.preprocessing import OneHotEncoder


class DataEncoder:
    """
    Handles encoding of categorical features.
    """

    def __init__(self) -> None:
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        self.fitted = False

    def fit_transform(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        columns: List[str],
    ) -> pd.DataFrame:
        """
        Fit the encoder and transform the specified columns.

        Args:
            data: Input data.
            columns: Categorical columns to encode.

        Returns:
            DataFrame with encoded columns added and original categorical columns removed.
        """
        df = pd.DataFrame(data) if isinstance(data, list) else data.copy()
        
        # Filter columns that actually exist
        valid_cols = [col for col in columns if col in df.columns]
        if not valid_cols:
            return df

        encoded_array = self.encoder.fit_transform(df[valid_cols])
        self.fitted = True
        
        feature_names = self.encoder.get_feature_names_out(valid_cols)
        encoded_df = pd.DataFrame(encoded_array, columns=feature_names, index=df.index)
        
        # Drop original columns and concatenate encoded ones
        df = df.drop(columns=valid_cols)
        df = pd.concat([df, encoded_df], axis=1)
        
        return df

    def transform(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        columns: List[str],
    ) -> pd.DataFrame:
        """
        Transform data using the fitted encoder.

        Args:
            data: Input data.
            columns: Categorical columns to encode.

        Returns:
            DataFrame with encoded columns.
        """
        if not self.fitted:
            raise ValueError("Encoder must be fitted before calling transform.")

        df = pd.DataFrame(data) if isinstance(data, list) else data.copy()
        
        valid_cols = [col for col in columns if col in df.columns]
        if not valid_cols:
            return df

        encoded_array = self.encoder.transform(df[valid_cols])
        
        feature_names = self.encoder.get_feature_names_out(valid_cols)
        encoded_df = pd.DataFrame(encoded_array, columns=feature_names, index=df.index)
        
        df = df.drop(columns=valid_cols)
        df = pd.concat([df, encoded_df], axis=1)
        
        return df
