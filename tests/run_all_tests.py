"""
Master Test Runner.
Executes all test suites and prints summary of test execution.
"""

import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from tests.test_extraction import TestExtractionAndDetection
from tests.test_classification import TestClassification
from tests.test_critical_workflows import TestCriticalWorkflows

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestExtractionAndDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestClassification))
    suite.addTests(loader.loadTestsFromTestCase(TestCriticalWorkflows))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n=======================================================")
        print("ALL CRITICAL ACCEPTANCE TESTS & WORKFLOWS PASSED! (100%)")
        print("=======================================================")
        sys.exit(0)
    else:
        print("\nTESTS FAILED!")
        sys.exit(1)
