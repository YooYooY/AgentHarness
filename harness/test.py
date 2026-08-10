import json
from history import tool_result_budget, snip_compact, micro_compact
from test_messages import TEXT_MESSAGES

THRESHOLE = 20

# snip_compact(TEXT_MESSAGES, max_messages=5)
print(json.dumps(micro_compact(TEXT_MESSAGES), ensure_ascii=False))


# print(json.dumps(tool_result_budget(TEXT_MESSAGES, 10), ensure_ascii=False))
