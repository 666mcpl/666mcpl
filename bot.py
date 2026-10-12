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


LINK_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|discord\.gg/\S+|discord\.com/invite/\S+)",
    re.IGNORECASE
)

GIF_PATTERN = re.compile(
    r"(https?://\S+\.gif(?:\?\S*)?|tenor\.com/\S+|giphy\.com/\S+)",
    re.IGNORECASE
)


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True


# =========================================================
# BOT
# =========================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# TYPY TICKETÓW
# =========================================================

TICKET_TYPES = {
    "pomoc": {
        "name": "Pomoc",
        "description": "Potrzebujesz wsparcia w grze lub na Discordzie",
        "emoji": "🆘"
    },
    "blad": {
        "name": "Błąd",
        "description": "Zgłoś wykryty błąd techniczny lub usterkę",
        "emoji": "🐛"
    },
    "platnosc": {
        "name": "Płatność",
        "description": "Problemy z zakupami w sklepie serwerowym",
        "emoji": "💳"
    },
    "backup": {
        "name": "Chcę uzyskać backup",
        "description": "Zgłoś utratę ekwipunku lub postępu",
        "emoji": "💾"
    },
    "cheater": {
        "name": "Chcę zgłosić cheatera",
        "description": "Zgłoszenie gracza podejrzanego o cheaty / błędy",
        "emoji": "🚨"
    },
    "inne": {
        "name": "Inne",
        "description": "Inne sprawy niewymienione powyżej",
        "emoji": "💡"
    }
}


# =========================================================
# POMOCNICZE
# =========================================================

def has_role_or_higher(
    member: discord.Member,
    role_id: int
):
    role = member.guild.get_role(role_id)

    if role is None:
        return False

    return member.top_role >= role


def can_access_ticket(
    member: discord.Member,
    ticket_type: str
):
    if ticket_type == "platnosc":
        ceo_role = member.guild.get_role(CEO_ROLE_ID)

        return (
            ceo_role is not None
            and ceo_role in member.roles
        )

    chatmod_role = member.guild.get_role(CHATMOD_ROLE_ID)

    if chatmod_role is not None and chatmod_role in member.roles:
        return True

    if ticket_type == "media":
        return has_role_or_higher(
            member,
            MODERATOR_ROLE_ID
        )

    return has_role_or_higher(
        member,
        HELPER_ROLE_ID
    )


async def safe_response(
    interaction: discord.Interaction,
    content: str,
    ephemeral: bool = True
):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                content,
                ephemeral=ephemeral
            )
        else:
            await interaction.response.send_message(
                content,
                ephemeral=ephemeral
            )
    except discord.HTTPException:
        pass


def find_existing_ticket(
    guild: discord.Guild,
    user_id: int
):
    for channel in guild.text_channels:

        if not channel.topic:
            continue

        if channel.topic.startswith(
            f"ticket_owner:{user_id}"
        ):
            return channel

    return None


# =========================================================
# FILTR @EVERYONE / @HERE
# =========================================================

async def punish_everyone_violation(
    message: discord.Message
):
    if not isinstance(message.author, discord.Member):
        return

    member = message.author
    user_id = member.id

    try:
        await message.delete()

    except discord.NotFound:
        return

    except discord.Forbidden:
        print(
            "❌ Bot nie ma uprawnień do usuwania wiadomości."
        )
        return

    except discord.HTTPException as error:
        print(
            f"❌ Błąd usuwania wiadomości: {error}"
        )
        return

    MENTION_WARNINGS[user_id] = (
        MENTION_WARNINGS.get(user_id, 0) + 1
    )

    warnings = MENTION_WARNINGS[user_id]

    if warnings >= MENTION_WARNINGS_REQUIRED:

        try:
            timeout_until = (
                discord.utils.utcnow()
                + timedelta(
                    minutes=MENTION_TIMEOUT_MINUTES
                )
            )

            await member.timeout(
                timeout_until,
                reason="3x użycie @everyone/@here"
            )

            MENTION_WARNINGS[user_id] = 0

            await message.channel.send(
                f"🔇 {member.mention}, "
                f"otrzymujesz **timeout na "
                f"{MENTION_TIMEOUT_MINUTES} minut** "
                "za 3-krotne użycie @everyone/@here.",
                delete_after=8
            )

            print(
                f"🔇 {member} otrzymał timeout."
            )

        except discord.Forbidden:
            try:
                await message.channel.send(
                    f"⚠️ {member.mention}, "
                    "nie możesz używać @everyone/@here.\n"
                    f"Upomnienie **{warnings}/"
                    f"{MENTION_WARNINGS_REQUIRED}**.",
                    delete_after=6
                )
            except discord.HTTPException:
                pass

        except discord.HTTPException as error:
            print(
                f"❌ Błąd nadawania timeoutu: {error}"
            )

        return

    try:
        await message.channel.send(
            f"⚠️ {member.mention}, "
            "nie możesz używać **@everyone/@here**!\n"
            f"Upomnienie **{warnings}/"
            f"{MENTION_WARNINGS_REQUIRED}**.",
            delete_after=6
        )

    except discord.HTTPException:
        pass


# =========================================================
# FILTR LINKÓW / GIF
# =========================================================

async def punish_link_violation(
    message: discord.Message,
    is_gif: bool = False
):
    # Zbieramy dane PRZED usunięciem wiadomości.
    sent_content = (message.content or "").strip()
    attachment_urls = [a.url for a in message.attachments]
    gif_urls = [
        a.url for a in message.attachments
        if a.filename.lower().endswith(".gif")
    ]

    # Logujemy każdą zablokowaną próbę linku/GIF-a przed usunięciem wiadomości.
    try:
        log_channel = bot.get_channel(LOGI_CHANNEL_ID)

        if log_channel is None:
            log_channel = await bot.fetch_channel(LOGI_CHANNEL_ID)

        what_was_sent = sent_content or "Brak tekstu"

        if attachment_urls:
            what_was_sent += "\n" + "\n".join(attachment_urls)

        if is_gif:
            log_title = "🚫 Próba wysłania GIF-a"
            log_footer = "666.6MC • Logi filtra GIF"
        else:
            log_title = "🚫 Próba wysłania linku"
            log_footer = "666.6MC • Logi filtra linków"

        log_embed = discord.Embed(
            title=log_title,
            color=COLOR_RED,
            timestamp=datetime.now()
        )

        log_embed.add_field(
            name="👤 Kto wysłał",
            value=f"{message.author.mention}\n`{message.author}`",
            inline=True
        )

        log_embed.add_field(
            name="📍 Gdzie",
            value=f"{message.channel.mention}\n`#{message.channel.name}`",
            inline=True
        )

        log_embed.add_field(
            name="🔗 Co wysłał",
            value=f"```text\n{what_was_sent[:1000]}\n```",
            inline=False
        )

        if gif_urls:
            log_embed.add_field(
                name="🖼️ Link do GIF-a",
                value="\n".join(gif_urls)[:1024],
                inline=False
            )

        log_embed.set_footer(text=log_footer)

        await log_channel.send(
            embed=log_embed,
            allowed_mentions=discord.AllowedMentions.none()
        )

    except (discord.HTTPException, discord.Forbidden, discord.NotFound) as error:
        print(f"❌ Nie udało się wysłać logu linku/GIF-a: {error}")

    try:
        await message.delete()
    except discord.NotFound:
        return
    except discord.Forbidden:
        print("❌ Bot nie ma uprawnień do usuwania wiadomości.")
        return
    except discord.HTTPException as error:
        print(f"❌ Błąd usuwania wiadomości: {error}")
        return

    try:
        await message.channel.send(
            f"⚠️ {message.author.mention}, "
            "linki oraz pliki GIF są tutaj niedozwolone.",
            delete_after=5
        )
    except discord.HTTPException:
        pass


# =========================================================
# TICKET — MODAL
# =========================================================

