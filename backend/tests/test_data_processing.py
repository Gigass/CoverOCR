import numpy as np
import pandas as pd
import pytest
from app.data_processing.cleaner import DataCleaner
from app.data_processing.encoder import DataEncoder
from app.data_processing.normalizer import DataNormalizer


class TestDataProcessing:
    def test_cleaner_missing_values(self):
        data = {
            "A": [1, 2, np.nan, 4],
            "B": ["x", "y", "z", np.nan],
            "C": [10, 10, 10, 10],
        }
        df = pd.DataFrame(data)
        
        # Test mean strategy
        cleaned_mean = DataCleaner.handle_missing_values(df, strategy="mean", columns=["A"])
        assert cleaned_mean["A"].isnull().sum() == 0
        assert cleaned_mean["A"][2] == 7/3  # Mean of 1, 2, 4

        # Test mode strategy
        cleaned_mode = DataCleaner.handle_missing_values(df, strategy="mode", columns=["B"])
        assert cleaned_mode["B"].isnull().sum() == 0
        # Mode could be x, y, or z depending on implementation stability, but shouldn't be nan

    def test_cleaner_outliers(self):
        data = {"val": [1, 2, 3, 4, 100]}  # 100 is outlier
        df = pd.DataFrame(data)
        
        cleaned = DataCleaner.remove_outliers(df, "val", method="iqr")
        assert 100 not in cleaned["val"].values
        assert len(cleaned) == 4

    def test_normalizer_image(self):
        img = np.array([[0, 127.5, 255]], dtype=np.uint8)
        norm = DataNormalizer.normalize_image(img, target_range=(0, 1))
        
        assert norm.min() == 0.0
        assert norm.max() == 1.0
        assert np.isclose(norm[0, 1], 0.5, atol=0.01)

    def test_normalizer_standardize(self):
        data = {"val": [1, 2, 3, 4, 5]}
        df = pd.DataFrame(data)
        
        standardized = DataNormalizer.standardize_labels(df, columns=["val"])
        assert np.isclose(standardized["val"].mean(), 0, atol=0.01)
        assert np.isclose(standardized["val"].std(ddof=0), 1, atol=0.01)

    def test_encoder_one_hot(self):
        data = {"cat": ["A", "B", "A", "C"]}
        df = pd.DataFrame(data)
        
        encoder = DataEncoder()
        encoded = encoder.fit_transform(df, columns=["cat"])
        
        assert "cat_A" in encoded.columns
        assert "cat_B" in encoded.columns
        assert "cat_C" in encoded.columns
        assert encoded.iloc[0]["cat_A"] == 1
        assert encoded.iloc[1]["cat_B"] == 1
