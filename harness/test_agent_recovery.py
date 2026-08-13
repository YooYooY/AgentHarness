"""
Tests for the `finish_reason == "length"` error-handling block in agent.agent_loop.

Covers the four branches:
  1. first `length`  -> escalate max_tokens (DEFAULT_MAX_TOKENS -> ESCALATE_MAX_TOKENS), continue
  2. escalated + tool_calls -> append assistant msg + failed-tool-result placeholders, continue
  3. escalated, no tool_calls, recovery_count < MAX -> append continuation prompt, continue
  4. escalated, no tool_calls, recovery_count >= MAX -> return (silent exit)

Plus regression tests that the normal `stop` flows (with/without tool calls)
still work.

Run with:
    cd /Users/weilongchen/Documents/AgentHarness/harness
    python3 test_agent_recovery.py
"""

import unittest
from unittest.mock import MagicMock, patch

import agent
from config import (
    CONTINUATION_PROMPT,
    DEFAULT_MAX_TOKENS,
    ESCALATE_MAX_TOKENS,
    MAX_RECOVERY_RETRIES,
)

TOOL_FAILED_CONTENT = "[output truncated; tool execution failed.]"


# ---------------------------------------------------------------- fakes ----

class FakeFunction:
    def __init__(self, name="bash", arguments="{}"):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, id_, function=None):
        self.id = id_
        self.function = function if function is not None else FakeFunction()


class FakeMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class FakeChoice:
    def __init__(self, finish_reason, message):
        self.finish_reason = finish_reason
        self.message = message


class FakeResponse:
    def __init__(self, finish_reason, content="", tool_calls=None):
        self.choices = [FakeChoice(finish_reason, FakeMessage(content, tool_calls))]


def length_response(content="truncated", tool_calls=None):
    return FakeResponse("length", content, tool_calls)


def stop_response(content="ok", tool_calls=None):
    return FakeResponse("stop", content, tool_calls)


# ------------------------------------------------------------ harness ------

def run_loop(responses):
    """Drive agent.agent_loop with a scripted list of FakeResponse objects.

    Returns (messages, state, captured, log_mock) where:
      messages  - the messages list after agent_loop terminates
      state     - the RecoveryState instance used inside the loop
      captured  - dict with 'max_tokens_each_call' (max_tokens observed at each
                  with_retry call) and 'exhausted' (whether responses ran out)
      log_mock  - the mocked agent.log (captures log.info(...) etc.)
    """
    captured = {"max_tokens_each_call": [], "exhausted": False}
    state_holder = {}
    log_mock = MagicMock()

    def fake_with_retry(fn, state):
        state_holder["state"] = state
        captured["max_tokens_each_call"].append(state.max_tokens)
        if not responses:
            captured["exhausted"] = True
            raise StopIteration  # sentinel: terminate the while-True loop
        return responses.pop(0)

    def fake_assistant_dict(msg):
        return {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [{"id": tc.id} for tc in (msg.tool_calls or [])],
        }

    messages = [{"role": "user", "content": "hello"}]
    with patch.object(agent, "get_system_prompt", return_value=""), \
         patch.object(agent, "load_memories", return_value=None), \
         patch.object(agent, "todo_update_reminder", return_value=None), \
         patch.object(agent, "tool_result_budget", side_effect=lambda m: m), \
         patch.object(agent, "snip_compact", side_effect=lambda m: m), \
         patch.object(agent, "micro_compact", side_effect=lambda m: m), \
         patch.object(agent, "estimate_size", return_value=0), \
         patch.object(agent, "compact_history", side_effect=lambda m: m), \
         patch.object(agent, "reactive_compact", side_effect=lambda m: m), \
         patch.object(agent, "repair_message_chain", side_effect=lambda m: m), \
         patch.object(agent, "assistant_message_dict", side_effect=fake_assistant_dict), \
         patch.object(agent, "with_retry", side_effect=fake_with_retry), \
         patch.object(agent, "exectue_tool", return_value="tool-output"), \
         patch.object(agent, "extract_memories", return_value=None), \
         patch.object(agent, "consolidate_memories", return_value=None), \
         patch.object(agent, "trigger_hooks", return_value=None), \
         patch.object(agent, "log", log_mock):
        try:
            agent.agent_loop(messages)
        except StopIteration:
            pass
    return messages, state_holder["state"], captured, log_mock


# -------------------------------------------------------------- tests ------

