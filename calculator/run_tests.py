import unittest
import sys
import os

# Add the parent directory to the Python path to allow importing 'pkg'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from pkg import tests

if __name__ == '__main__':
    # Discover and run tests from the 'pkg.tests' module
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
