import sys
import time
import csv
from PyQt6 import QtWidgets, QtCore
import pyvisa
import pyqtgraph as pg


class OscilloAvgPlot(QtWidgets.QMainWindow):
    def __init__(
        self, resource_str, csv_path="waveform_avg.csv", interval_ms=10, window_sec=10
    ):
        super().__init__()
        self.setWindowTitle("Average Voltage Trace")
        self.window_sec = window_sec
        self.csv_path = csv_path

        # CSV ヘッダ作成
        with open(self.csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time [s]", "Avg Voltage [V]"])

        # --- VISA／Scope 初期化
        self.rm = pyvisa.ResourceManager()
        self.scope = self.rm.open_resource(resource_str)
        self.scope.timeout = 10000  # ms

        # 波形設定：BYTE バイナリ
        self.scope.write(":WAVeform:SOURce CHAN1")
        self.scope.write(":WAVeform:MODE NORMal")
        self.scope.write(":WAVeform:FORMat BYTE")
        self.scope.write(":WAVeform:ENCdg RIBinary")
        self.scope.write(":WAVeform:DATA:WIDth 1")

        # Preamble からスケール情報を取得
        pre = self.scope.query(":WAVeform:PREamble?").split(",")
        # [2]=points, [4]=xinc, [7]=yincrement, [8]=yorigin(count), [9]=yreference(count)
        self.total_points = int(pre[2])
        self.xinc = float(pre[4])
        self.ymult = float(pre[7])
        self.yorig = float(pre[8])  # count offset for 0V position
        self.yref = float(pre[9])  # count reference (center)

        # データ保存用
        self.start_time = time.time()
        self.times = []
        self.avgs = []

        # --- pyqtgraph プロットセットアップ
        self.plot = pg.PlotWidget()
        self.plot.setLabel("left", "Voltage", units="V")
        self.plot.setLabel("bottom", "Time", units="s")
        self.curve = self.plot.plot(self.times, self.avgs)
        self.setCentralWidget(self.plot)

        # --- タイマーで定期サンプリング
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._update)
        self.timer.start()

    def _update(self):
        # 生データ取得
        raw = self.scope.query_binary_values(
            ":WAVeform:DATA?", datatype="B", container=list, header_fmt="ieee"
        )
        # カウント差分を引いて電圧に変換
        volts = [((d - self.yref) - self.yorig) * self.ymult for d in raw]

        # 時間と平均電圧を計算
        t = time.time() - self.start_time
        v_avg = sum(volts) / len(volts)

        # CSV に追記
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([t, v_avg])

        # プロットデータ更新
        self.times.append(t)
        self.avgs.append(v_avg)

        # 古いデータをウィンドウ範囲外へスクロール
        while self.times and t - self.times[0] > self.window_sec:
            self.times.pop(0)
            self.avgs.pop(0)

        # プロットを更新
        self.curve.setData(self.times, self.avgs)

    def closeEvent(self, event):
        # アプリ終了時にリソースをクリーンアップ
        self.timer.stop()
        try:
            self.scope.close()
            self.rm.close()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # 認識されたリソース文字列に置き換えてください
    RESOURCE = "USB0::0x1AB1::0x04CE::DS1ZA200401246::INSTR"
    CSV_FILE = "waveform_avg.csv"
    win = OscilloAvgPlot(RESOURCE, csv_path=CSV_FILE, interval_ms=5, window_sec=10)
    win.show()
    sys.exit(app.exec())
