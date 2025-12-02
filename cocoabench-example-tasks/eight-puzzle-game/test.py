"""
Test function for eight-puzzle-game.

Evaluates the code from the 8-puzzle game.
"""

import json
import re

# Ground truth value
EXPECTED_ANSWER = "EFPTGK"


def _extract_answer_from_text(text: str) -> str | None:
    """Extract answer from <answer>...</answer> tags."""
    # Try to find answer in <answer> tags
    answer_pattern = re.compile(r'<answer>(.*?)</answer>', re.IGNORECASE | re.DOTALL)
    match = answer_pattern.search(text)
    if match:
        return match.group(1).strip()
    return None


def _extract_answer_from_conversation(conversation: list) -> str | None:
    """Extract answer from conversation history."""
    # First, check assistant messages with tool_calls for task_complete with result parameter
    for message in reversed(conversation or []):
        if not isinstance(message, dict):
            continue
        if message.get("role") == "assistant" and message.get("tool_calls"):
            # Check if any tool call is task_complete with result
            for tc in message.get("tool_calls", []):
                if not isinstance(tc, dict):
                    continue
                func = tc.get("function", {})
                if func.get("name") == "task_complete":
                    # Extract result from tool call arguments
                    try:
                        args_str = func.get("arguments", "{}")
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                        if "result" in args:
                            result_str = args["result"]
                            # Try to extract answer from result
                            answer = _extract_answer_from_text(result_str)
                            if answer:
                                return answer
                    except (json.JSONDecodeError, Exception):
                        pass
    
    # Search through assistant messages in reverse order for answer in content
    for message in reversed(conversation or []):
        if not isinstance(message, dict):
            continue
        if message.get("role") != "assistant":
            continue
        content = message.get("content") or ""
        answer = _extract_answer_from_text(content)
        if answer:
            return answer
    return None


def _normalize_answer(answer: str) -> str:
    """Normalize answer for comparison (strip whitespace, uppercase)."""
    return answer.strip().upper()


def test(result: dict) -> dict:
    """
    Test executor result.

    Args:
        result: Result dict from TaskExecutor.run_task()

    Returns:
        Test dict with metrics and pass/fail status
    """
    conversation = result.get("conversation") or []
    task_completed = result.get("status") == "success"

    # First, check if task_result is directly provided in result dict
    task_result = result.get("task_result")
    output_answer = None
    if task_result:
        # Try to extract answer from task_result
        output_answer = _extract_answer_from_text(task_result)
    
    # If not found in task_result, extract from conversation
    if not output_answer:
        output_answer = _extract_answer_from_conversation(conversation)
    
    if not output_answer:
        return {
            "passed": False,
            "feedback": "No valid answer found in assistant responses. Expected format: <answer>CODE</answer>",
            "details": {
                "task_completed": task_completed,
                "conversation_length": len(conversation),
            },
        }

    # Normalize answers for comparison (case-insensitive)
    normalized_output = _normalize_answer(output_answer)
    normalized_expected = _normalize_answer(EXPECTED_ANSWER)

    # Check if answer matches
    answer_correct = normalized_output == normalized_expected

    passed = task_completed and answer_correct

    feedback_parts = []
    feedback_parts.append(f"Found answer: {output_answer}")
    feedback_parts.append(
        f"{'✓' if answer_correct else '✗'} Code: got '{output_answer}', expected '{EXPECTED_ANSWER}'."
    )
    if not task_completed:
        feedback_parts.append("✗ Task status is not success.")

    return {
        "passed": passed,
        "feedback": "\n".join(feedback_parts),
        "details": {
            "task_completed": task_completed,
            "output_answer": output_answer,
            "answer_correct": answer_correct,
            "expected_answer": EXPECTED_ANSWER,
        },
    }

