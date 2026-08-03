import inspect
from tools.handlers import TOOL_HANDLERS


def exectue_tool(name: str, args: dict) -> str:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return f"Unknown tool {name}"

    # sig = inspect.signature(handler)
    # valid = {
    #   k: v
    #   for k, v in args.items()
    #   if k in sig.parameters
    # }
    # return handler(**valid)

    try:
        sig = inspect.signature(handler)
        bound = sig.bind(**args)
    except TypeError as e:
        return f"Invalid arguments: {e}"

    return handler(**bound.arguments)