class TestLengthRecovery(unittest.TestCase):

    def _run(self, responses):
        return run_loop(responses)

    # ---- branch 1: escalation ----
    def test_first_length_escalates_max_tokens(self):
        messages, state, captured, log = self._run(
            [length_response("t1"), stop_response("done")]
        )
        self.assertTrue(state.has_escalated)
        self.assertEqual(state.max_tokens, ESCALATE_MAX_TOKENS)
        # first call used default, second call already escalated
        self.assertEqual(
            captured["max_tokens_each_call"],
            [DEFAULT_MAX_TOKENS, ESCALATE_MAX_TOKENS],
        )
        # the truncated response must NOT be appended (escalation path continues)
        contents = [m["content"] for m in messages if m.get("role") == "assistant"]
        self.assertNotIn("t1", contents)
        # loop continued and finished normally on the next response
        self.assertIn("done", contents)
        log.info.assert_any_call(
            f"[max_token] {DEFAULT_MAX_TOKENS} escalate to {ESCALATE_MAX_TOKENS}"
        )
        # recovery counters untouched by escalation branch
        self.assertEqual(state.recovery_count, 0)

    # ---- branch 2: escalated + tool_calls -> failed tool results ----
    def test_escalated_length_with_tool_calls_appends_failed_tool_results(self):
        tc1, tc2 = FakeToolCall("call_1"), FakeToolCall("call_2")
        messages, state, captured, log = self._run(
            [
                length_response("t0"),  # triggers escalation
                length_response("t1", tool_calls=[tc1, tc2]),
                stop_response("done"),
            ]
        )
        self.assertTrue(state.has_escalated)
        self.assertEqual(state.recovery_count, 0)  # tool path does not consume recovery
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        self.assertEqual(len(tool_msgs), 2)
        self.assertEqual(tool_msgs[0]["tool_call_id"], "call_1")
        self.assertEqual(tool_msgs[1]["tool_call_id"], "call_2")
        self.assertTrue(
            all(m["content"] == TOOL_FAILED_CONTENT for m in tool_msgs)
        )
        # truncated assistant message appended; escalated first one not
        contents = [m["content"] for m in messages if m.get("role") == "assistant"]
        self.assertIn("t1", contents)
        self.assertNotIn("t0", contents)
        self.assertIn("done", contents)  # loop continued afterwards

    # ---- branch 3: escalated, no tools -> continuation prompt ----
    def test_escalated_length_no_tools_appends_continuation(self):
        messages, state, captured, log = self._run(
            [
                length_response("t0"),  # escalate
                length_response("t1"),  # recovery #1
                stop_response("done"),
            ]
        )
        self.assertTrue(state.has_escalated)
        self.assertEqual(state.recovery_count, 1)
        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        self.assertEqual(user_contents.count(CONTINUATION_PROMPT), 1)
        # order: assistant(t1) -> user(continuation) -> assistant(done)
        roles = [m["role"] for m in messages]
        self.assertEqual(
            roles[-3:], ["assistant", "user", "assistant"]
        )
        log.info.assert_any_call(f"Pick up 1/{MAX_RECOVERY_RETRIES}")

    # ---- branch 4: retry limit reached -> return ----
    def test_recovery_retries_limit_reached_returns(self):
        responses = [
            length_response("t0"),  # escalate
            length_response("t1"),  # recovery 1
            length_response("t2"),  # recovery 2
            length_response("t3"),  # recovery 3
            length_response("t4"),  # limit reached -> should return
            length_response("t5"),  # must never be consumed
        ]
        messages, state, captured, log = self._run(responses)
        self.assertTrue(state.has_escalated)
        self.assertEqual(state.recovery_count, MAX_RECOVERY_RETRIES)
        # exactly 5 LLM polls; t5 never consumed
        self.assertEqual(len(captured["max_tokens_each_call"]), 5)
        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        self.assertEqual(user_contents.count(CONTINUATION_PROMPT), MAX_RECOVERY_RETRIES)
        # last assistant message appended, but NO 4th continuation after it
        contents = [m["content"] for m in messages if m.get("role") == "assistant"]
        self.assertIn("t4", contents)
        self.assertNotIn("t5", contents)
        self.assertEqual(messages[-1]["content"], "t4")
        log.info.assert_any_call("reach Recovery retries limit")
        for i in range(1, MAX_RECOVERY_RETRIES + 1):
            log.info.assert_any_call(f"Pick up {i}/{MAX_RECOVERY_RETRIES}")

    # ---- combined realistic scenario ----
    def test_full_scenario_escalate_toolfail_continuation_stop(self):
        tc = FakeToolCall("call_x")
        messages, state, captured, log = self._run(
            [
                length_response("t0"),                              # escalate
                length_response("t1", tool_calls=[tc]),             # tool fail
                length_response("t2"),                              # recovery 1
                stop_response("final"),                             # normal stop
            ]
        )
        self.assertTrue(state.has_escalated)
        self.assertEqual(state.recovery_count, 1)
        self.assertEqual(captured["max_tokens_each_call"],
                         [DEFAULT_MAX_TOKENS, ESCALATE_MAX_TOKENS,
                          ESCALATE_MAX_TOKENS, ESCALATE_MAX_TOKENS])
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        self.assertEqual([m["tool_call_id"] for m in tool_msgs], ["call_x"])
        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        self.assertEqual(user_contents.count(CONTINUATION_PROMPT), 1)
        contents = [m["content"] for m in messages if m.get("role") == "assistant"]
        self.assertIn("t1", contents)
        self.assertIn("t2", contents)
        self.assertEqual(contents[-1], "final")

    # ---- regression: normal stop without tool calls ----
    def test_normal_stop_flow_unaffected(self):
        messages, state, captured, log = self._run([stop_response("hello")])
        self.assertFalse(state.has_escalated)
        self.assertEqual(state.recovery_count, 0)
        self.assertEqual(state.max_tokens, DEFAULT_MAX_TOKENS)
        self.assertEqual(len(captured["max_tokens_each_call"]), 1)
        contents = [m["content"] for m in messages if m.get("role") == "assistant"]
        self.assertEqual(contents, ["hello"])
        self.assertFalse(captured["exhausted"])  # returned, didn't run out of reps

    # ---- regression: normal stop WITH tool calls (tool execution still works) ----
    def test_normal_tool_execution_flow_unaffected(self):
        tc = FakeToolCall("call_y", function=FakeFunction(name="bash", arguments="{}"))
        messages, state, captured, log = self._run([stop_response("run", tool_calls=[tc])])
        self.assertFalse(state.has_escalated)
        self.assertEqual(state.recovery_count, 0)
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        self.assertEqual(len(tool_msgs), 1)
        self.assertEqual(tool_msgs[0]["tool_call_id"], "call_y")
        self.assertEqual(tool_msgs[0]["content"], "tool-output")
        self.assertTrue(captured["exhausted"])  # loop continued, then ran out


if __name__ == "__main__":
    unittest.main(verbosity=2)
