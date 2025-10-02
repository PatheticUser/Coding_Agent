from pkg.calculator import Calculator
from pkg.render import format_json_output

calc = Calculator()
expression = "sin(90) + 7 * 2"
result = calc.evaluate(expression) # Test with a scientific function

rendered_output = format_json_output(expression, result)
print(rendered_output)