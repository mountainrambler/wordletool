from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class AppTests(unittest.TestCase):
    def new_app(self):
        app = AppTest.from_file(APP, default_timeout=30).run()
        self.assertFalse(app.exception)
        return app

    def test_guess_feedback_undo_and_reset(self):
        app = self.new_app()
        self.assertTrue(app.button(key="apply").disabled)
        app.text_input(key="draft").set_value("crane").run()
        self.assertTrue(app.button(key="apply").disabled)
        for i in range(5):
            app.button(key=f"feedback_{i}").click().run()
        self.assertFalse(app.button(key="apply").disabled)
        app.button(key="apply").click().run()
        self.assertEqual(app.session_state["history"], [("crane", (0,) * 5)])
        self.assertTrue(any("1 / 6" in m.value for m in app.markdown))
        self.assertFalse(any(e.label == "All 3,159 possible answers" for e in app.expander))
        self.assertFalse(app.exception)
        app.button(key="undo").click().run()
        self.assertEqual(app.session_state["draft"], "CRANE")
        self.assertEqual(app.session_state["tiles"], [0] * 5)
        self.assertFalse(app.session_state["history"])
        app.button(key="reset").click().run()
        self.assertEqual(app.session_state["draft"], "")
        self.assertEqual(app.session_state["tiles"], [-1] * 5)

    def test_suggestion_and_mode_switch(self):
        app = self.new_app()
        key = next(b.key for b in app.button if b.key and b.key.startswith("use_"))
        app.button(key=key).click().run()
        self.assertEqual(app.session_state["draft"], key.removeprefix("use_").upper())
        self.assertEqual(app.session_state["tiles"], [-1] * 5)
        app.radio(key="mode").set_value("Gather information").run()
        self.assertFalse(app.exception)

    def test_missing_answer_and_unknown_guess(self):
        app = self.new_app()
        app.text_input(key="extra_word").set_value("zzzzz").run()
        app.button(key="include_answer").click().run()
        self.assertIn("zzzzz", app.session_state["extra_solutions"])
        app.text_input(key="draft").set_value("zzzzz").run()
        self.assertNotIn("allow_unknown", [c.key for c in app.checkbox])
        app.text_input(key="draft").set_value("xxxxx").run()
        self.assertFalse(app.checkbox(key="allow_unknown").value)
        for i in range(5):
            app.button(key=f"feedback_{i}").click().run()
        self.assertTrue(app.button(key="apply").disabled)
        app.checkbox(key="allow_unknown").check().run()
        self.assertFalse(app.button(key="apply").disabled)

    def test_solved_contradictory_and_last_turn(self):
        app = self.new_app()
        app.session_state["history"] = [("apple", (2,) * 5)]
        app.run()
        self.assertTrue(app.success)
        self.assertNotIn("apply", [b.key for b in app.button])
        app.session_state["history"] = [("apple", (2,) * 5), ("ample", (2,) * 5)]
        app.run()
        self.assertTrue(any("No bundled answers" in w.value for w in app.warning))
        self.assertFalse(app.exception)
        app.session_state["history"] = [("crane", (0,) * 5)] * 5
        app.run()
        app.radio(key="mode").set_value("Gather information").run()
        self.assertTrue(any("final guess" in c.value for c in app.caption))
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
