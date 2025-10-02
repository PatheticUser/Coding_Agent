import unittest
import sys
import os

# Add the parent directory of pkg to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pkg.calculator import Calculator
from pkg.render import format_json_output


class TestCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = Calculator()

    def test_addition(self):
        self.assertEqual(self.calculator.evaluate("1 + 1"), 2.0)

    def test_subtraction(self):
        self.assertEqual(self.calculator.evaluate("5 - 3"), 2.0)

    def test_multiplication(self):
        self.assertEqual(self.calculator.evaluate("2 * 3"), 6.0)

    def test_division(self):
        self.assertEqual(self.calculator.evaluate("6 / 3"), 2.0)

    def test_order_of_operations(self):
        self.assertEqual(self.calculator.evaluate("1 + 2 * 3"), 7.0)
        self.assertEqual(self.calculator.evaluate("(1 + 2) * 3"), 9.0)

    def test_floating_point(self):
        self.assertEqual(self.calculator.evaluate("1.5 + 2.5"), 4.0)

    def test_negative_numbers(self):
        self.assertEqual(self.calculator.evaluate("5 - 10"), -5.0)

    def test_zero_division(self):
        with self.assertRaises(ValueError):
            self.calculator.evaluate("1 / 0")

    def test_empty_expression(self):
        self.assertIsNone(self.calculator.evaluate(""))
        self.assertIsNone(self.calculator.evaluate("   "))

    def test_complex_expression(self):
        self.assertEqual(self.calculator.evaluate("10 - 2 * 3 + (8 / 4)"), 6.0)

    def test_single_number(self):
        self.assertEqual(self.calculator.evaluate("123"), 123.0)

    def test_invalid_token(self):
        with self.assertRaises(ValueError):
            self.calculator.evaluate("1 + a")

    def test_mismatched_parentheses(self):
        with self.assertRaises(ValueError):
            self.calculator.evaluate("(1 + 2") # Reverted to original test case
        with self.assertRaises(ValueError):
            self.calculator.evaluate("1 + 2)")

    def test_trigonometric_functions(self):
        # Test sin(90) which is 1
        self.assertAlmostEqual(self.calculator.evaluate("sin(90)"), 1.0, places=7)
        # Test cos(0) which is 1
        self.assertAlmostEqual(self.calculator.evaluate("cos(0)"), 1.0, places=7)
        # Test tan(45) which is 1
        self.assertAlmostEqual(self.calculator.evaluate("tan(45)"), 1.0, places=7)
        # Test combined expression
        self.assertAlmostEqual(self.calculator.evaluate("sin(30) + cos(60)"), 1.0, places=7)

class TestRender(unittest.TestCase):

    def test_json_output(self):
        expression = "1 + 1"
        result = 2.0
        expected_output = '{\n  "expression": "1 + 1",\n  "result": 2\n}'
        self.assertEqual(format_json_output(expression, result), expected_output)

        expression = "5 / 2"
        result = 2.5
        expected_output = '{\n  "expression": "5 / 2",\n  "result": 2.5\n}'
        self.assertEqual(format_json_output(expression, result), expected_output)

    def test_json_output_with_int_result(self):
        expression = "2 * 3"
        result = 6.0
        expected_output = '{\n  "expression": "2 * 3",\n  "result": 6\n}'
        self.assertEqual(format_json_output(expression, result), expected_output)


if __name__ == '__main__':
    unittest.main()
