import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

import run_text_location_eval as qa


class TextLocationTests(unittest.TestCase):
    def setUp(self):
        self.task = {"event_id": "Z1", "passage": "The troops camped across the river.", "question": "Where?"}
        self.answer = {"event_id": "Z1", "answer_location": "Across the river", "evidence_quotes": ["across the river"], "uncertainty": "No exact site."}

    def test_input_allowlist(self):
        source = {"event_id": "Z1", "text": self.task["passage"], "question": "Where?", "image": "SECRET", "place": "ANSWER", "geometry": "GOLD", "width": 500}
        with patch.object(qa, "read_package", return_value=({}, b"IMAGE", [source], "OLD PROMPT")):
            self.assertEqual(qa.text_tasks(Path("input.zip")), [self.task])

    def test_answer_and_abstention(self):
        self.assertEqual(qa.parse_answer(json.dumps(self.answer), self.task), self.answer)
        abstain = {**self.answer, "answer_location": None, "evidence_quotes": []}
        self.assertEqual(qa.parse_answer(json.dumps(abstain), self.task), abstain)

    def test_invalid_responses_not_silent_abstentions(self):
        for value in ({**self.answer, "event_id": "OTHER"}, {**self.answer, "geometry": {}},
                      {**self.answer, "answer_location": ""}, {**self.answer, "evidence_quotes": []},
                      {**self.answer, "evidence_quotes": [5]}, {**self.answer, "uncertainty": None}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                qa.parse_answer(json.dumps(value), self.task)

    def test_api_is_text_only(self):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(output_text=json.dumps(self.answer), usage=None,
            status="completed", incomplete_details=None, model="test", id="test-id")
        raw, _, meta = qa.call_api(client, "test", self.task, 4096)
        kwargs = client.responses.create.call_args.kwargs
        self.assertFalse(kwargs["store"])
        self.assertEqual(kwargs["input"], [{"role": "user", "content": [{"type": "input_text", "text": json.dumps(self.task, ensure_ascii=False)}]}])
        self.assertEqual(qa.parse_answer(raw, self.task), self.answer)
        self.assertEqual(meta["response_status"], "completed")

    def test_local_is_text_only(self):
        class Inputs(dict):
            def to(self, device):
                return self
        inputs = Inputs(input_ids=SimpleNamespace(shape=(1, 3)))
        processor = Mock(return_value=inputs)
        processor.apply_chat_template.return_value = "TEXT TEMPLATE"
        processor.decode.return_value = json.dumps(self.answer)
        model = Mock(device="cpu")
        model.generate.return_value = [[0, 1, 2, 3, 4]]
        with patch.dict("sys.modules", {"torch": MagicMock()}):
            raw, usage, _ = qa.call_local((model, processor, {}), self.task, 32)
        self.assertEqual(processor.call_args.kwargs, {"text": ["TEXT TEMPLATE"], "padding": True, "return_tensors": "pt"})
        messages = processor.apply_chat_template.call_args.args[0]
        self.assertEqual(messages[1]["content"], [{"type": "text", "text": json.dumps(self.task, ensure_ascii=False)}])
        self.assertEqual(usage["output_tokens"], 2)
        self.assertEqual(qa.parse_answer(raw, self.task), self.answer)

    def test_review_does_not_assign_correctness(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = root / "model"
            run.mkdir()
            (run / "tasks.jsonl").write_text(json.dumps(self.task) + "\n")
            (run / "prompt.txt").write_text(qa.INSTRUCTION + "\n")
            (run / "answers.json").write_text(json.dumps({"model": "test", "answers": [self.answer], "errors": []}))
            qa.write_review([run], root)
            review = json.loads((root / "human_review.jsonl").read_text())
            self.assertEqual(review["status"], "pending")
            self.assertIn(self.answer["answer_location"], (root / "REVIEW.md").read_text())
            with self.assertRaises(FileExistsError):
                qa.write_review([run], root)


if __name__ == "__main__":
    unittest.main()