class TicketModal(discord.ui.Modal):

    def __init__(self, ticket_type):

        self.ticket_type = ticket_type

        ticket_name = TICKET_TYPES[
            ticket_type
        ]["name"]

        super().__init__(
            title=f"Formularz — {ticket_name}"
        )

        self.minecraft_nick = discord.ui.TextInput(
            label="Nick z Minecrafta",
            placeholder="Wpisz swój dokładny nick z gry",
            required=True,
            max_length=32
        )

        if ticket_type == "platnosc":

            self.product = discord.ui.TextInput(
                label="Co chcesz kupić / kupiłeś?",
                placeholder="Np. SVIP, ranga, przedmiot, usługa...",
                required=True,
                max_length=200
            )

            self.price = discord.ui.TextInput(
                label="Za ile chcesz kupić?",
                placeholder="Np. 20 zł",
                required=True,
                max_length=50
            )

            self.payment_method = discord.ui.TextInput(
                label="Metoda płatności",
                placeholder="Np. PayPal, BLIK, przelew, PaySafeCard...",
                required=True,
                max_length=100
            )

            self.description = discord.ui.TextInput(
                label="Dodatkowe informacje",
                placeholder="Napisz coś, co powinniśmy wiedzieć...",
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=1000
            )

            self.add_item(self.minecraft_nick)
            self.add_item(self.product)
            self.add_item(self.price)
            self.add_item(self.payment_method)
            self.add_item(self.description)

        elif ticket_type == "backup":

            self.description = discord.ui.TextInput(
                label="Opis sytuacji",
                placeholder="Opisz, jaki backup potrzebujesz i z jakiego powodu...",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=1000
            )

            self.add_item(self.minecraft_nick)
            self.add_item(self.description)

        elif ticket_type == "cheater":

            self.cheater_nick = discord.ui.TextInput(
                label="Nick osoby, którą zgłaszasz",
                placeholder="Wpisz nick gracza podejrzanego o cheaty",
                required=True,
                max_length=32
            )

            self.description = discord.ui.TextInput(
                label="Opis sytuacji & Dowody",
                placeholder="Opisz dokładnie sytuację i wklej linki do dowodów...",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=1000
            )

            self.add_item(self.cheater_nick)
            self.add_item(self.description)

        else:

            self.description = discord.ui.TextInput(
                label="Opis sprawy",
                placeholder="Opisz dokładnie, w czym potrzebujesz pomocy...",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=1000
            )

            self.add_item(self.minecraft_nick)
            self.add_item(self.description)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild
        user = interaction.user

        if guild is None:
            await safe_response(
                interaction,
                "❌ Nie znaleziono serwera."
            )
            return

        category = guild.get_channel(
            TICKET_CATEGORY_ID
        )

        if category is None or not isinstance(category, discord.CategoryChannel):
            await safe_response(
                interaction,
                "❌ Nie znaleziono prawidłowej kategorii ticketów na serwerze."
            )
            return

        existing_ticket = find_existing_ticket(
            guild,
            user.id
        )

        if existing_ticket is not None:
            await safe_response(
                interaction,
                "⚠️ **Posiadasz już aktywne zgłoszenie!**\n\n"
                f"> Twój otwarty ticket: {existing_ticket.mention}\n"
                "> Przed otwarciem nowego, musisz zamknąć poprzedni."
            )
            return

        ticket_info = TICKET_TYPES[
            self.ticket_type
        ]

        safe_username = re.sub(
            r"[^a-zA-Z0-9\-_]",
            "",
            user.name.lower()
        )

        if not safe_username:
            safe_username = str(user.id)

        channel_name = (
            f"ticket-{self.ticket_type}-{safe_username}"
        )[:100]

        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )
        }

        if self.ticket_type == "platnosc":
            staff_roles = [CEO_ROLE_ID]
        elif self.ticket_type == "media":
            staff_roles = [
                CHATMOD_ROLE_ID,
                MODERATOR_ROLE_ID,
                ADMIN_ROLE_ID,
                TECHNIK_ROLE_ID,
                DEVELOPER_ROLE_ID,
                HEAD_ADMIN_ROLE_ID,
                CEO_ROLE_ID
            ]
        else:
            staff_roles = [
                CHATMOD_ROLE_ID,
                HELPER_ROLE_ID,
                MODERATOR_ROLE_ID,
                ADMIN_ROLE_ID,
                TECHNIK_ROLE_ID,
                DEVELOPER_ROLE_ID,
                HEAD_ADMIN_ROLE_ID,
                CEO_ROLE_ID
            ]

        for role_id in staff_roles:
            role = guild.get_role(role_id)
            if role is not None:
                overwrites[role] = (
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        attach_files=True,
                        embed_links=True
                    )
                )

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=(
                    f"ticket_owner:{user.id}"
                    f"|ticket_type:{self.ticket_type}"
                ),
                reason=f"Ticket utworzony przez {user}"
            )

        except discord.Forbidden:
            await safe_response(
                interaction,
                "❌ Bot nie ma uprawnień do zarządzania kanałami (**Manage Channels**)."
            )
            return

        except discord.HTTPException as error:
            print(f"❌ Błąd tworzenia ticketu: {error}")
            await safe_response(
                interaction,
                "❌ Wystąpił nieoczekiwany błąd podczas tworzenia kanału."
            )
            return

        # Profesjonalny Embed wewnątrz kanału Ticketu[cite: 2]
        embed = discord.Embed(
            title=f"{ticket_info['emoji']} ZGŁOSZENIE — {ticket_info['name'].upper()}",
            description=(
                f"Witaj {user.mention}!\n\n"
                "> Dziękujemy za utworzenie zgłoszenia w centrum pomocy **666.6MC**.\n"
                "> Prosimy o cierpliwość – wolny członek administracji odpisze najszybciej, jak to możliwe.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=COLOR_PRIMARY,
            timestamp=datetime.now()
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(
            name="👤 Użytkownik",
            value=f"{user.mention}\n`{user.name}`",
            inline=True
        )

        embed.add_field(
            name="🎮 Nick z gry",
            value=f"`{self.minecraft_nick.value}`",
            inline=True
        )

        embed.add_field(
            name="📂 Kategoria",
            value=f"`{ticket_info['name']}`",
            inline=True
        )

        if self.ticket_type == "platnosc":
            embed.add_field(name="🛒 Produkt", value=f"> {self.product.value}", inline=False)
            embed.add_field(name="💰 Kwota", value=f"`{self.price.value}`", inline=True)
            embed.add_field(name="💳 Płatność", value=f"`{self.payment_method.value}`", inline=True)
            if self.description.value:
                embed.add_field(
                    name="📝 Informacje",
                    value=f"```text\n{self.description.value}\n```",
                    inline=False
                )

        elif self.ticket_type == "backup":
            embed.add_field(
                name="📝 Opis sytuacji",
                value=f"```text\n{self.description.value}\n```",
                inline=False
            )

        elif self.ticket_type == "cheater":
            embed.add_field(
                name="🚨 Zgłoszony gracz",
                value=f"`{self.cheater_nick.value}`",
                inline=False
            )
            embed.add_field(
                name="📝 Opis i dowody",
                value=f"```text\n{self.description.value}\n```",
                inline=False
            )

        else:
            embed.add_field(
                name="📝 Treść zgłoszenia",
                value=f"```text\n{self.description.value}\n```",
                inline=False
            )

        embed.set_footer(
            text="666.6MC • Aby zakończyć zgłoszenie, kliknij przycisk poniżej."
        )

        try:
            await channel.send(
                content=f"{user.mention}",
                embed=embed,
                view=CloseTicketView()
            )

            await safe_response(
                interaction,
                f"✅ Zgłoszenie zostało pomyślnie utworzone: {channel.mention}"
            )

        except discord.HTTPException as error:
            print(f"❌ Błąd wysyłania panelu ticketu: {error}")
            await safe_response(
                interaction,
                f"✅ Zgłoszenie utworzone: {channel.mention}"
            )


# =========================================================
# ZAMYKANIE TICKETU
# =========================================================

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Zamknij ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_button"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        channel = interaction.channel
        user = interaction.user

        if channel is None:
            return

        ticket_type = None
        owner_id = None

        if channel.topic:
            parts = channel.topic.split("|")
            for part in parts:
                if part.startswith("ticket_owner:"):
                    owner_id = part[len("ticket_owner:"):]
                elif part.startswith("ticket_type:"):
                    ticket_type = part[len("ticket_type:"):]

        is_owner = owner_id == str(user.id)
        is_staff = False

        if ticket_type:
            is_staff = can_access_ticket(user, ticket_type)

        if not (is_owner or is_staff):
            await safe_response(
                interaction,
                "❌ Nie posiadasz wystarczających uprawnień do zamknięcia tego ticketu."
            )
            return

        close_embed = discord.Embed(
            description="🔒 **Zgłoszenie zostanie trwale zamknięte i usunięte za 3 sekundy...**",
            color=COLOR_RED
        )

        if interaction.response.is_done():
            await interaction.followup.send(embed=close_embed)
        else:
            await interaction.response.send_message(embed=close_embed)

        await asyncio.sleep(3)

        try:
            await channel.delete(
                reason=f"Ticket zamknięty przez {user}"
            )
        except discord.NotFound:
            pass
        except discord.Forbidden:
            print("❌ Bot nie ma uprawnień do usunięcia ticketu.")
        except discord.HTTPException as error:
            print(f"❌ Błąd usuwania ticketu: {error}")


# =========================================================
# PANEL TICKETÓW (STYL TOKYOCODE)[cite: 2]
# =========================================================

class TicketSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label=data["name"],
                description=data["description"],
                emoji=data["emoji"],
                value=key
            )
            for key, data in TICKET_TYPES.items()
        ]

        super().__init__(
            placeholder="Wybierz kategorię zgłoszenia...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_category_select"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        ticket_type = self.values[0]
        try:
            modal = TicketModal(ticket_type)
            await interaction.response.send_modal(modal)
        except Exception as error:
            import traceback
            print(f"❌ BŁĄD OTWIERANIA MODALA '{ticket_type}': {error!r}")
            traceback.print_exc()
            await safe_response(
                interaction,
                "❌ Nie udało się otworzyć formularza ticketu."
            )


class TicketPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


def create_ticket_embed():
    """Nowoczesny layout panelu wzorowany na profesjonalnych serwerach (TokyoCode)[cite: 2]"""
    embed = discord.Embed(
        title="Centrum zgłoszeń",
        description=(
            "Masz pytanie, potrzebujesz pomocy lub chcesz coś zakupić? Wybierz odpowiednią kategorię zgłoszenia poniżej.\n\n"
            "**Pamiętaj**, że administracja ma również swoje życie prywatne, dlatego prosimy o cierpliwość i niepingowanie.\n\n"
            "┃ Wybierz kategorię **zgłoszenia** z poniższego paska wyboru."
        ),
        color=COLOR_DARK
    )

    if SERVER_ICON_URL and "http" in SERVER_ICON_URL:
        embed.set_thumbnail(url=SERVER_ICON_URL)

    if SERVER_BANNER_URL and "http" in SERVER_BANNER_URL:
        embed.set_image(url=SERVER_BANNER_URL)

    embed.set_footer(text="666.6MC • Oficjalny system pomocy")
    return embed


# =========================================================
# REKRUTACJA
# =========================================================

def create_recruitment_embed():

    if RECRUITMENT_OPEN:
        embed = discord.Embed(
            title="📋 REKRUTACJA — 666.6MC",
            description=(
                "Chcesz dołączyć do zespołu administracji naszego serwera?\n\n"
                "Jeżeli czujesz się na siłach, spełniasz wymagania i masz czas na pomoc graczom, "
                "kliknij poniższy przycisk **📝 ZŁÓŻ REKRUTACJĘ** i wypełnij krótki formularz.\n\n"
                "**📌 Ważne wskazówki:**\n"
                "• Odpowiadaj szczerze i wyczerpująco.\n"
                "• Nie składaj kilku podań w krótkim odstępie czasu.\n"
                "• Złożenie podania nie jest gwarancją przyjęcia na okres próbny.\n\n"
                "🟢 **STATUS: REKRUTACJA JEST OTWARTA**\n"
                "Życzymy powodzenia! 💚"
            ),
            color=COLOR_PRIMARY
        )
        if SERVER_ICON_URL and "http" in SERVER_ICON_URL:
            embed.set_thumbnail(url=SERVER_ICON_URL)
        return embed

    embed = discord.Embed(
        title="📋 REKRUTACJA — 666.6MC",
        description=(
            "Aktualnie rekrutacja do ekipy serwera jest **zamknięta**.\n\n"
            "> Śledź ogłoszenia, aby dowiedzieć się o kolejnym naborze."
        ),
        color=COLOR_RED
    )
    return embed


class RecruitmentModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Formularz Rekrutacyjny")

        self.minecraft_nick = discord.ui.TextInput(
            label="Nick z Minecrafta",
            placeholder="Wpisz swój dokładny nick z gry",
            required=True,
            max_length=32
        )

        self.age = discord.ui.TextInput(
            label="Wiek",
            placeholder="Np. 16",
            required=True,
            max_length=3
        )

        self.experience = discord.ui.TextInput(
            label="Doświadczenie",
            placeholder="Opisz swoje wcześniejsze doświadczenie w administracji...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.availability = discord.ui.TextInput(
            label="Dyspozycyjność tygodniowa",
            placeholder="Ile godzin tygodniowo możesz poświęcić na serwer?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.reason = discord.ui.TextInput(
            label="Dlaczego właśnie Ty powinieneś dołączyć?",
            placeholder="Napisz kilka zdań o sobie i swoich mocnych stronach...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1500
        )

        self.add_item(self.minecraft_nick)
        self.add_item(self.age)
        self.add_item(self.experience)
        self.add_item(self.availability)
        self.add_item(self.reason)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        global RECRUITMENT_OPEN

        if not RECRUITMENT_OPEN:
            await safe_response(
                interaction,
                "🔴 Rekrutacja została w międzyczasie zamknięta."
            )
            return

        guild = interaction.guild
        user = interaction.user

        if guild is None:
            await safe_response(interaction, "❌ Nie znaleziono serwera.")
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)

        if category is None or not isinstance(category, discord.CategoryChannel):
            await safe_response(interaction, "❌ Kategoria zgłoszeń nie została odnaleziona.")
            return

        existing_ticket = find_existing_ticket(guild, user.id)

        if existing_ticket is not None:
            await safe_response(
                interaction,
                f"⚠️ Posiadasz już otwarte zgłoszenie: {existing_ticket.mention}"
            )
            return

        safe_username = re.sub(r"[^a-zA-Z0-9\-_]", "", user.name.lower()) or str(user.id)
        channel_name = f"rekrutacja-{safe_username}"[:100]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        }

        staff_roles = [
            CHATMOD_ROLE_ID,
            HELPER_ROLE_ID,
            MODERATOR_ROLE_ID,
            ADMIN_ROLE_ID,
            TECHNIK_ROLE_ID,
            DEVELOPER_ROLE_ID,
            HEAD_ADMIN_ROLE_ID,
            CEO_ROLE_ID
        ]

        for role_id in staff_roles:
            role = guild.get_role(role_id)
            if role is not None:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"ticket_owner:{user.id}|ticket_type:rekrutacja",
                reason=f"Rekrutacja utworzona przez {user}"
            )
        except discord.Forbidden:
            await safe_response(interaction, "❌ Bot nie posiada uprawnień do tworzenia kanałów.")
            return
        except discord.HTTPException as error:
            print(f"❌ Błąd tworzenia rekrutacji: {error}")
            await safe_response(interaction, "❌ Błąd podczas generowania kanału rekrutacji.")
            return

        embed = discord.Embed(
            title="📋 NOWE PODANIE O REKRUTACJĘ — 666.6MC",
            description=f"Użytkownik {user.mention} złożył nowe podanie rekrutacyjne.",
            color=COLOR_PRIMARY,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(name="👤 Kandydat", value=f"{user.mention}\n`{user.name}`", inline=True)
        embed.add_field(name="🎮 Nick Minecraft", value=f"`{self.minecraft_nick.value}`", inline=True)
        embed.add_field(name="🎂 Wiek", value=f"`{self.age.value}`", inline=True)

        embed.add_field(
            name="🛡️ Doświadczenie",
            value=f"```text\n{self.experience.value}\n```",
            inline=False
        )
        embed.add_field(
            name="⏰ Dyspozycyjność",
            value=f"```text\n{self.availability.value}\n```",
            inline=False
        )
        embed.add_field(
            name="💬 Dlaczego ta osoba?",
            value=f"```text\n{self.reason.value}\n```",
            inline=False
        )

        embed.set_footer(text="666.6MC • System rekrutacji administracyjnej")

        try:
            await channel.send(
                content=user.mention,
                embed=embed,
                view=CloseTicketView()
            )
            await safe_response(
                interaction,
                f"✅ Twoje podanie zostało pomyślnie złożone: {channel.mention}"
            )
        except discord.HTTPException as error:
            print(f"❌ Błąd wysyłania rekrutacji: {error}")
            await safe_response(interaction, f"✅ Zgłoszenie utworzone: {channel.mention}")


class RecruitmentView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ZŁÓŻ REKRUTACJĘ",
        emoji="📝",
        style=discord.ButtonStyle.success,
        custom_id="recruitment_application_button"
    )
    async def recruitment_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not RECRUITMENT_OPEN:
            await safe_response(interaction, "🔴 Rekrutacja jest w tym momencie zamknięta.")
            return

        await interaction.response.send_modal(RecruitmentModal())


