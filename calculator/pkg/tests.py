import unittest
from pkg.calculator import Calculator

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = Calculator()

    def test_multiplication(self):
        self.assertEqual(self.calculator.evaluate("2*3"), 6)
        self.assertEqual(self.calculator.evaluate("2 * 3"), 6)
        self.assertEqual(self.calculator.evaluate("2*3*4"), 24)
        self.assertEqual(self.calculator.evaluate("10/2*5"), 25) # Test mixed multiplication and division
        self.assertEqual(self.calculator.evaluate("5*2+3"), 13) # Test precedence with addition
        self.assertEqual(self.calculator.evaluate("3+5*2"), 13) # Test precedence with addition

    def test_division(self):
        self.assertEqual(self.calculator.evaluate("6/2"), 3)
        self.assertEqual(self.calculator.evaluate("7/2"), 3.5)
        with self.assertRaises(ValueError):
            self.calculator.evaluate("1/0")

    def test_addition_subtraction(self):
        self.assertEqual(self.calculator.evaluate("1+2"), 3)
        self.assertEqual(self.calculator.evaluate("5-3"), 2)
        self.assertEqual(self.calculator.evaluate("10-5+2"), 7)

    def test_parentheses(self):
        self.assertEqual(self.calculator.evaluate("(2+3)*4"), 20)
        self.assertEqual(self.calculator.evaluate("2*(3+4)"), 14)
        self.assertEqual(self.calculator.evaluate("(10-5)/(1+1)"), 2.5)

    def test_power(self):
        self.assertEqual(self.calculator.evaluate("2^3"), 8)
        self.assertEqual(self.calculator.evaluate("3^2"), 9)
        self.assertEqual(self.calculator.evaluate("2^3^2"), 512) # Right-associativity for power

    def test_functions(self):
        self.assertAlmostEqual(self.calculator.evaluate("sin(0)"), 0)
        self.assertAlmostEqual(self.calculator.evaluate("cos(0)"), 1)
        self.assertAlmostEqual(self.calculator.evaluate("sqrt(9)"), 3)
        self.assertAlmostEqual(self.calculator.evaluate("log(1)"), 0)
        self.assertAlmostEqual(self.calculator.evaluate("tan(0)"), 0)

    def test_complex_expressions(self):
        self.assertAlmostEqual(self.calculator.evaluate("sin(90-60)*2"), 1.0) # This should actually be sin(30) * 2 which is 0.5 * 2 = 1
        self.assertAlmostEqual(self.calculator.evaluate("sqrt(4)+2*3"), 8)

if __name__ == '__main__':
    unittest.main()
