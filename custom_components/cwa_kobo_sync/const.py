"""Constants for the CWA Kobo Sync integration."""

from datetime import timedelta

DOMAIN = "cwa_kobo_sync"
CONF_SYNC_URL = "sync_url"
SYNC_TOKEN_HEADER = "x-kobo-synctoken"
SYNC_CONTINUE_HEADER = "x-kobo-sync"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
MAX_SYNC_PAGES = 20