async def update_recruitment_panel(guild: discord.Guild):
    channel = guild.get_channel(RECRUITMENT_CHANNEL_ID)
    if channel is None:
        return False

    try:
        async for message in channel.history(limit=50):
            if (
                message.author == bot.user
                and message.embeds
                and "REKRUTACJA — 666.6MC" in (message.embeds[0].title or "")
            ):
                await message.edit(
                    embed=create_recruitment_embed(),
                    view=RecruitmentView()
                )
                return True

        await channel.send(
            embed=create_recruitment_embed(),
            view=RecruitmentView()
        )
        return True

    except discord.HTTPException as error:
        print(f"❌ Błąd panelu rekrutacji: {error}")
        return False


@bot.tree.command(name="startrekrutacja", description="Otwiera rekrutację do ekipy serwera.")
async def startrekrutacja(interaction: discord.Interaction):
    global RECRUITMENT_OPEN

    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna wyłącznie na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko ranga CEO ma uprawnienia do otwarcia rekrutacji.")
        return

    RECRUITMENT_OPEN = True
    success = await update_recruitment_panel(interaction.guild)

    if success:
        await safe_response(interaction, "🟢 **Rekrutacja została pomyślnie otwarta!**")
    else:
        await safe_response(interaction, "⚠️ Otwarto rekrutację, lecz wystąpił problem z panelem.")


