"""Agent-X Secure Calculator Tool with AST Evaluation."""

import ast
import math
import operator
from collections.abc import Callable
from typing import Any

from agentx.tools.base import BaseTool
from agentx.tools.schemas import ToolDeclaration, ToolInvocationContext, ToolRiskLevel


class SafeMathVisitor(ast.NodeVisitor):
    """Safely evaluates arithmetic expressions using AST inspection without eval()."""

    ALLOWED_OPERATORS: dict[type[ast.AST], Callable[[Any, Any], Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    ALLOWED_UNARY_OPERATORS: dict[type[ast.AST], Callable[[Any], Any]] = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    ALLOWED_FUNCTIONS: dict[str, Callable[..., Any]] = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "pow": pow,
    }

    ALLOWED_CONSTANTS: dict[str, float] = {
        "pi": math.pi,
        "e": math.e,
    }

    def evaluate(self, expr: str) -> float | int:
        """Parse and safely evaluate math expression."""
        try:
            tree = ast.parse(expr.strip(), mode="eval")
            res = self.visit(tree.body)
            if isinstance(res, (int, float)):
                return res
            raise ValueError(f"Result is not a number: {type(res)}")
        except Exception as exc:
            raise ValueError(f"Invalid or unsafe math expression '{expr}': {str(exc)}") from exc

    def visit_Constant(self, node: ast.Constant) -> float | int:  # noqa: N802
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Name(self, node: ast.Name) -> float | int:  # noqa: N802
        if node.id in self.ALLOWED_CONSTANTS:
            return self.ALLOWED_CONSTANTS[node.id]
        raise ValueError(f"Undefined or unauthorized symbol: '{node.id}'")

    def visit_BinOp(self, node: ast.BinOp) -> float | int:  # noqa: N802
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type not in self.ALLOWED_OPERATORS:
            raise ValueError(f"Unauthorized binary operator: {op_type}")
        op_func = self.ALLOWED_OPERATORS[op_type]
        res = op_func(left, right)
        return float(res) if isinstance(res, float) else int(res)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float | int:  # noqa: N802
        operand = self.visit(node.operand)
        op_type = type(node.op)
        if op_type not in self.ALLOWED_UNARY_OPERATORS:
            raise ValueError(f"Unauthorized unary operator: {op_type}")
        op_func = self.ALLOWED_UNARY_OPERATORS[op_type]
        res = op_func(operand)
        return float(res) if isinstance(res, float) else int(res)

    def visit_Call(self, node: ast.Call) -> float | int:  # noqa: N802
        if not isinstance(node.func, ast.Name) or node.func.id not in self.ALLOWED_FUNCTIONS:
            func_name = getattr(node.func, "id", "unnamed")
            raise ValueError(f"Unauthorized function call: '{func_name}'")
        func = self.ALLOWED_FUNCTIONS[node.func.id]
        args = [self.visit(arg) for arg in node.args]
        res = func(*args)
        return float(res) if isinstance(res, float) else int(res)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Disallowed AST expression syntax: {type(node).__name__}")


class CalculatorTool(BaseTool):
    """Tool for deterministic and secure evaluation of mathematical expressions."""

    def __init__(self) -> None:
        super().__init__(
            declaration=ToolDeclaration(
                name="calculator",
                description="Performs safe mathematical calculations using an AST parser (no arbitrary execution).",
                capabilities=["analysis"],
                permissions=["compute:eval"],
                risk=ToolRiskLevel.LOW,
                estimated_cost=0.0001,
                timeout=5.0,
                input_schema={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical formula to evaluate",
                        }
                    },
                    "required": ["expression"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                        "result": {"type": "number"},
                    },
                },
            )
        )
        self._evaluator = SafeMathVisitor()

    async def _run(
        self, parameters: dict[str, Any], context: ToolInvocationContext
    ) -> dict[str, Any]:
        expr = str(parameters.get("expression", ""))
        if not expr:
            raise ValueError("Parameter 'expression' cannot be empty")

        result = self._evaluator.evaluate(expr)
        return {
            "expression": expr,
            "result": result,
        }
