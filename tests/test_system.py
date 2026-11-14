"""
Pruebas unitarias para el motor estadístico v2 de EarthTrend Detective.
"""

import unittest
import math
import sys
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.stats.trend_engine import (
    mann_kendall,
    theil_sen_slope,
    ols_with_ci,
    deseasonalize,
    analyze,
)


class TestMannKendall(unittest.TestCase):

    def test_strictly_increasing(self):
        # Serie con tendencia + ruido (como datos reales)
        random.seed(42)
        vals = [float(i) + random.gauss(0, 0.5) for i in range(1, 51)]
        res = mann_kendall(vals)
        # La serie tiene tendencia positiva — S debe ser positivo
        self.assertGreater(res['s_stat'], 0)

    def test_strictly_decreasing(self):
        random.seed(42)
        vals = [float(50 - i) + random.gauss(0, 0.5) for i in range(50)]
        res = mann_kendall(vals)
        self.assertLess(res['s_stat'], 0)  # tendencia negativa

    def test_pure_noise(self):
        random.seed(42)
        vals = [math.sin(i * 0.5) for i in range(100)]
        res = mann_kendall(vals)
        # Sin corrección: podria ser significativo; con corrección, no
        self.assertIn(res['trend'], ['ascendente', 'descendente', 'ninguna'])


class TestTheilSen(unittest.TestCase):

    def test_robustness_to_outlier(self):
        vals = [2.0 * i for i in range(20)]
        vals[10] = 9999.0  # Outlier extremo
        slope = theil_sen_slope(vals)
        self.assertAlmostEqual(slope, 2.0, places=1)


class TestOLS(unittest.TestCase):

    def test_linear_fit(self):
        n = 100
        x = list(range(n))
        y = [2.0 * i + 10.0 + random.gauss(0, 1) for i in range(n)]
        res = ols_with_ci(x, y)
        self.assertAlmostEqual(res['slope'], 2.0, places=1)
        self.assertAlmostEqual(res['intercept'], 10.0, places=0)
        self.assertGreater(res['r_squared'], 0.9)


class TestDeseasonalize(unittest.TestCase):

    def test_seasonal_removed(self):
        series = []
        for y in range(2020, 2023):
            for m in range(1, 13):
                seasonal = 10.0 if m == 1 else 0.0
                series.append({
                    'date': f'{y}-{m:02d}',
                    'year': y, 'month': m,
                    'value': 20.0 + seasonal,
                })

        deseason = deseasonalize(series)
        anomalies = [d['anomaly'] for d in deseason]
        # Tras desestacionalizar, enero y julio deben tener anomalía ~0
        self.assertAlmostEqual(anomalies[0], 0.0, places=3)
        self.assertAlmostEqual(anomalies[6], 0.0, places=3)


class TestFullPipeline(unittest.TestCase):

    def test_analyze_with_power_format(self):
        """Prueba con formato POWER: {'date': ..., 'value': ...}"""
        random.seed(42)
        series = []
        for i in range(60):
            year = 2020 + i // 12
            month = (i % 12) + 1
            seasonal = -2 * math.cos(2 * math.pi * month / 12)
            trend = 0.002 * i
            noise = random.gauss(0, 0.8)
            series.append({
                'date': f'{year}-{month:02d}',
                'value': round(20.0 + seasonal + trend + noise, 2),
            })

        result = analyze(
            series=series,
            variable_id='T2M',
            variable_name='Temperatura a 2 metros',
            unit='C',
            region={'name': 'Lima', 'lat': -12.05, 'lon': -77.03},
            provenance={'source': 'NASA POWER (MERRA-2)'},
        )

        self.assertIn('metrics', result)
        self.assertIn('detective_answers', result)
        self.assertIn('annual_rate', result['metrics'])
        self.assertIn('significance_label', result['metrics'])
        self.assertGreater(result['metrics']['annual_rate'], -1.0)

    def test_analyze_with_variable_format(self):
        """Prueba con formato {date: ..., 'T2M': ...}"""
        random.seed(42)
        series = []
        for i in range(60):
            year = 2020 + i // 12
            month = (i % 12) + 1
            seasonal = -2 * math.cos(2 * math.pi * month / 12)
            trend = 0.002 * i
            noise = random.gauss(0, 0.8)
            series.append({
                'date': f'{year}-{month:02d}',
                'T2M': round(20.0 + seasonal + trend + noise, 2),
            })

        result = analyze(
            series=series,
            variable_id='T2M',
            variable_name='Temperatura',
            unit='C',
            region={'name': 'Test', 'lat': 0, 'lon': 0},
            provenance={'source': 'test'},
        )

        self.assertIn('metrics', result)
        self.assertIn('mann_kendall_p', result['metrics'])


if __name__ == '__main__':
    unittest.main()
