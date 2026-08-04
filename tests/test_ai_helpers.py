import unittest
from unittest.mock import patch

from ai import answer_task_question, build_task_plan_from_goal, extract_task_items, get_chat_response
from app import app as flask_app


class TestAIHelpers(unittest.TestCase):
    def test_extract_task_items_parses_bullets_and_numbering(self):
        response = "Here are some tasks:\n- Review project brief\n1. Write README\n* Set up deployment"

        self.assertEqual(
            extract_task_items(response),
            ["Review project brief", "Write README", "Set up deployment"],
        )

    def test_answer_task_question_summarizes_tasks(self):
        tasks = [
            {"title": "Write report", "status": 0, "priority": "High", "due_date": "2026-08-05"},
            {"title": "Send email", "status": 1, "priority": "Low", "due_date": None},
        ]

        response = answer_task_question("What tasks are pending?", tasks)

        self.assertIn("pending", response.lower())
        self.assertIn("Write report", response)

    def test_build_task_plan_from_goal_infers_priority_and_due_dates(self):
        plan = build_task_plan_from_goal("Prepare for my interview next week and finish the project today")

        self.assertTrue(plan)
        self.assertTrue(any(task["priority"] == "High" for task in plan))
        self.assertTrue(any(task["due_date"] for task in plan))

    def test_get_chat_response_uses_history_for_follow_up(self):
        history = [
            {"role": "user", "content": "what tasks are pending?"},
            {"role": "assistant", "content": "You still have 1 pending task on your plate."},
        ]

        response = get_chat_response("tell me more", [{"title": "Write report", "status": 0, "priority": "High"}], history)

        self.assertIn("more", response.lower())
        self.assertIn("pending", response.lower())

    def test_ask_ai_returns_json_without_database(self):
        client = flask_app.test_client()

        with patch("app.cursor", None):
            with client.session_transaction() as session:
                session.clear()

            response = client.post(
                "/ask-ai",
                data={"question": "hi"},
                headers={"X-Requested-With": "XMLHttpRequest"},
            )

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertIn("answer", payload)
            self.assertIn("TaskFlow AI", payload["answer"])

    def test_empty_ajax_question_still_returns_json(self):
        client = flask_app.test_client()

        response = client.post(
            "/ask-ai",
            data={"question": "   "},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("answer", payload)
        self.assertIn("Please ask", payload["answer"])


if __name__ == "__main__":
    unittest.main()
