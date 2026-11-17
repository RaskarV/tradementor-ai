import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
for k, v in {
    "TELEGRAM_BOT_TOKEN": "123456:TESTTOKEN",
    "TELEGRAM_WEBHOOK_SECRET": "test-webhook-secret-123456",
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/test",
    "JWT_SECRET": "test-jwt-secret-that-is-long-enough-123456",
    "ADMIN_TELEGRAM_IDS": "111",
}.items():
    os.environ.setdefault(k, v)
