import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft, fftfreq
from scipy.interpolate import interp1d

# CSVファイルの読み込み
df = pd.read_csv("outputdatas\\waveform_avg.csv")
df = df.drop_duplicates(subset="Time [s]")

# 時間と電圧の抽出
t = df["Time [s]"].values
v = df["Avg Voltage [V]"].values

# 等間隔に補間（FFTの前処理）

# len(t)に対して過大に取らないと失敗する
n_points = 10 * len(t)
t_uniform = np.linspace(t.min(), t.max(), n_points)
interp_func = interp1d(t, v, kind='cubic')
v_uniform = interp_func(t_uniform)

# 中心化（DCオフセット除去）
v_centered = v_uniform - np.mean(v_uniform)

# FFTの実行
V_fft = fft(v_centered)
freq = fftfreq(n_points, d=(t_uniform[1] - t_uniform[0]))

# 振幅のスケーリング
amplitude = 2 * np.abs(V_fft[:n_points//2]) / n_points
freq_half = freq[:n_points//2]

# カットしたりしなかったり
V_fft_filtered = V_fft.copy()
V_fft_filtered[np.abs(V_fft) <= 1e-5 * n_points / 2] = 0  # スケーリングに合わせて調整
amplitude_filtered = 2 * np.abs(V_fft_filtered[:n_points//2]) / n_points

# 振幅スペクトル（対数軸）の表示
plt.figure(figsize=(10, 4))
plt.semilogy(freq_half, amplitude, label='FFT Amplitude (log scale)')
plt.semilogy(freq_half, amplitude_filtered, label='FFT Filtered Amplitude (log scale)')
plt.xlabel("Frequency [Hz]")
plt.ylabel("Amplitude [V] (log scale)")
plt.title("FFT Spectrum (Log Scale)")
plt.grid(True, which='both')
plt.xlim(0, 35)
plt.legend()
plt.tight_layout()
plt.show()

# 逆FFTで復元
v_filtered = np.real(ifft(V_fft_filtered))

# 元データとフィルタ後の比較表示
plt.figure(figsize=(10, 4))
plt.plot(t_uniform, v_uniform, label='Original (Interpolated)', alpha=0.7)
plt.plot(t_uniform, v_filtered, label='Filtered (amp ≤ 1e-5 removed)', alpha=0.7)
plt.xlabel("Time [s]")
plt.ylabel("Voltage [V]")
plt.title("Comparison of Original and Filtered Waveform")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()