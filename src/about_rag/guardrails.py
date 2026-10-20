"""Cheap pre-checks that run before any LLM call.

The system prompt is the real boundary: it sees every question and understands meaning.
These regex checks are a first, cheap layer (defense in depth). They catch the obvious
cases for free, so greetings, oversized input, blatant off-limits questions, and
copy-pasted injection attempts never spend Gemini quota. Anything subtler passes through
to the model, which declines it there.

Keyword lists are easy to dodge ("how much does he make?" passes), so the patterns are
kept narrow: a false positive blocks a real visitor, a false negative only costs a call.
"""

import re
from dataclasses import dataclass

PERSONAL_REPLY = (
    "That's a bit personal, so I'll leave that one to Saeem himself! "
    "I'm happy to tell you about his work, projects, or education though."
)
INJECTION_REPLY = (
    "I can only answer questions about Saeem, so I'll stick to that. "
    "Ask me about his work, projects, or education!"
)
GREETING_REPLY = (
    "Hi! I answer questions about Saeem Mehmood Sadiq: his work, projects, skills, "
    "education, and hobbies. What would you like to know?"
)
THANKS_REPLY = "You're welcome! Anything else you'd like to know about Saeem?"


def _words(*alternatives: str) -> re.Pattern[str]:
    """Match any alternative as whole words, case-insensitively."""
    return re.compile(r"\b(?:" + "|".join(alternatives) + r")\b", re.IGNORECASE)


OFF_LIMITS = {
    "money": _words(
        r"salar(?:y|ies)", "compensation", "net worth", "income", r"tankh?wah?", "kitna kamata"
    ),
    "relationships": _words(
        "married", "marital", "wife", "girlfriend", "boyfriend", "spouse", r"sh?aadi", "biwi"
    ),
    "family": _words("parents", "father", "mother", "siblings", "brother", "sister", "kids"),
    "private_contact": _words(
        "home address", "house address", "phone number", "mobile number", "whatsapp"
    ),
    "age": _words("how old", "age", "date of birth", "birthday", "dob"),
    "beliefs": _words("religion", "religious", "sect", r"politic\w*"),
    "health": _words("health", "illness", "disease", "medical", r"disabilit\w*"),
    "documents": _words("cnic", "passport", "visa", "national id", "id card"),
}

INJECTION = [
    re.compile(
        r"\b(?:ignore|disregard|forget)\b.{0,30}\b(?:instructions|rules|prompt)", re.IGNORECASE
    ),
    _words(r"(?:system|initial|hidden) prompt", "you are now", "developer mode", "jailbreak"),
    _words(r"pretend (?:to be|you are)"),
]

GREETING = re.compile(
    r"^(?:hi+|hello|hey|a?ss?alam(?:[\s-]*[ou]?[\s-]*a?laikum)?|aoa"
    r"|good (?:morning|afternoon|evening)"
    r"|how are you)\W*$",
    re.IGNORECASE,
)
THANKS = re.compile(r"^(?:thanks?|thank you|thx|shukriya|bye|goodbye|ok(?:ay)?)\W*$", re.IGNORECASE)


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    reason: str
    reply: str | None = None


def check(question: str, max_chars: int = 500) -> Verdict:
    """Decide whether `question` goes to the LLM, or gets a canned reply instead."""
    text = " ".join(question.split())
    if not text:
        return Verdict(False, "empty", "Please type a question about Saeem.")
    if len(text) > max_chars:
        reply = f"That's a long message! Please keep questions under {max_chars} characters."
        return Verdict(False, "too_long", reply)
    if GREETING.match(text):
        return Verdict(False, "small_talk", GREETING_REPLY)
    if THANKS.match(text):
        return Verdict(False, "small_talk", THANKS_REPLY)
    if any(pattern.search(text) for pattern in INJECTION):
        return Verdict(False, "injection", INJECTION_REPLY)
    for topic, pattern in OFF_LIMITS.items():
        if pattern.search(text):
            return Verdict(False, f"off_limits:{topic}", PERSONAL_REPLY)
    return Verdict(True, "ok")
