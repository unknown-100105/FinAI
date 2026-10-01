import unittest

from finai.persona.policy import get_persona_policy
from finai.persona.prompts import (
    HYPE_MAN_SYSTEM_PROMPT,
    STERN_ACCOUNTANT_SYSTEM_PROMPT,
    get_persona_prompt,
)


class TestPersona(unittest.TestCase):

    def test_hype_persona(self):
        policy = get_persona_policy("hype")

        self.assertEqual(policy.display_name, "Financial Hype Man")
        self.assertIn("energetic", policy.description.lower())

        prompt = get_persona_prompt("hype")
        self.assertEqual(prompt, HYPE_MAN_SYSTEM_PROMPT)

    def test_accountant_persona(self):
        policy = get_persona_policy("accountant")

        self.assertEqual(policy.display_name, "Stern Accountant")

        prompt = get_persona_prompt("accountant")
        self.assertEqual(prompt, STERN_ACCOUNTANT_SYSTEM_PROMPT)

    def test_case_insensitive(self):
        self.assertEqual(
            get_persona_policy("HYPE").name,
            "hype",
        )

    def test_invalid_persona(self):
        with self.assertRaises(ValueError):
            get_persona_policy("anything-else")


if __name__ == "__main__":
    unittest.main()