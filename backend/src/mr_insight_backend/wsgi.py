"""
WSGI config for mr_insight_backend project.
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Ensure src/ is on the path when running via a WSGI server directly
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mr_insight_backend.settings")

application = get_wsgi_application()