@bot.tree.command(name="stoprekrutacja", description="Zamyka rekrutację do ekipy serwera.")
async def stoprekrutacja(interaction: discord.Interaction):
    global RECRUITMENT_OPEN

    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna wyłącznie na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko ranga CEO ma uprawnienia do zamknięcia rekrutacji.")
        return

    RECRUITMENT_OPEN = False
    success = await update_recruitment_panel(interaction.guild)

    if success:
        await safe_response(interaction, "🔴 **Rekrutacja została pomyślnie zamknięta!**")
    else:
        await safe_response(interaction, "⚠️ Zamknięto rekrutację, lecz wystąpił problem z panelem.")


# =========================================================
# MEDIA
# =========================================================

class MediaView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ZŁÓŻ WNIOSEK MEDIA",
        emoji="🎥",
        style=discord.ButtonStyle.success,
        custom_id="media_application_button"
    )
    async def media_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(MediaModal())


class MediaModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Wniosek o rangę MEDIA")

        self.minecraft_nick = discord.ui.TextInput(
            label="Nick z Minecrafta",
            placeholder="Wpisz swój dokładny nick z gry",
            required=True,
            max_length=32
        )

        self.platform = discord.ui.TextInput(
            label="Link do kanału / profilu",
            placeholder="Wklej link do YouTube lub TikToka",
            required=True,
            max_length=500
        )

        self.followers = discord.ui.TextInput(
            label="Liczba subskrypcji / obserwacji",
            placeholder="Np. 250",
            required=True,
            max_length=20
        )

        self.videos = discord.ui.TextInput(
            label="Linki do filmów z serwera",
            placeholder="Wklej linki do min. 5 opublikowanych materiałów z 666.6MC",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1500
        )

        self.description = discord.ui.TextInput(
            label="Dodatkowe informacje",
            placeholder="Coś, co chcesz nam przekazać...",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )

        self.add_item(self.minecraft_nick)
        self.add_item(self.platform)
        self.add_item(self.followers)
        self.add_item(self.videos)
        self.add_item(self.description)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        guild = interaction.guild
        user = interaction.user

        if guild is None:
            await safe_response(interaction, "❌ Nie znaleziono serwera.")
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category is None or not isinstance(category, discord.CategoryChannel):
            await safe_response(interaction, "❌ Kategoria zgłoszeń jest nieprawidłowa.")
            return

        existing = find_existing_ticket(guild, user.id)
        if existing:
            await safe_response(interaction, f"⚠️ Posiadasz już aktywne zgłoszenie: {existing.mention}")
            return

        safe_username = re.sub(r"[^a-zA-Z0-9\-_]", "", user.name.lower()) or str(user.id)
        channel_name = f"media-{safe_username}"[:100]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        }

        staff_roles = [
            CHATMOD_ROLE_ID,
            MODERATOR_ROLE_ID,
            ADMIN_ROLE_ID,
            TECHNIK_ROLE_ID,
            DEVELOPER_ROLE_ID,
            HEAD_ADMIN_ROLE_ID,
            CEO_ROLE_ID
        ]

        for role_id in staff_roles:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"ticket_owner:{user.id}|ticket_type:media",
                reason=f"Wniosek MEDIA utworzony przez {user}"
            )
        except discord.Forbidden:
            await safe_response(interaction, "❌ Bot nie może utworzyć ticketu MEDIA.")
            return
        except discord.HTTPException as error:
            print(f"❌ Błąd tworzenia ticketu MEDIA: {error}")
            await safe_response(interaction, "❌ Błąd tworzenia kanału.")
            return

        embed = discord.Embed(
            title="🎥 NOWY WNIOSEK O RANGĘ MEDIA",
            description=f"Użytkownik {user.mention} zgłasza chęć dołączenia do programu partnerskiego.",
            color=COLOR_PRIMARY,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(name="👤 Twórca", value=f"{user.mention}\n`{user.name}`", inline=True)
        embed.add_field(name="🎮 Nick Minecraft", value=f"`{self.minecraft_nick.value}`", inline=True)
        embed.add_field(name="📊 Liczba widzów", value=f"`{self.followers.value}`", inline=True)
        embed.add_field(name="🔗 Kanał / Profil", value=self.platform.value, inline=False)
        embed.add_field(name="🎬 Filmy z 666.6MC", value=f"```text\n{self.videos.value}\n```", inline=False)

        if self.description.value:
            embed.add_field(name="📝 Uwagi", value=f"```text\n{self.description.value}\n```", inline=False)

        embed.set_footer(text="666.6MC • Weryfikacja twórców internetowych")

        try:
            await channel.send(
                content=user.mention,
                embed=embed,
                view=CloseTicketView()
            )
        except discord.HTTPException as error:
            print(f"❌ Błąd wysyłania wniosku Media: {error}")

        await safe_response(
            interaction,
            f"✅ Twój wniosek MEDIA został pomyślnie utworzony: {channel.mention}"
        )


def create_media_embed():
    embed = discord.Embed(
        title="WSPÓŁPRACA ORAZ RANGA MEDIA — 666.6MC.PL",
        description=(
            "Tworzysz treści internetowe i nagrywasz filmy z naszego serwera?\n"
            "Dołącz do oficjalnego grona twórców **666.6MC** i zgarnij unikalne bonusy!\n\n"
            "**📋 Wymagania minimalne:**\n"
            "• Minimum **25 subskrypcji** na kanale YouTube **LUB** **50 obserwujących** na TikToku\n"
            "• Przynajmniej **5 opublikowanych filmów / shorts / tiktoków** z serwera **666.6mc.pl**\n\n"
            "Spełniasz powyższe punkty? Kliknij przycisk poniżej i wypełnij zgłoszenie!"
        ),
        color=COLOR_PRIMARY
    )
    if SERVER_ICON_URL and "http" in SERVER_ICON_URL:
        embed.set_thumbnail(url=SERVER_ICON_URL)
    return embed


# =========================================================
# WERYFIKACJA (STYL TOKYOCODE)[cite: 2]
# =========================================================

def create_verification_embed():
    embed = discord.Embed(
        title="Weryfikacja Konta",
        description=(
            "Witaj na oficjalnym serwerze Discord społeczności **666.6MC**!\n\n"
            "> Aby zabezpieczyć serwer przed botami oraz odblokować pełny dostęp do kanałów,\n"
            "> kliknij poniższy przycisk **Zweryfikuj się**.\n\n"
            "┃ Przestrzegaj regulaminu i ciesz się wspólną rozgrywką!"
        ),
        color=COLOR_DARK
    )
    if SERVER_ICON_URL and "http" in SERVER_ICON_URL:
        embed.set_thumbnail(url=SERVER_ICON_URL)
    if SERVER_BANNER_URL and "http" in SERVER_BANNER_URL:
        embed.set_image(url=SERVER_BANNER_URL)
    embed.set_footer(text="666.6MC • System weryfikacji anty-bot")
    return embed


class VerificationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Zweryfikuj się",
        emoji="🛡️",
        style=discord.ButtonStyle.success,
        custom_id="verification_button"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "✅ Pomyślnie zweryfikowano Twoje konto. Miłego pobytu na serwerze!",
            ephemeral=True
        )


