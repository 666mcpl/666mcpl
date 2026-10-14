import os
import asyncio
import random
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands


# =========================================================
# KONFIGURACJA & GRAFIKA
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

TICKET_CATEGORY_ID = 1539334265022582784
MEDIA_CHANNEL_ID = 1553347721770045440
VERIFICATION_CHANNEL_ID = 1553347976662089748
TICKET_PANEL_CHANNEL_ID = 1539334313785565184

POLL_CHANNEL_ID = 1553347567612592239
PROPOSAL_CHANNEL_ID = 1553348406460678264
CONTEST_CHANNEL_ID = 1553347368429031556
RULES_CHANNEL_ID = 1553348189292339280

LOBBY_CHANNEL_ID = 1553347858294509588
CHANGELOG_CHANNEL_ID = 1543311008221630474
URLopy_CHANNEL_ID = 1545541960230506620
LOGI_CHANNEL_ID = 1548480034157895740

# =========================================================
# BANERY I LOGA SERWERA (Zmień linki na własne grafiki)
# =========================================================
# Możesz wkleić tutaj bezpośrednie linki do grafik (np. z Imgura lub kanału z grafikami)
SERVER_ICON_URL = "https://i.imgur.com/example_logo.png"       # Logo w prawym górnym rogu
SERVER_BANNER_URL = "https://i.imgur.com/example_banner.png"   # Szeroki baner na dole embeda TokyoCode[cite: 2]

COLOR_PRIMARY = discord.Color.from_rgb(46, 204, 113)  # Szmaragdowy (główny)
COLOR_DARK = discord.Color.from_rgb(30, 31, 35)       # Ciemny grafit (styl paneli głównych)[cite: 2]
COLOR_BLUE = discord.Color.from_rgb(43, 114, 230)     # Niebieski (propozycje)[cite: 1]
COLOR_RED = discord.Color.from_rgb(231, 76, 60)       # Czerwony (ostrzeżenia / błędy)

# =========================================================
# REKRUTACJA
# =========================================================

RECRUITMENT_CHANNEL_ID = 1553348089023172618

# True = rekrutacja otwarta
# False = rekrutacja zamknięta
RECRUITMENT_OPEN = True


# =========================================================
# ROLE
# =========================================================

CHATMOD_ROLE_ID = 1540390698854129794
HELPER_ROLE_ID = 1539324328368144475
MODERATOR_ROLE_ID = 1539324147660750939
ADMIN_ROLE_ID = 1539323959995015260
TECHNIK_ROLE_ID = 1539323255641341992
DEVELOPER_ROLE_ID = 1539323093728763944
HEAD_ADMIN_ROLE_ID = 1539322826224566342
CEO_ROLE_ID = 1539322697283010631
OWNER_USER_ID = 1459201433152000044

# =========================================================
# FILTR LINKÓW
# =========================================================

LINK_FILTER_BYPASS_ROLE_IDS = {
    CHATMOD_ROLE_ID,
    HELPER_ROLE_ID,
    MODERATOR_ROLE_ID,
    ADMIN_ROLE_ID,
    TECHNIK_ROLE_ID,
    DEVELOPER_ROLE_ID,
    HEAD_ADMIN_ROLE_ID,
    CEO_ROLE_ID,
}

BLOCK_LINKS = True
BLOCK_GIFS = True


# =========================================================
# ANTI @EVERYONE / @HERE
# =========================================================

MENTION_WARNINGS = {}

MENTION_WARNINGS_REQUIRED = 3
MENTION_TIMEOUT_MINUTES = 5
