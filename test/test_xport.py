'''
Tests for ``xport.py``.
'''

import csv
import glob
import math
import os
import unittest
import xport



class TestCSVs(unittest.TestCase):

    def convert_types(self, row):
        typed = []
        for s in row:
            try:
                value = int(s)
            except ValueError:
                try:
                    value = float(s)
                except ValueError:
                    try:
                        value = s.decode('utf-8')
                    except UnicodeDecodeError:
                        value = s
                    except AttributeError: # Python 3, no need to convert
                        value = s
            typed.append(value)
        return tuple(typed)


    def test_csvs(self):
        for csvfile in glob.glob('test/data/*.csv'):
            directory, filename = os.path.split(csvfile)
            xptfile = os.path.join(directory, filename[:-4] + '.xpt')

            with open(csvfile) as fcsv, open(xptfile, 'rb') as fxpt:
                csvreader = csv.reader(fcsv)
                xptreader = xport.reader(fxpt)

                self.assertEqual(tuple(next(csvreader)), xptreader.fields)

                values = (self.convert_types(row) for row in csvreader)
                list(map(self.assertEqual, values, xptreader))



class TestStringsDataset(unittest.TestCase):


    def test_header(self):
        with open('test/data/strings.xpt', 'rb') as f:
            reader = xport.reader(f)
            x, = reader._variables

            assert reader.fields == ('X',)

            assert x.name == 'X'
            assert x.numeric == False
            assert x.position == 0
            assert x.size == 100


    def test_length(self):
        with open('test/data/strings.xpt', 'rb') as f:
            assert len(list(xport.reader(f))) == 2


    def test_values(self):
        with open('test/data/strings.xpt', 'rb') as f:
            it = (row.X for row in xport.reader(f))
            assert next(it) == ''.join(chr(i) for i in range(1, 101))
            assert next(it) == ''.join(chr(i) for i in range(101,128))




class TestKnownValuesDataset(unittest.TestCase):


    def test_header(self):
        with open('test/data/known_values.xpt', 'rb') as f:
            reader = xport.reader(f)
            x, = reader._variables

            assert reader.fields == ('X',)

            assert x.name == 'X'
            assert x.numeric == True
            assert x.position == 0
            assert x.size == 8


    def test_length(self):
        with open('test/data/known_values.xpt', 'rb') as f:
            assert len(list(xport.reader(f))) == 2123


    def test_values(self):
        with open('test/data/known_values.xpt', 'rb') as f:
            it = (row.X for row in xport.reader(f))
            for value in [float(e) for e in range(-1000, 1001)]:
                assert value == next(it)
            for value in [math.pi ** e for e in range(-30, 31)]:
                self.assertAlmostEqual(value, next(it), places=30)
            for value in [-math.pi ** e for e in range(-30, 31)]:
                self.assertAlmostEqual(value, next(it), places=30)



class TestMultipleColumnsDataset(unittest.TestCase):


    def test_header(self):
        with open('test/data/multi.xpt', 'rb') as f:
            reader = xport.reader(f)
            x, y = reader._variables

            assert reader.fields == ('X', 'Y')

            assert x.name == 'X'
            assert x.numeric == False
            assert x.position == 0
            assert x.size == 10

            assert y.name == 'Y'
            assert y.numeric == True
            assert y.position == 10
            assert y.size == 8


    def test_length(self):
        with open('test/data/multi.xpt', 'rb') as f:
            assert len(list(xport.reader(f))) == 20


    def test_values(self):
        strings = '''
            This is one time where television really fails to capture
            the true excitement of a large squirrel predicting the weather.
            '''.split()
        with open('test/data/multi.xpt', 'rb') as f:
            for (i, s), (x, y) in zip(enumerate(strings, 1), xport.reader(f)):
                assert (x, y) == (s, i)


class TestIEEEtoIBM(unittest.TestCase):

    def roundtrip(self, n):
        ibm = xport.ieee_to_ibm(n)
        ieee = xport.ibm_to_ieee(ibm)
        return round(ieee, 9)

    def test_overflow(self):
        with self.assertRaises(xport.Overflow):
            xport.ieee_to_ibm(16 ** 63)

    def test_underflow(self):
        with self.assertRaises(xport.Underflow):
            xport.ieee_to_ibm(16 ** -66)

    def test_nan(self):
        n = float('nan')
        self.assertTrue(math.isnan(self.roundtrip(n)))

    def test_zero(self):
        self.assertEqual(0, self.roundtrip(0))

    def test_small_magnitude_integers(self):
        for i in range(-1000, 1000):
            self.assertEqual(i, self.roundtrip(i))

    def test_small_magnitude_floats(self):
        for i in range(-10, 10):
            i /= 1000
            self.assertEqual(i, self.roundtrip(i))

    def test_large_magnitude_floats(self):
        n = int(1e9)
        for i in range(n, n + 100):
            self.assertEqual(i, self.roundtrip(i))

    def test_large_magnitude_floats_with_fraction(self):
        offset = 1e9
        for i in range(100):
            i /= 1e9
            x = i + offset
            self.assertEqual(x, self.roundtrip(x))

    def test_very_small_magnitude_floats(self):
        for i in range(-10, 10):
            i /= 1e6
            self.assertEqual(i, self.roundtrip(i))


if __name__ == '__main__':
    unittest.main()


