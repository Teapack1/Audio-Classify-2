import librosa
import numpy as np
from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    MaxAbsScaler,
    RobustScaler,
)
import joblib


class Audio_Features:
    def __init__(
        self,
        sample_rate=44100,
        duration=0.4,
        n_mels=128,
        n_mfcc=40,
        n_fft=1024,
        hop_length=512,
        data_range=1,
        scaler_type="standard",  # 'minmax', 'maxabs', 'robust', or None
        use_delta=False,
    ):
        self.sample_rate = sample_rate
        self.duration = duration
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.data_range = data_range
        self.use_delta = use_delta
        self.audio_length = int(sample_rate * duration)

        if scaler_type == "standard":
            self.scaler = StandardScaler()
        elif scaler_type == "minmax":
            self.scaler = MinMaxScaler()
        elif scaler_type == "maxabs":
            self.scaler = MaxAbsScaler()
        elif scaler_type == "robust":
            self.scaler = RobustScaler()
        else:
            self.scaler = None

    def fit_scaler(self, features):
        # Flatten features to fit the scaler on the entire dataset
        features = np.vstack(features)
        if self.scaler:
            self.scaler.fit(features)

    def post_process(self, feature):
        if self.scaler:
            feature = self.scaler.transform(feature)

        feature = (feature - feature.min()) / (feature.max() - feature.min())

        if self.data_range == 255:
            feature = feature * 255.0
            feature = feature.astype(np.uint8)
        elif self.data_range == 1:
            feature = (feature * 2) - 1

        return feature

    def extract_spectrogram(self, y):
        spectrogram = librosa.stft(y=y, n_fft=self.n_fft, hop_length=self.hop_length)
        spectrogram_db = librosa.amplitude_to_db(np.abs(spectrogram), ref=np.max)
        spectrogram_db = self.post_process(spectrogram_db)
        return spectrogram_db.T  # Transpose to ensure time axis is the second dimension

    def extract_mel_spectrogram(self, y):
        mel_spectrogram = librosa.feature.melspectrogram(
            y=y,
            sr=self.sample_rate,
            n_mels=self.n_mels,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )
        mel_spectrogram_db = librosa.power_to_db(mel_spectrogram, ref=np.max)
        mel_spectrogram_db = self.post_process(mel_spectrogram_db)
        return (
            mel_spectrogram_db.T
        )  # Transpose to ensure time axis is the second dimension

    def extract_mfcc(self, y):
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )

        if self.use_delta:
            mfcc_delta = librosa.feature.delta(mfcc)
            mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
            mfcc_combined = np.vstack([mfcc, mfcc_delta, mfcc_delta2])
            mfcc_combined = self.post_process(mfcc_combined)
            return (
                mfcc_combined.T
            )  # Transpose to ensure time axis is the second dimension
        else:
            mfcc = self.post_process(mfcc)
            return mfcc.T  # Transpose to ensure time axis is the second dimension