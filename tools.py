from typing import Any, Literal

ABSOLUTE_ZERO_C = -273.15


def get_usage_guide() -> str:
    """
    Explains what this server does, which tool to call for what, and how errors are reported.
    Call this first.
    """
    return """\
This server does simple arithmetic and temperature conversion.

Tools:
- add_two_numbers(a, b): add two integers.
- divide_two_numbers(a, b): divide a by b. Returns {"error": ...} if b is 0.
- convert_temperature(value, from_unit, to_unit): convert between "celsius" and "fahrenheit".

Workflow:
- To halve a sum, call add_two_numbers, then divide_two_numbers with the sum it returns as a and 2 as b.
- To convert a temperature, call convert_temperature once. Write the unit names exactly as shown above.

Errors:
- A call that runs and fails (b is 0, or a temperature below absolute zero) returns {"error": "<what went wrong>"}.
- A unit other than "celsius" or "fahrenheit" is rejected before convert_temperature runs, and the message lists the valid values.
- Either way, read the message, fix the input, and try again. Do not repeat the same call.
"""


def divide_two_numbers(a: int, b: int) -> dict[str, Any]:
    """
    Divide a by b. Returns {"error": ...} instead of a result if b is 0.

    args:
        a: The dividend
        b: The divisor. Must not be 0.

    returns:
        {"result": <float>} on success, {"error": <message>} if b is 0
    """
    if b == 0:
        return {"error": "b must not be 0."}
    return {"result": a / b}


def convert_temperature(
    value: float,
    from_unit: Literal["celsius", "fahrenheit"],
    to_unit: Literal["celsius", "fahrenheit"],
) -> dict[str, Any]:
    """
    Convert a temperature between "celsius" and "fahrenheit". Write the unit names exactly like that, in lowercase: any other value is rejected. A value below absolute zero returns {"error": ...}.

    args:
        value: The temperature to convert, in from_unit. Must not be below absolute zero.
        from_unit: The unit of value: "celsius" or "fahrenheit"
        to_unit: The unit to convert to: "celsius" or "fahrenheit"

    returns:
        {"value": <float, rounded to 2 decimals>, "unit": <to_unit>} on success, {"error": <message>} if value is below absolute zero
    """
    celsius = value if from_unit == "celsius" else (value - 32) * 5 / 9
    if celsius < ABSOLUTE_ZERO_C:
        return {"error": f"{value} {from_unit} is below absolute zero."}
    result = celsius if to_unit == "celsius" else celsius * 9 / 5 + 32
    return {"value": round(result, 2), "unit": to_unit}
