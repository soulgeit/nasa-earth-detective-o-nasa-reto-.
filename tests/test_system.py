"""
Pruebas unitarias para el motor estadístico de EarthTrend Detective.
"""

import unittest
import math
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.stats.trend_engine import (
    mann_kendall_test,
    theil_sen_slope,
    calculate_linear_trend,
    deseasonalize_monthly,
    analyze_earth_science_trend
)


class TestTrendEngine(unittest.TestCase):

    def test_mann_kendall_strictly_increasing(self):
        # Serie monótona creciente
        vals = [float(i) for i in range(1, 51)]
        res = mann_kendall_test(vals)
        self.assertTrue(res['is_significant'])
        self.assertEqual(res['trend'], 'ascendente')
        self.assertLess(res['p_value'], 0.001)

    def test_mann_kendall_strictly_decreasing(self):
        # Serie monótona decreciente
        vals = [float(50 - i) for i in range(50)]
        res = mann_kendall_test(vals)
        self.assertTrue(res['is_significant'])
        self.assertEqual(res['trend'], 'descendente')
        self.assertLess(res['p_value'], 0.001)

    def test_mann_kendall_pure_noise(self):
        # Serie oscilatoria simétrica sin tendencia
        vals = [math.sin(i * 0.5) for i in range(100)]
        res = mann_kendall_test(vals)
        self.assertFalse(res['is_significant'])

    def test_theil_sen_slope_robustness(self):
        # Pendiente = 2.0 con un outlier extremo
        vals = [2.0 * i for i in range(20)]
        vals[10] = 9999.0  # Ruido extremo
        slope = theil_sen_slope(vals)
        self.assertAlmostEqual(slope, 2.0, places=1)

    def test_deseasonalize_monthly(self):
        series = []
        for y in range(2020, 2023):
            for m in range(1, 13):
                # Enero siempre tiene +10 respecto a Julio
                seasonal = 10.0 if m == 1 else 0.0
                series.append({'date': f'{y}-{m:02d}-01', 'year': y, 'month': m, 'value': 20.0 + seasonal})

        deseason = deseasonalize_monthly(series)
        anomalies = [d['anomaly'] for d in deseason]
        # Tras desestacionalizar, la anomalía en enero y julio debe ser 0.0
        self.assertAlmostEqual(anomalies[0], 0.0, places=3)
        self.assertAlmostEqual(anomalies[6], 0.0, places=3)


if __name__ == '__main__':
    unittest.main()
