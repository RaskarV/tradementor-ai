"""All static bot strings. Every one of them is run through the compliance gate before delivery
(and tests/test_texts.py asserts that none would be blocked)."""

INTRO = (
    "Welcome to TradeMentor AI!\n\n"
    "I'm an educational assistant. I can teach trading concepts, explain risk management, and run a "
    "position size calculator.\n\n"
    "I can't give buy or sell tips, predict prices, guarantee returns, share live market prices, or place "
    "trades for you. Nothing I say is financial advice.")
Q_TRADED = "To start, have you traded before, or would this be a fresh start?"
Q_TRADED_RETRY = "Sorry, I didn't catch that. Have you traded before? You can tap a button or just type it."
Q_EXPERIENCE = "Thanks! How would you describe your experience level?"
Q_EXPERIENCE_RETRY = "I couldn't tell which level fits best. Please tap one of the options."
Q_CAPITAL = ("Optional: roughly how much would you use for learning examples? This only makes the examples "
             "more relatable, and you can skip it. Type an amount like 50000 or tap Skip.")
Q_GOALS = "What would you most like to get out of this? Tap an option or describe it in your own words."
Q_LANGUAGE = "Which language do you prefer for explanations?"
ONBOARD_DONE = ("You're all set! Ask me anything about trading concepts, try /risk for the position size "
                "calculator, or /learn to browse topics. Type /help to see everything I can do.")
WELCOME_BACK = "Welcome back! What would you like to learn today? Type /help to see all commands."
ONBOARD_FIRST = "Let's finish a quick setup first so I can tailor my explanations to you."

HELP = ("Here's what I can do:\n\n"
        "/start - begin or restart setup\n/learn - browse trading education topics\n"
        "/risk - position size and risk calculator\n/profile - see your learning profile\n"
        "/human - ask a human educator for help\n/reset - clear this conversation's context\n"
        "/delete_my_data - delete the data I store about you\n/help - show this list\n\n"
        "You can also just ask me questions in your own words.")

RISK_INTRO = ("Let's work out a position size. This is a learning tool, not a recommendation to trade. "
              "Send /cancel at any time.")
RISK_Q_CAPITAL = "What is the account capital to use for this example? (e.g. 50000)"
RISK_Q_PCT = "What percentage of that capital are you willing to risk on this one trade? (e.g. 1 or 2)"
RISK_Q_ENTRY = "What is the entry price?"
RISK_Q_STOP = "What is the stop-loss price?"
RISK_Q_TARGET = "Optional: what is the target price? Send a number, or tap Skip."
RISK_CANCELLED = "Calculator cancelled. Send /risk whenever you want to try again."
RISK_FAILED = "That calculation didn't work. Send /risk to start again."
RISK_QUICK_HELP = "Quick format: /risk capital risk% entry stop [target]. Example: /risk 50000 2 500 490 530"

HUMAN_OFFER = ("Absolutely. I can arrange for a member of the team to assist you.\n\n"
               "Would you like to submit a support request?")
HUMAN_DECLINED = "No problem. I'm happy to keep going here. What would you like to explore?"
HUMAN_EXISTS = ("You already have an open support request ({code}). It's still active, and an educator "
                "will reply here when someone picks it up.")
HUMAN_CREATED = ("Your support request {code} has been recorded as pending. I can't promise when someone "
                 "will respond, but an educator will reply here once it is picked up.")
EDUCATOR_PREFIX = "Message from your educator (request {code}):\n\n"
TICKET_CLOSED = "Your support request {code} has been closed. Send /human if you need more help."

RESET_DONE = "Done. I've cleared this conversation's context. Your profile is unchanged."
DELETE_CONFIRM = ("This will permanently delete your profile, conversations and support requests from my "
                  "records. Do you want to continue?")
DELETE_DONE = "Your data has been deleted. If you message me again, we'll start fresh."
DELETE_CANCELLED = "Okay, nothing was deleted."
LEARN_PROMPT = "Pick a topic to explore, or just type your own question."
RATE_LIMIT = "You're sending messages quickly. Please wait a moment and try again."
ERROR_GENERIC = "Something went wrong on our side. Please try again in a moment."
NO_PROFILE = "I don't have a profile for you yet. Send /start to set one up."
SKIP_NOTED = "No problem, skipped."


def profile_text(p) -> str:
    exp = {"complete_beginner": "Complete beginner", "beginner": "Beginner with some knowledge",
           "intermediate": "Intermediate trader", "experienced": "Experienced trader"}
    lines = ["Your learning profile", ""]
    lines.append("Traded before: " + ("not set" if p.has_traded is None else ("yes" if p.has_traded else "no")))
    lines.append("Experience: " + exp.get(getattr(p.experience, "value", p.experience), "not set"))
    lines.append("Learning capital for examples: " + (f"Rs {int(p.learning_capital):,}" if p.learning_capital else "not shared"))
    lines.append("Goals: " + (p.objectives or "not set"))
    lines.append("Language: " + (p.language or "English"))
    lines.append("\nSend /start to update these answers.")
    return "\n".join(lines)
