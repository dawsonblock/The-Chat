from __future__ import annotations

import os
import tempfile

_fd, _TEST_DB_PATH = tempfile.mkstemp(suffix='-pytest-operator-one.db')
os.close(_fd)
os.environ['DATABASE_URL'] = f'sqlite:///{_TEST_DB_PATH}'