# =========================================================
# ANKIETY
# =========================================================

class PollData:

    def __init__(
        self,
        question,
        option_one,
        option_two,
        duration_minutes,
        creator_id
    ):
        self.question = question
        self.option_one = option_one
        self.option_two = option_two
        self.duration_minutes = duration_minutes
        self.creator_id = creator_id

        self.votes_one = set()
        self.votes_two = set()

        self.message = None
        self.end_time = datetime.now() + timedelta(minutes=duration_minutes)
        self.finished = False


ACTIVE_POLLS = []


def create_poll_embed(poll):
    votes_one = len(poll.votes_one)
    votes_two = len(poll.votes_two)
    total_votes = votes_one + votes_two

    if total_votes > 0:
        p1 = (votes_one / total_votes) * 100
        p2 = (votes_two / total_votes) * 100
    else:
        p1 = 0
        p2 = 0

    end_ts = int(poll.end_time.timestamp())

    status = (
        "🔴 **ANKIETA ZAKOŃCZONA**"
        if poll.finished
        else f"🟢 **ANKIETA W TOKU** • Kończy się <t:{end_ts}:R>"
    )

    embed = discord.Embed(
        title=f"📊 {poll.question}",
        description=(
            f"{status}\n\n"
            f"> Zagłosuj na wybraną opcję za pomocą przycisków pod wiadomością.\n\n"
            f"🟢 **{poll.option_one}**\n"
            f"┗ **{votes_one}** głosów ({p1:.1f}%)\n\n"
            f"🔵 **{poll.option_two}**\n"
            f"┗ **{votes_two}** głosów ({p2:.1f}%)"
        ),
        color=COLOR_PRIMARY
    )

    embed.add_field(name="🗳️ Oddanych głosów", value=f"`{total_votes}`", inline=True)
    embed.add_field(name="⏱️ Czas trwania", value=f"`{poll.duration_minutes} min`", inline=True)
    embed.set_footer(text="666.6MC • Oficjalne ankiety serwerowe")
    return embed


class PollView(discord.ui.View):

    def __init__(self, poll):
        super().__init__(timeout=None)
        self.poll = poll

        self.option_one_button = discord.ui.Button(
            label=poll.option_one,
            emoji="🟢",
            style=discord.ButtonStyle.success,
            custom_id=f"poll_one_{id(poll)}"
        )

        self.option_two_button = discord.ui.Button(
            label=poll.option_two,
            emoji="🔵",
            style=discord.ButtonStyle.primary,
            custom_id=f"poll_two_{id(poll)}"
        )

        self.option_one_button.callback = self.vote_one
        self.option_two_button.callback = self.vote_two

        self.add_item(self.option_one_button)
        self.add_item(self.option_two_button)

    async def vote_one(self, interaction: discord.Interaction):
        await self.handle_vote(interaction, 1)

    async def vote_two(self, interaction: discord.Interaction):
        await self.handle_vote(interaction, 2)

    async def handle_vote(self, interaction, option):
        if self.poll.finished:
            await safe_response(interaction, "🔴 Ta ankieta została już zakończona.")
            return

        user_id = interaction.user.id

        if user_id in self.poll.votes_one or user_id in self.poll.votes_two:
            await safe_response(interaction, "⚠️ Twój głos w tej ankiecie został już wcześniej zarejestrowany.")
            return

        if option == 1:
            self.poll.votes_one.add(user_id)
        else:
            self.poll.votes_two.add(user_id)

        try:
            await interaction.message.edit(
                embed=create_poll_embed(self.poll),
                view=self
            )
            await safe_response(interaction, "✅ Pomyślnie oddano głos!")
        except discord.HTTPException as error:
            print(f"❌ Błąd aktualizacji ankiety: {error}")


async def finish_poll_after_delay(poll, view):
    await asyncio.sleep(poll.duration_minutes * 60)

    if poll.finished:
        return

    poll.finished = True
    view.option_one_button.disabled = True
    view.option_two_button.disabled = True

    if poll.message is not None:
        try:
            await poll.message.edit(
                embed=create_poll_embed(poll),
                view=view
            )
        except (discord.NotFound, discord.HTTPException):
            pass


class PollModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Kreator nowej ankiety")

        self.question = discord.ui.TextInput(
            label="Pytanie ankiety",
            placeholder="Np. Czy wprowadzić nową edycję trybu Survival?",
            required=True,
            max_length=200
        )

        self.option_one = discord.ui.TextInput(
            label="Opcja 1",
            placeholder="Np. Tak",
            required=True,
            max_length=80
        )

        self.option_two = discord.ui.TextInput(
            label="Opcja 2",
            placeholder="Np. Nie",
            required=True,
            max_length=80
        )

        self.duration = discord.ui.TextInput(
            label="Czas trwania (w minutach)",
            placeholder="Np. 60",
            required=True,
            max_length=6
        )

        self.add_item(self.question)
        self.add_item(self.option_one)
        self.add_item(self.option_two)
        self.add_item(self.duration)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            duration_minutes = int(self.duration.value)
        except ValueError:
            await safe_response(interaction, "❌ Czas trwania musi być liczbą całkowitą.")
            return

        if duration_minutes < 1 or duration_minutes > 10080:
            await safe_response(interaction, "❌ Czas trwania musi mieścić się w przedziale 1 - 10080 minut.")
            return

        if interaction.guild is None:
            return

        poll_channel = interaction.guild.get_channel(POLL_CHANNEL_ID)
        if poll_channel is None:
            await safe_response(interaction, "❌ Nie odnaleziono kanału ankiet.")
            return

        poll = PollData(
            question=self.question.value,
            option_one=self.option_one.value,
            option_two=self.option_two.value,
            duration_minutes=duration_minutes,
            creator_id=interaction.user.id
        )

        ACTIVE_POLLS.append(poll)
        view = PollView(poll)

        try:
            message = await poll_channel.send(
                embed=create_poll_embed(poll),
                view=view
            )
            poll.message = message

            await safe_response(
                interaction,
                f"✅ Ankieta opublikowana: {message.jump_url}"
            )
            asyncio.create_task(finish_poll_after_delay(poll, view))

        except discord.HTTPException as error:
            print(f"❌ Błąd tworzenia ankiety: {error}")
            await safe_response(interaction, "❌ Wystąpił błąd podczas wysyłania ankiety.")


