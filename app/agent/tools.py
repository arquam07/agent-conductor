"""Tools the agent can call. Kept small and real — extend as needed.
Each tool is a plain function with a docstring; LangChain binds them by schema."""
import ast
import logging

from langchain_core.tools import tool

logger = logging.getLogger("agent")


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. '2 * (3 + 4)'.
    Supports + - * / ** and parentheses only."""
    try:
        node = ast.parse(expression, mode="eval")
        result = _safe_eval(node.body)
        return str(result)
    except Exception as e:
        return f"error: {e}"


@tool
def word_count(text: str) -> str:
    """Count the words in a piece of text."""
    return str(len(text.split()))


# --- safe arithmetic eval (no builtins, no names) ---

_ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
            ast.USub, ast.UAdd)


def _safe_eval(node):
    if not isinstance(node, _ALLOWED):
        raise ValueError(f"disallowed expression: {type(node).__name__}")
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError("only numbers allowed")
        return node.value
    if isinstance(node, ast.UnaryOp):
        v = _safe_eval(node.operand)
        return +v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp):
        l, r = _safe_eval(node.left), _safe_eval(node.right)
        op = node.op
        if isinstance(op, ast.Add): return l + r
        if isinstance(op, ast.Sub): return l - r
        if isinstance(op, ast.Mult): return l * r
        if isinstance(op, ast.Div): return l / r
        if isinstance(op, ast.Pow): return l ** r
    raise ValueError("unsupported")


TOOLS = [calculator, word_count]