@bot.tree.command(name="ankieta", description="Tworzy nową ankietę serwerową.")
async def ankieta(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna tylko na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko CEO posiada uprawnienia do tworzenia ankiet.")
        return

    await interaction.response.send_modal(PollModal())


@bot.tree.command(name="glosy", description="Pokazuje listę użytkowników głosujących w ankiecie.")
async def glosy(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna tylko na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko CEO może sprawdzać szczegóły głosów.")
        return

    polls = [p for p in ACTIVE_POLLS if not p.finished]
    if not polls:
        await safe_response(interaction, "ℹ️ Nie znaleziono żadnej trwającej ankiety.")
        return

    for poll in polls:
        one_names = [
            (interaction.guild.get_member(uid).mention if interaction.guild.get_member(uid) else f"`{uid}`")
            for uid in poll.votes_one
        ]
        two_names = [
            (interaction.guild.get_member(uid).mention if interaction.guild.get_member(uid) else f"`{uid}`")
            for uid in poll.votes_two
        ]

        embed = discord.Embed(
            title="🗳️ PODGLĄD GŁOSÓW — ANKIETA",
            description=f"**{poll.question}**",
            color=COLOR_PRIMARY
        )
        embed.add_field(
            name=f"🟢 {poll.option_one} ({len(one_names)})",
            value="\n".join(one_names)[:1024] if one_names else "*Brak głosów*",
            inline=False
        )
        embed.add_field(
            name=f"🔵 {poll.option_two} ({len(two_names)})",
            value="\n".join(two_names)[:1024] if two_names else "*Brak głosów*",
            inline=False
        )
        embed.set_footer(text="666.6MC • Wgląd administracyjny")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        return


# =========================================================
# KONKURSY
# =========================================================

class ContestData:

    def __init__(
        self,
        prize,
        winners_count,
        duration_minutes,
        creator_id
    ):
        self.prize = prize
        self.winners_count = winners_count
        self.duration_minutes = duration_minutes
        self.creator_id = creator_id

        self.participants = set()
        self.message = None
        self.finished = False
        self.end_time = datetime.now() + timedelta(minutes=duration_minutes)


def create_contest_embed(contest):
    participant_count = len(contest.participants)
    end_timestamp = int(contest.end_time.timestamp())

    status = (
        "🔴 **KONKURS ROZSTRZYGNIĘTY**"
        if contest.finished
        else f"🟢 **KONKURS AKTYWNY** • Zakończenie <t:{end_timestamp}:R>"
    )

    embed = discord.Embed(
        title="🎉 OFICJALNY KONKURS — 666.6MC",
        description=(
            f"{status}\n\n"
            f"🎁 **Główna nagroda:**\n"
            f"> **{contest.prize}**\n\n"
            f"🏆 **Ilość wygrywających:** `{contest.winners_count}`\n"
            f"👥 **Łącznie zgłoszonych:** `{participant_count}`\n\n"
            "Aby dołączyć do losowania, wciśnij poniższy przycisk **🎉 Weź udział**!"
        ),
        color=COLOR_PRIMARY
    )
    embed.set_footer(text="666.6MC • Życzymy powodzenia!")
    return embed


class ContestView(discord.ui.View):

    def __init__(self, contest):
        super().__init__(timeout=None)
        self.contest = contest

        self.join_button = discord.ui.Button(
            label="Weź udział",
            emoji="🎉",
            style=discord.ButtonStyle.success,
            custom_id=f"contest_join_{id(contest)}"
        )
        self.join_button.callback = self.join_contest
        self.add_item(self.join_button)

    async def join_contest(self, interaction: discord.Interaction):
        if self.contest.finished:
            await safe_response(interaction, "🔴 Ten konkurs został już zakończony.")
            return

        user_id = interaction.user.id
        if user_id in self.contest.participants:
            await safe_response(interaction, "⚠️ Zostałeś już wcześniej zapisany do tego losowania!")
            return

        self.contest.participants.add(user_id)

        try:
            await interaction.message.edit(
                embed=create_contest_embed(self.contest),
                view=self
            )
            await safe_response(interaction, "🎉 Zostałeś pomyślnie dodany do listy uczestników!")
        except discord.HTTPException as error:
            print(f"❌ Błąd aktualizacji konkursu: {error}")


async def finish_contest_after_delay(contest, view):
    await asyncio.sleep(contest.duration_minutes * 60)

    if contest.finished:
        return

    contest.finished = True
    view.join_button.disabled = True

    winners = []
    if contest.participants:
        w_count = min(contest.winners_count, len(contest.participants))
        winners = random.sample(list(contest.participants), w_count)

    if contest.message is None:
        return

    try:
        await contest.message.edit(
            embed=create_contest_embed(contest),
            view=view
        )

        if winners:
            mentions = [
                (contest.message.guild.get_member(wid).mention if contest.message.guild.get_member(wid) else f"<@{wid}>")
                for wid in winners
            ]
            winners_text = "\n".join(f"🏆 {m}" for m in mentions)

            result_embed = discord.Embed(
                title="🏆 WYNIKI KONKURSU!",
                description=(
                    f"Gratulacje dla wygranych!\n\n"
                    f"🎁 **Wylosowana nagroda:**\n> {contest.prize}\n\n"
                    f"🎉 **Lista zwycięzców:**\n{winners_text}"
                ),
                color=COLOR_PRIMARY
            )
            await contest.message.channel.send(
                content="🎉 **Gratulacje dla zwycięzców! Skontaktujcie się z Administracją w tickecie.**",
                embed=result_embed
            )
        else:
            empty_embed = discord.Embed(
                title="🔴 KONKURS ZAKOŃCZONY",
                description=f"Niestety nikt nie dołączył do losowania.\n\n🎁 **Nagroda:** {contest.prize}",
                color=COLOR_RED
            )
            await contest.message.channel.send(embed=empty_embed)

    except (discord.NotFound, discord.HTTPException) as error:
        print(f"❌ Błąd kończenia konkursu: {error}")


class ContestModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Kreator Konkursu")

        self.prize = discord.ui.TextInput(
            label="Nagroda do wygrania",
            placeholder="Np. Ranga VIP na okres 30 dni",
            required=True,
            max_length=200
        )

        self.winners_count = discord.ui.TextInput(
            label="Liczba wygranych osób",
            placeholder="Np. 3",
            required=True,
            max_length=3
        )

        self.duration = discord.ui.TextInput(
            label="Czas trwania (w minutach)",
            placeholder="Np. 1440 (24h)",
            required=True,
            max_length=7
        )

        self.add_item(self.prize)
        self.add_item(self.winners_count)
        self.add_item(self.duration)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            winners_count = int(self.winners_count.value)
            duration_minutes = int(self.duration.value)
        except ValueError:
            await safe_response(interaction, "❌ Wprowadzone wartości muszą być liczbami całkowitymi.")
            return

        if winners_count < 1 or winners_count > 100:
            await safe_response(interaction, "❌ Liczba zwycięzców musi mieścić się w przedziale 1 - 100.")
            return

        if duration_minutes < 1 or duration_minutes > 43200:
            await safe_response(interaction, "❌ Czas trwania musi wynosić od 1 do 43200 minut.")
            return

        if interaction.guild is None:
            return

        channel = interaction.guild.get_channel(CONTEST_CHANNEL_ID)
        if channel is None:
            await safe_response(interaction, "❌ Kanał konkursowy nie został odnaleziony.")
            return

        contest = ContestData(
            prize=self.prize.value,
            winners_count=winners_count,
            duration_minutes=duration_minutes,
            creator_id=interaction.user.id
        )

        view = ContestView(contest)

        try:
            msg = await channel.send(
                embed=create_contest_embed(contest),
                view=view
            )
            contest.message = msg

            await safe_response(
                interaction,
                f"✅ Konkurs został pomyślnie utworzony: {msg.jump_url}"
            )
            asyncio.create_task(finish_contest_after_delay(contest, view))

        except discord.HTTPException as error:
            print(f"❌ Błąd tworzenia konkursu: {error}")
            await safe_response(interaction, "❌ Wystąpił błąd podczas publikowania konkursu.")


@bot.tree.command(name="konkurs", description="Tworzy i uruchamia nowe wydarzenie/konkurs.")
async def konkurs(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna wyłącznie na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko CEO ma uprawnienia do tworzenia konkursów.")
        return

    await interaction.response.send_modal(ContestModal())


# =========================================================
# REGULAMIN
# =========================================================

def create_rules_embed():
    embed = discord.Embed(
        title="📜 OFICJALNY REGULAMIN SERWERA — 666.6MC.PL",
        description=(
            "> Wejście na serwer oznacza automatyczną i bezwzględną akceptację poniższych zasad.\n"
            "> Nieznajomość regulaminu w żadnym wypadku nie zwalnia gracza z jego przestrzegania."
        ),
        color=COLOR_PRIMARY
    )
    if SERVER_ICON_URL and "http" in SERVER_ICON_URL:
        embed.set_thumbnail(url=SERVER_ICON_URL)
    return embed


@bot.tree.command(name="regulamin", description="Generuje i publikuje oficjalny regulamin.")
async def regulamin(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna tylko na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko ranga CEO może wysyłać regulamin.")
        return

    channel = interaction.guild.get_channel(RULES_CHANNEL_ID)
    if channel is None:
        await safe_response(interaction, "❌ Nie znaleziono kanału regulaminu.")
        return

    try:
        embed = create_rules_embed()

        embed.add_field(
            name="━━━ I. ZASADY OGÓLNE SPOŁECZNOŚCI ━━━",
            value=(
                "**1.** Szanuj każdego użytkownika oraz członka administracji.\n"
                "**2.** Całkowity zakaz toksyczności, prowokacji, gróźb oraz mowy nienawiści.\n"
                "**3.** Zakaz spamowania, floodowania oraz nadużywania wielkich liter (CAPS LOCK).\n"
                "**4.** Bezwzględny zakaz reklamowania innych serwerów Discord / Minecraft.\n"
                "**5.** Zakaz wysyłania treści NSFW, wulgarnych oraz niezgodnych z prawem.\n"
                "**6.** Stosuj się do zaleceń i poleceń wydawanych przez Administrację."
            ),
            inline=False
        )

        embed.add_field(
            name="━━━ II. ZASADY KORZYSTANIA Z DISCORDA ━━━",
            value=(
                "**1.** Wiadomości należy zamieszczać na kanałach do tego przeznaczonych.\n"
                "**2.** Zakaz oznaczania (@everyone, @here, administracja) bez uzasadnienia.\n"
                "**3.** Zakaz wykorzystywania botów exploitujących, crashujących i self-botów.\n"
                "**4.** Zakaz podszywania się pod graczy, administrację lub znane osoby.\n"
                "**5.** Dbaj o kulturę wypowiedzi na czatach tekstowych oraz głosowych."
            ),
            inline=False
        )

        embed.add_field(
            name="━━━ III. ZASADY SERWERA MINECRAFT ━━━",
            value=(
                "**1.** Całkowity zakaz używania oprogramowania ułatwiającego grę (cheaty, boty).\n"
                "**2.** Zakaz niszczenia cudzych budowli (griefing) w strefach chronionych.\n"
                "**3.** Zakaz kradzieży mienia innych graczy i oszustw przy wymianach.\n"
                "**4.** Zakaz celowego przeciążania serwera (maszyny lagujące, exploity).\n"
                "**5.** Walka PvP dozwolona jest tylko w wyznaczonych strefach i arenach.\n"
                "**6.** Zakaz gry na wielu kontach (multikonta) w celu ominięcia blokad."
            ),
            inline=False
        )

        embed.add_field(
            name="━━━ IV. TARYFIKATOR KAR ━━━",
            value=(
                "🟡 **Ostrzeżenie (Warn)** — Wpis do kartoteki gracza\n"
                "🔇 **Wyciszenie (Mute/Timeout)** — Czasowa blokada czatu\n"
                "👢 **Wyrzucenie (Kick)** — Natychmiastowe wyrzucenie z serwera\n"
                "⏳ **Ban Czasowy (TempBan)** — Okresowa blokada dostępu\n"
                "🔴 **Ban Permanentny (PermBan)** — Trwałe wykluczenie ze społeczności"
            ),
            inline=False
        )

        embed.set_footer(text="666.6MC • Życzymy udanej i bezpiecznej rozgrywki!")

        await channel.send(embed=embed)
        await safe_response(interaction, "✅ Regulamin został pomyślnie wysłany na kanał.")

    except discord.HTTPException as error:
        print(f"❌ Błąd wysyłania regulaminu: {error}")
        await safe_response(interaction, "❌ Wystąpił błąd podczas wysyłania regulaminu.")


# =========================================================
# CHANGELOG
# =========================================================

class ChangelogModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Nowy wpis w Changelogu")

        self.change_description = discord.ui.TextInput(
            label="Co zostało zmienione / naprawione?",
            placeholder="Wypisz zmiany serwerowe w podpunktach...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )

        self.add_item(self.change_description)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(CHANGELOG_CHANNEL_ID)

        if channel is None:
            await safe_response(interaction, "❌ Kanał changelogu nie został znaleziony.")
            return

        now = datetime.now()
        timestamp = int(now.timestamp())

        embed = discord.Embed(
            title="🚀 AKTUALIZACJA SERWERA — 666.6MC",
            description=f"### 📋 Lista wprowadzonych zmian:\n\n{self.change_description.value}",
            color=COLOR_PRIMARY,
            timestamp=now
        )

        embed.set_author(
            name=f"Wdrożone przez {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="📅 Data wdrożenia",
            value=f"<t:{timestamp}:F> (<t:{timestamp}:R>)",
            inline=True
        )

        embed.add_field(
            name="👤 Odpowiedzialny",
            value=interaction.user.mention,
            inline=True
        )

        embed.set_footer(text="666.6MC • Oficjalny dziennik zmian")

        try:
            await channel.send(embed=embed)
            await safe_response(interaction, "✅ Changelog został opublikowany!")
        except discord.HTTPException as error:
            print(f"❌ Błąd publikowania changelogu: {error}")
            await safe_response(interaction, "❌ Błąd publikacji wpisu.")


@bot.tree.command(name="changelog", description="Publikuje nowy wpis o aktualizacji serwera.")
async def changelog(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna wyłącznie na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko ranga CEO może dodawać wpisy do changelogu.")
        return

    await interaction.response.send_modal(ChangelogModal())


# =========================================================
# PLUS / MINUS
# =========================================================

class PlusMinusModal(discord.ui.Modal):

    def __init__(self, action_type):
        self.action_type = action_type
        emoji = "➕" if action_type == "plus" else "➖"
        title = "PLUS" if action_type == "plus" else "MINUS"

        super().__init__(title=f"{emoji} Przyznaj {title}")

        self.target = discord.ui.TextInput(
            label="Dla kogo?",
            placeholder="Wpisz nick lub oznacz użytkownika...",
            required=True,
            max_length=100
        )

        self.reason = discord.ui.TextInput(
            label="Powód przyznania punktu",
            placeholder="Podaj szczegółowe uzasadnienie...",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )

        self.add_item(self.target)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.channel is None:
            await safe_response(interaction, "❌ Nie znaleziono kanału.")
            return

        is_plus = self.action_type == "plus"
        emoji = "➕" if is_plus else "➖"
        title = "PUNKT DODATNI (PLUS)" if is_plus else "PUNKT UJEMNY (MINUS)"

        embed = discord.Embed(
            title=f"{emoji} {title}",
            color=COLOR_PRIMARY if is_plus else COLOR_RED,
            timestamp=datetime.now()
        )

        embed.add_field(name="👤 Otrzymujący", value=self.target.value, inline=True)
        embed.add_field(name="🛡️ Wystawiający", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Uzasadnienie", value=f"```text\n{self.reason.value}\n```", inline=False)
        embed.set_footer(text="666.6MC • System oceny kadry administracyjnej")

        try:
            await interaction.channel.send(embed=embed)
            await safe_response(
                interaction,
                f"✅ Zapisano wpis na kanale {interaction.channel.mention}."
            )
        except discord.HTTPException as error:
            print(f"❌ Błąd wysyłania plus/minus: {error}")
            await safe_response(interaction, "❌ Błąd dodawania wpisu.")


async def open_plus_minus_modal(interaction, action_type):
    if interaction.guild is None:
        await safe_response(interaction, "❌ Komenda dostępna wyłącznie na serwerze.")
        return

    ceo_role = interaction.guild.get_role(CEO_ROLE_ID)
    if ceo_role is None or ceo_role not in interaction.user.roles:
        await safe_response(interaction, "❌ Tylko ranga CEO posiada dostęp do tej funkcji.")
        return

    await interaction.response.send_modal(PlusMinusModal(action_type))


@bot.tree.command(name="plus", description="Przyznaje plusa członkowi administracji.")
async def plus(interaction: discord.Interaction):
    await open_plus_minus_modal(interaction, "plus")


@bot.tree.command(name="minus", description="Przyznaje minusa członkowi administracji.")
async def minus(interaction: discord.Interaction):
    await open_plus_minus_modal(interaction, "minus")


# =========================================================
# PROPOZYCJE (STYL ZONEMC Z DYSKUSJĄ W WĄTKU)[cite: 1]
# =========================================================

class ProposalModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Nowa propozycja serwerowa")

        self.suggestion = discord.ui.TextInput(
            label="Treść Twojej propozycji",
            placeholder="Opisz dokładnie swój pomysł lub usprawnienie serwera...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1500
        )
        self.add_item(self.suggestion)

    async def on_submit(self, interaction: discord.Interaction):
        content = self.suggestion.value.strip()
        channel = interaction.channel

        now = datetime.now()
        embed = discord.Embed(
            description=f"```text\n{content}\n```",
            color=COLOR_BLUE
        )
        embed.set_author(
            name=f"Propozycja od: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        embed.set_footer(
            text=f"666.6MC.PL • Dzisiaj o {now.strftime('%H:%M')}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )

        msg = await channel.send(
            embed=embed,
            view=ProposalButtonView(),
            allowed_mentions=discord.AllowedMentions.none()
        )
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        try:
            thread = await msg.create_thread(
                name="Dyskusja o propozycji",
                auto_archive_duration=1440
            )
            await thread.send(
                f"💬 Tutaj możecie swobodnie dyskutować na temat propozycji gracza {interaction.user.mention}!"
            )
        except discord.HTTPException:
            pass

        await safe_response(interaction, "✅ Twoja propozycja została pomyślnie zgłoszona!")


class ProposalButtonView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Napisz propozycję!",
        emoji="💡",
        style=discord.ButtonStyle.secondary,
        custom_id="create_proposal_btn"
    )
    async def create_proposal(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(ProposalModal())


# =========================================================
# ON_MESSAGE (FILTRY + PROPOZYCJE + URLOPY)
# =========================================================

@bot.event
async def on_message(
    message: discord.Message
):
    if message.author.bot:
        return

    has_bypass_role = False

    if isinstance(
        message.author,
        discord.Member
    ):
        has_bypass_role = any(
            role.id in LINK_FILTER_BYPASS_ROLE_IDS
            for role in message.author.roles
        )

    # =====================================================
    # @EVERYONE / @HERE
    # =====================================================

    if (
        isinstance(message.author, discord.Member)
        and not has_bypass_role
        and (
            message.mention_everyone
            or "@everyone" in (message.content or "").lower()
            or "@here" in (message.content or "").lower()
        )
    ):
        await punish_everyone_violation(message)
        return

    # =====================================================
    # PROPOZYCJE (STYL ZONEMC Z PRZYCISKIEM I WĄTKIEM)[cite: 1]
    # =====================================================

    if message.channel.id == PROPOSAL_CHANNEL_ID:
        content = message.content.strip()

        if not content:
            await bot.process_commands(message)
            return

        try:
            await message.delete()

            now = datetime.now()
            # Styl z ramką i autorem zoptymalizowany jak w ZONEMC[cite: 1]
            embed = discord.Embed(
                description=f"```text\n{content}\n```",
                color=COLOR_BLUE
            )
            embed.set_author(
                name=f"Propozycja od: {message.author.display_name}",
                icon_url=message.author.display_avatar.url
            )
            embed.set_footer(
                text=f"666.6MC.PL • Dzisiaj o {now.strftime('%H:%M')}",
                icon_url=message.guild.icon.url if message.guild.icon else None
            )

            proposal_message = await message.channel.send(
                embed=embed,
                view=ProposalButtonView(),
                allowed_mentions=discord.AllowedMentions.none()
            )

            await proposal_message.add_reaction("✅")
            await proposal_message.add_reaction("❌")

            # Tworzenie dedykowanego wątku dyskusyjnego pod propozycją[cite: 1]
            try:
                thread = await proposal_message.create_thread(
                    name="Dyskusja o propozycji",
                    auto_archive_duration=1440
                )
                await thread.send(
                    f"💬 Tutaj możecie swobodnie dyskutować na temat propozycji gracza {message.author.mention}!"
                )
            except discord.HTTPException:
                pass

        except discord.HTTPException as error:
            print(f"❌ Błąd propozycji: {error}")

        return

    # =====================================================
    # URLOPY
    # =====================================================

    if message.channel.id == URLopy_CHANNEL_ID:
        content = message.content.strip()

        if not content:
            await bot.process_commands(message)
            return

        try:
            await message.delete()

            now = datetime.now()
            timestamp = int(now.timestamp())

            embed = discord.Embed(
                title="🏖️ ZGŁOSZENIE URLOPU",
                description=f"```text\n{content}\n```",
                color=discord.Color.from_rgb(52, 152, 219),
                timestamp=now
            )

            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )

            embed.add_field(
                name="👤 Zgłaszający",
                value=message.author.mention,
                inline=True
            )

            embed.add_field(
                name="📅 Data zgłoszenia",
                value=f"<t:{timestamp}:F>",
                inline=True
            )

            embed.set_footer(
                text="666.6MC • System urlopów kadry"
            )

            await message.channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none()
            )

        except discord.HTTPException as error:
            print(f"❌ Błąd systemu urlopów: {error}")

        return

    # =====================================================
    # LINKI / GIF
    # =====================================================

    if not has_bypass_role:
        content = message.content or ""

        has_link = (
            BLOCK_LINKS
            and LINK_PATTERN.search(content) is not None
        )

        has_gif = (
            BLOCK_GIFS
            and GIF_PATTERN.search(content) is not None
        )

        attachment_is_gif = False

        if BLOCK_GIFS:
            for attachment in message.attachments:
                if attachment.filename.lower().endswith(".gif"):
                    attachment_is_gif = True
                    break

        if (
            has_link
            or has_gif
            or attachment_is_gif
        ):
            await punish_link_violation(
                message,
                is_gif=(has_gif or attachment_is_gif)
            )
            return

    await bot.process_commands(message)


# =========================================================
# POWITANIE
# =========================================================

@bot.event
async def on_member_join(
    member: discord.Member
):
    if LOBBY_CHANNEL_ID == 0:
        return

    channel = bot.get_channel(LOBBY_CHANNEL_ID)
    if channel is None:
        return

    member_count = member.guild.member_count

    embed = discord.Embed(
        title="Nowy użytkownik na serwerze!",
        description=(
            f"Witaj serdecznie, {member.mention}! Miło Cię widzieć na **666.6MC**! 💚\n\n"
            f"> Jesteś naszym **{member_count}.** graczem na serwerze!\n"
            "> Koniecznie odbierz rolę weryfikacji i zapoznaj się z zasadami."
        ),
        color=COLOR_PRIMARY,
        timestamp=datetime.now()
    )

    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="666.6MC • Witamy w naszej społeczności!")

    try:
        await channel.send(embed=embed)
    except discord.HTTPException as error:
        print(f"❌ Błąd powitania: {error}")


# =========================================================
# READY & INICJALIZACJA PANELI
# =========================================================

@bot.event
async def on_ready():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ Zalogowano pomyślnie jako: {bot.user} (ID: {bot.user.id})")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Rejestracja Persistent Views
    try:
        bot.add_view(VerificationView())
        bot.add_view(TicketPanelView())
        bot.add_view(CloseTicketView())
        bot.add_view(MediaView())
        bot.add_view(RecruitmentView())
        bot.add_view(ProposalButtonView())
        print("✅ Zarejestrowano wszystkie persistent views.")
    except Exception as error:
        print(f"❌ Błąd rejestracji views: {error}")

    # Synchronizacja komend Slash
    try:
        synced = await bot.tree.sync()
        print(f"✅ Zsynchronizowano {len(synced)} komend slash.")
    except Exception as error:
        print(f"❌ Błąd synchronizacji komend: {error}")

    # Sprawdzenie panelu weryfikacji
    try:
        channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
        if channel:
            exists = False
            async for message in channel.history(limit=50):
                if (
                    message.author == bot.user
                    and message.embeds
                    and "Weryfikacja" in (message.embeds[0].title or "")
                ):
                    exists = True
                    break

            if not exists:
                await channel.send(
                    embed=create_verification_embed(),
                    view=VerificationView()
                )
                print("✅ Panel weryfikacji został wysłany.")
            else:
                print("✅ Panel weryfikacji już istnieje.")
    except discord.HTTPException as error:
        print(f"❌ Błąd panelu weryfikacji: {error}")

    # Sprawdzenie panelu ticketów (TokyoCode layout)[cite: 2]
    try:
        channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
        if channel:
            panel_exists = False
            async for message in channel.history(limit=50):
                if (
                    message.author == bot.user
                    and message.embeds
                    and "Centrum zgłoszeń" in (message.embeds[0].title or "")
                ):
                    panel_exists = True
                    break

            if not panel_exists:
                await channel.send(
                    embed=create_ticket_embed(),
                    view=TicketPanelView()
                )
                print("✅ Nowy panel ticketów został wysłany.")
            else:
                print("✅ Panel ticketów już istnieje.")
    except discord.HTTPException as error:
        print(f"❌ Błąd panelu ticketów: {error}")

    # Sprawdzenie panelu rekrutacji
    try:
        if bot.guilds:
            for guild in bot.guilds:
                await update_recruitment_panel(guild)
    except Exception as error:
        print(f"❌ Błąd panelu rekrutacji: {error}")


# =========================================================
# START BOTA
# =========================================================

if not TOKEN:
    raise RuntimeError("❌ Brak zdefiniowanej zmiennej środowiskowej DISCORD_TOKEN.")

bot.run(TOKEN)
