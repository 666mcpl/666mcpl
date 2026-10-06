import os
import asyncio
import random
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands


# =========================================================
# KONFIGURACJA
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
        "emoji": "🆘"
    },
    "rekrutacja": {
        "name": "Rekrutacja",
        "emoji": "📋"
    },
    "media": {
        "name": "Media",
        "emoji": "🎥"
    },
    "blad": {
        "name": "Błąd",
        "emoji": "🐛"
    },
    "platnosc": {
        "name": "Płatność",
        "emoji": "💳"
    },
    "inne": {
        "name": "Inne",
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

    # Logowanie prób wysłania GIF-a na kanał LOGI.
    if is_gif:
        try:
            log_channel = message.guild.get_channel(LOGI_CHANNEL_ID)

            if log_channel is not None:
                log_embed = discord.Embed(
                    title="🚫 Próba wysłania GIF-a",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                log_embed.add_field(
                    name="👤 Użytkownik",
                    value=f"{message.author.mention} (`{message.author}` / `{message.author.id}`)",
                    inline=False
                )
                log_embed.add_field(
                    name="📍 Kanał",
                    value=f"{message.channel.mention} (`{message.channel.id}`)",
                    inline=True
                )

                sent_content = (message.content or "").strip()
                gif_urls = []

                for attachment in message.attachments:
                    if attachment.filename.lower().endswith(".gif"):
                        gif_urls.append(attachment.url)

                if sent_content:
                    what_was_sent = sent_content[:1000]
                elif gif_urls:
                    what_was_sent = "\n".join(gif_urls)[:1000]
                else:
                    what_was_sent = "GIF wysłany jako załącznik"

                log_embed.add_field(
                    name="🔗 Co wysłano",
                    value=what_was_sent,
                    inline=False
                )

                if gif_urls:
                    log_embed.add_field(
                        name="🖼️ Link do GIF-a",
                        value="\n".join(gif_urls)[:1000],
                        inline=False
                    )

                log_embed.add_field(
                    name="🕐 Data",
                    value=f"<t:{int(datetime.now().timestamp())}:F>",
                    inline=True
                )
                log_embed.set_footer(text="666.6MC • Logi filtra GIF")

                await log_channel.send(
                    embed=log_embed,
                    allowed_mentions=discord.AllowedMentions.none()
                )

        except discord.HTTPException as error:
            print(f"❌ Błąd wysyłania logu GIF: {error}")

    try:
        await message.channel.send(
            f"⚠️ {message.author.mention}, "
            "linki/GIF-y są tutaj niedozwolone.",
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
            title=f"🎫 Ticket — {ticket_name}"
        )

        self.minecraft_nick = discord.ui.TextInput(
            label="Nick z Minecrafta",
            placeholder="Wpisz swój nick z gry",
            required=True,
            max_length=32
        )

        # Formularz Płatność ma osobne pola:
        # co kupuje, za ile oraz metoda płatności.
        if ticket_type == "platnosc":

            self.product = discord.ui.TextInput(
                label="Co chcesz kupić?",
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
                placeholder="Np. PayPal, BLIK, przelew...",
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

        if category is None:
            await safe_response(
                interaction,
                "❌ Nie znaleziono kategorii ticketów."
            )
            return

        if not isinstance(
            category,
            discord.CategoryChannel
        ):
            await safe_response(
                interaction,
                "❌ Podane ID nie wskazuje na kategorię Discord."
            )
            return

        existing_ticket = find_existing_ticket(
            guild,
            user.id
        )

        if existing_ticket is not None:
            await safe_response(
                interaction,
                "⚠️ **Masz już otwarty ticket!**\n\n"
                f"Twój obecny ticket: {existing_ticket.mention}\n\n"
                "Musisz go najpierw zamknąć."
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

            staff_roles = [
                CEO_ROLE_ID
            ]

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
                "❌ Bot nie może utworzyć ticketu. "
                "Sprawdź **Manage Channels**."
            )
            return

        except discord.HTTPException as error:

            print(
                f"❌ Błąd tworzenia ticketu: {error}"
            )

            await safe_response(
                interaction,
                "❌ Discord zwrócił błąd podczas tworzenia ticketu."
            )
            return

        embed = discord.Embed(
            title=(
                f"{ticket_info['emoji']} "
                f"Ticket — {ticket_info['name']}"
            ),
            description=(
                "Dziękujemy za zgłoszenie! 💚\n\n"
                "Administracja odpowie tutaj na Twoją wiadomość."
            ),
            color=discord.Color.from_rgb(
                46,
                204,
                113
            )
        )

        embed.add_field(
            name="👤 Użytkownik",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="🎮 Nick z gry",
            value=f"`{self.minecraft_nick.value}`",
            inline=False
        )

        if self.ticket_type == "platnosc":

            embed.add_field(
                name="🛒 Co chce kupić?",
                value=self.product.value,
                inline=False
            )

            embed.add_field(
                name="💰 Za ile?",
                value=self.price.value,
                inline=True
            )

            embed.add_field(
                name="💳 Metoda płatności",
                value=self.payment_method.value,
                inline=True
            )

            if self.description.value:
                embed.add_field(
                    name="📝 Dodatkowe informacje",
                    value=self.description.value,
                    inline=False
                )

        else:

            embed.add_field(
                name="📝 Opis sprawy",
                value=self.description.value,
                inline=False
            )

        embed.set_footer(
            text="666.6MC • System ticketów"
        )

        try:

            await channel.send(
                content=user.mention,
                embed=embed,
                view=CloseTicketView()
            )

            await safe_response(
                interaction,
                f"✅ Ticket został utworzony: {channel.mention}"
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd wysyłania panelu ticketu: {error}"
            )

            await safe_response(
                interaction,
                f"✅ Ticket utworzony: {channel.mention}"
            )


# =========================================================
# ZAMYKANIE TICKETU
# =========================================================

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(
            timeout=None
        )

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

                    owner_id = part[
                        len("ticket_owner:"):
                    ]

                elif part.startswith("ticket_type:"):

                    ticket_type = part[
                        len("ticket_type:"):
                    ]

        is_owner = owner_id == str(user.id)

        is_staff = False

        if ticket_type:
            is_staff = can_access_ticket(
                user,
                ticket_type
            )

        if not (is_owner or is_staff):

            await safe_response(
                interaction,
                "❌ Nie masz uprawnień do zamknięcia tego ticketu."
            )
            return

        await safe_response(
            interaction,
            "🔒 **Ticket zostanie zamknięty za 3 sekundy.**",
            ephemeral=False
        )

        await asyncio.sleep(3)

        try:

            await channel.delete(
                reason=f"Ticket zamknięty przez {user}"
            )

        except discord.NotFound:
            pass

        except discord.Forbidden:
            print(
                "❌ Bot nie ma uprawnień do usunięcia ticketu."
            )

        except discord.HTTPException as error:
            print(
                f"❌ Błąd usuwania ticketu: {error}"
            )


# =========================================================
# PANEL TICKETÓW
# =========================================================

class TicketSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="Pomoc",
                description="Potrzebujesz pomocy?",
                emoji="🆘",
                value="pomoc"
            ),

            discord.SelectOption(
                label="Rekrutacja",
                description="Sprawa związana z rekrutacją",
                emoji="📋",
                value="rekrutacja"
            ),

            discord.SelectOption(
                label="Media",
                description="Sprawy związane z mediami",
                emoji="🎥",
                value="media"
            ),

            discord.SelectOption(
                label="Błąd",
                description="Znalazłeś błąd na serwerze",
                emoji="🐛",
                value="blad"
            ),

            discord.SelectOption(
                label="Płatność",
                description="Sprawa związana z płatnością",
                emoji="💳",
                value="platnosc"
            ),

            discord.SelectOption(
                label="Inne",
                description="Inne zgłoszenie",
                emoji="💡",
                value="inne"
            )
        ]

        super().__init__(
            placeholder="🎫 Wybierz kategorię ticketu...",
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

            modal = TicketModal(
                ticket_type
            )

            await interaction.response.send_modal(
                modal
            )

        except Exception as error:

            import traceback

            print(
                f"❌ BŁĄD OTWIERANIA MODALA "
                f"'{ticket_type}': {error!r}"
            )

            traceback.print_exc()

            await safe_response(
                interaction,
                "❌ Nie udało się otworzyć formularza."
            )


class TicketPanelView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            TicketSelect()
        )


def create_ticket_embed():

    return discord.Embed(
        title="🎫 CENTRUM TICKETÓW 666.6MC",
        description=(
            "Potrzebujesz pomocy? 💚\n\n"
            "Wybierz odpowiednią kategorię z menu poniżej.\n\n"
            "🆘 **Pomoc** — pomoc z serwerem\n"
            "📋 **Rekrutacja** — sprawy rekrutacyjne\n"
            "🎥 **Media** — współpraca/media\n"
            "🐛 **Błąd** — zgłoszenie błędu\n"
            "💳 **Płatność** — płatności\n"
            "💡 **Inne** — pozostałe sprawy"
        ),
        color=discord.Color.from_rgb(
            46,
            204,
            113
        )
    )


# =========================================================
# REKRUTACJA
# =========================================================

def create_recruitment_embed():

    if RECRUITMENT_OPEN:

        return discord.Embed(
            title="📋 REKRUTACJA — 666.6MC",
            description=(
                "Chcesz dołączyć do naszej administracji?\n\n"
                "Jeżeli uważasz, że nadajesz się do ekipy, "
                "kliknij przycisk **📝 ZŁÓŻ REKRUTACJĘ** "
                "i wypełnij formularz.\n\n"

                "**📌 Pamiętaj:**\n"
                "• Podawaj prawdziwe informacje.\n"
                "• Nie składaj kilku rekrutacji jednocześnie.\n"
                "• Odpowiadaj na pytania dokładnie.\n"
                "• Wysłanie rekrutacji nie gwarantuje przyjęcia.\n\n"

                "🟢 **REKRUTACJA JEST OTWARTA**\n\n"
                "Powodzenia! 💚"
            ),
            color=discord.Color.from_rgb(
                46,
                204,
                113
            )
        )

    return discord.Embed(
        title="📋 REKRUTACJA — 666.6MC",
        description=(
            "Aktualnie **rekrutacja jest zamknięta**.\n\n"
            "Spróbuj ponownie później."
        ),
        color=discord.Color.red()
    )


class RecruitmentModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="📋 Rekrutacja — 666.6MC"
        )

        self.minecraft_nick = discord.ui.TextInput(
            label="Nick z Minecrafta",
            placeholder="Wpisz swój nick",
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
            placeholder="Opisz swoje doświadczenie w administracji",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.availability = discord.ui.TextInput(
            label="Dyspozycyjność",
            placeholder="Ile czasu możesz poświęcać na serwer?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.reason = discord.ui.TextInput(
            label="Dlaczego Ty?",
            placeholder="Dlaczego chcesz dołączyć do administracji?",
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
                "🔴 Rekrutacja jest obecnie zamknięta."
            )

            return

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

        if category is None:

            await safe_response(
                interaction,
                "❌ Nie znaleziono kategorii ticketów."
            )

            return

        if not isinstance(
            category,
            discord.CategoryChannel
        ):

            await safe_response(
                interaction,
                "❌ ID kategorii ticketów jest nieprawidłowe."
            )

            return

        existing_ticket = find_existing_ticket(
            guild,
            user.id
        )

        if existing_ticket is not None:

            await safe_response(
                interaction,
                "⚠️ **Masz już otwarte zgłoszenie!**\n\n"
                f"{existing_ticket.mention}"
            )

            return

        safe_username = re.sub(
            r"[^a-zA-Z0-9\-_]",
            "",
            user.name.lower()
        )

        if not safe_username:
            safe_username = str(user.id)

        channel_name = (
            f"rekrutacja-{safe_username}"
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

            role = guild.get_role(
                role_id
            )

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
                    "|ticket_type:rekrutacja"
                ),
                reason=f"Rekrutacja utworzona przez {user}"
            )

        except discord.Forbidden:

            await safe_response(
                interaction,
                "❌ Bot nie może utworzyć rekrutacji. "
                "Sprawdź uprawnienie **Manage Channels**."
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Błąd tworzenia rekrutacji: {error}"
            )

            await safe_response(
                interaction,
                "❌ Wystąpił błąd podczas tworzenia rekrutacji."
            )

            return

        embed = discord.Embed(
            title="📋 NOWA REKRUTACJA — 666.6MC",
            description=(
                "Nowa osoba złożyła rekrutację.\n\n"
                "Administracja może zapoznać się z odpowiedziami."
            ),
            color=discord.Color.from_rgb(
                46,
                204,
                113
            )
        )

        embed.add_field(
            name="👤 Użytkownik",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="🎮 Nick Minecraft",
            value=f"`{self.minecraft_nick.value}`",
            inline=False
        )

        embed.add_field(
            name="🎂 Wiek",
            value=f"`{self.age.value}`",
            inline=False
        )

        embed.add_field(
            name="🛡️ Doświadczenie",
            value=self.experience.value,
            inline=False
        )

        embed.add_field(
            name="⏰ Dyspozycyjność",
            value=self.availability.value,
            inline=False
        )

        embed.add_field(
            name="💬 Dlaczego chcesz dołączyć?",
            value=self.reason.value,
            inline=False
        )

        embed.set_footer(
            text="666.6MC • System rekrutacji"
        )

        try:

            await channel.send(
                content=user.mention,
                embed=embed,
                view=CloseTicketView()
            )

            await safe_response(
                interaction,
                "✅ Rekrutacja została wysłana!\n"
                f"Twoje zgłoszenie: {channel.mention}"
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd wysyłania rekrutacji: {error}"
            )

            await safe_response(
                interaction,
                f"✅ Rekrutacja została utworzona: "
                f"{channel.mention}"
            )


class RecruitmentView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

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

            await safe_response(
                interaction,
                "🔴 Rekrutacja jest obecnie zamknięta."
            )

            return

        await interaction.response.send_modal(
            RecruitmentModal()
        )


async def update_recruitment_panel(
    guild: discord.Guild
):

    channel = guild.get_channel(
        RECRUITMENT_CHANNEL_ID
    )

    if channel is None:

        print(
            f"❌ Nie znaleziono kanału rekrutacji "
            f"{RECRUITMENT_CHANNEL_ID}"
        )

        return False

    try:

        async for message in channel.history(
            limit=50
        ):

            if (
                message.author == bot.user
                and message.embeds
                and message.embeds[0].title
                == "📋 REKRUTACJA — 666.6MC"
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

    except discord.Forbidden:

        print(
            "❌ Bot nie ma uprawnień do kanału rekrutacji."
        )

    except discord.HTTPException as error:

        print(
            f"❌ Błąd panelu rekrutacji: {error}"
        )

    return False


@bot.tree.command(
    name="startrekrutacja",
    description="Otwiera rekrutację."
)
async def startrekrutacja(
    interaction: discord.Interaction
):

    global RECRUITMENT_OPEN

    if interaction.guild is None:
        await safe_response(
            interaction,
            "❌ Komenda dostępna tylko na serwerze."
        )
        return

    ceo_role = interaction.guild.get_role(
        CEO_ROLE_ID
    )

    if ceo_role is None:

        await safe_response(
            interaction,
            "❌ Nie znaleziono roli CEO."
        )

        return

    if ceo_role not in interaction.user.roles:

        await safe_response(
            interaction,
            "❌ Tylko CEO może otworzyć rekrutację."
        )

        return

    RECRUITMENT_OPEN = True

    success = await update_recruitment_panel(
        interaction.guild
    )

    if success:

        await safe_response(
            interaction,
            "🟢 **Rekrutacja została otwarta!**"
        )

    else:

        await safe_response(
            interaction,
            "⚠️ Rekrutacja została włączona, "
            "ale nie udało się zaktualizować panelu."
        )


@bot.tree.command(
    name="stoprekrutacja",
    description="Zamyka rekrutację."
)
async def stoprekrutacja(
    interaction: discord.Interaction
):

    global RECRUITMENT_OPEN

    if interaction.guild is None:
        await safe_response(
            interaction,
            "❌ Komenda dostępna tylko na serwerze."
        )
        return

    ceo_role = interaction.guild.get_role(
        CEO_ROLE_ID
    )

    if ceo_role is None:

        await safe_response(
            interaction,
            "❌ Nie znaleziono roli CEO."
        )

        return

    if ceo_role not in interaction.user.roles:

        await safe_response(
            interaction,
            "❌ Tylko CEO może zamknąć rekrutację."
        )

        return

    RECRUITMENT_OPEN = False

    success = await update_recruitment_panel(
        interaction.guild
    )

    if success:

        await safe_response(
            interaction,
            "🔴 **Rekrutacja została zamknięta!**"
        )

    else:

        await safe_response(
            interaction,
            "⚠️ Rekrutacja została wyłączona, "
            "ale nie udało się zaktualizować panelu."
        )


# =========================================================
# MEDIA
# =========================================================

class MediaView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

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

        await interaction.response.send_modal(
            MediaModal()
        )


class MediaModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="🎥 Wniosek MEDIA"
        )

        self.minecraft_nick = discord.ui.TextInput(
            label="Nick z Minecrafta",
            placeholder="Wpisz swój nick z gry",
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
            placeholder="Np. 125",
            required=True,
            max_length=20
        )

        self.videos = discord.ui.TextInput(
            label="Linki do filmów z 666.6MC",
            placeholder="Wklej linki do minimum 5 filmów",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1500
        )

        self.description = discord.ui.TextInput(
            label="Dodatkowe informacje",
            placeholder="Napisz coś dodatkowego...",
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
            await safe_response(
                interaction,
                "❌ Nie znaleziono serwera."
            )
            return

        category = guild.get_channel(
            TICKET_CATEGORY_ID
        )

        if category is None or not isinstance(
            category,
            discord.CategoryChannel
        ):

            await safe_response(
                interaction,
                "❌ Nie znaleziono kategorii ticketów."
            )
            return

        existing = find_existing_ticket(
            guild,
            user.id
        )

        if existing:

            await safe_response(
                interaction,
                f"⚠️ Masz już otwarty ticket: {existing.mention}"
            )
            return

        safe_username = re.sub(
            r"[^a-zA-Z0-9\-_]",
            "",
            user.name.lower()
        )

        if not safe_username:
            safe_username = str(user.id)

        channel_name = (
            f"media-{safe_username}"
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

        staff_roles = [
            MODERATOR_ROLE_ID,
            ADMIN_ROLE_ID,
            TECHNIK_ROLE_ID,
            DEVELOPER_ROLE_ID,
            HEAD_ADMIN_ROLE_ID,
            CEO_ROLE_ID
        ]

        for role_id in staff_roles:

            role = guild.get_role(
                role_id
            )

            if role:

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
                    "|ticket_type:media"
                ),
                reason=f"Wniosek MEDIA utworzony przez {user}"
            )

        except discord.Forbidden:

            await safe_response(
                interaction,
                "❌ Bot nie może utworzyć ticketu MEDIA."
            )
            return

        except discord.HTTPException as error:

            print(
                f"❌ Błąd tworzenia ticketu MEDIA: {error}"
            )

            await safe_response(
                interaction,
                "❌ Wystąpił błąd podczas tworzenia ticketu MEDIA."
            )
            return

        embed = discord.Embed(
            title="🎥 WNIOSEK MEDIA — 666.6MC",
            description=(
                "Nowe zgłoszenie o rangę **MEDIA**."
            ),
            color=discord.Color.from_rgb(
                46,
                204,
                113
            )
        )

        embed.add_field(
            name="👤 Użytkownik",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="🎮 Nick z Minecrafta",
            value=f"`{self.minecraft_nick.value}`",
            inline=False
        )

        embed.add_field(
            name="🔗 Kanał / profil",
            value=self.platform.value,
            inline=False
        )

        embed.add_field(
            name="📊 Subskrypcje / obserwacje",
            value=self.followers.value,
            inline=False
        )

        embed.add_field(
            name="🎬 Filmy z 666.6MC",
            value=self.videos.value,
            inline=False
        )

        if self.description.value:

            embed.add_field(
                name="📝 Dodatkowe informacje",
                value=self.description.value,
                inline=False
            )

        embed.set_footer(
            text="666.6MC • System Media"
        )

        try:

            await channel.send(
                content=user.mention,
                embed=embed,
                view=CloseTicketView()
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd wysyłania Media: {error}"
            )

        await safe_response(
            interaction,
            f"✅ Wniosek MEDIA został utworzony: {channel.mention}"
        )


def create_media_embed():

    return discord.Embed(
        title="WSPÓŁPRACA ORAZ RANGA MEDIA — 666.6MC.PL",
        description=(
            "Chcesz otrzymać rangę **MEDIA** na naszym serwerze?\n\n"
            "**📋 Wymagania:**\n"
            "• Minimum **25 subskrypcji na YouTube** "
            "LUB **50 obserwacji na TikToku**\n"
            "• Minimum **5 opublikowanych filmów / shorts / "
            "tiktoków** z serwera **666.6mc.pl**\n\n"
            "Spełniasz wymagania? Kliknij przycisk poniżej "
            "i złóż zgłoszenie!"
        ),
        color=discord.Color.from_rgb(
            46,
            204,
            113
        )
    )


# =========================================================
# WERYFIKACJA
# =========================================================

def create_verification_embed():

    return discord.Embed(
        title="💚 WERYFIKACJA 666.6MC",
        description=(
            "Kliknij przycisk poniżej, aby się zweryfikować."
        ),
        color=discord.Color.from_rgb(
            46,
            204,
            113
        )
    )


class VerificationView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Zweryfikuj się",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="verification_button"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "✅ Weryfikacja została wykonana.",
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

        self.end_time = (
            datetime.now()
            + timedelta(minutes=duration_minutes)
        )

        self.finished = False


def create_poll_embed(poll):

    votes_one = len(poll.votes_one)
    votes_two = len(poll.votes_two)

    total_votes = votes_one + votes_two

    if total_votes > 0:

        percentage_one = (
            votes_one / total_votes
        ) * 100

        percentage_two = (
            votes_two / total_votes
        ) * 100

    else:

        percentage_one = 0
        percentage_two = 0

    end_timestamp = int(
        poll.end_time.timestamp()
    )

    if poll.finished:

        status = "🔴 **ANKIETA ZAKOŃCZONA**"

    else:

        status = (
            "🟢 **ANKIETA TRWA**\n"
            f"⏰ Kończy się: <t:{end_timestamp}:R>"
        )

    embed = discord.Embed(
        title=f"📊 {poll.question}",
        description=(
            f"{status}\n\n"
            "Wybierz jedną z dwóch odpowiedzi.\n\n"
            f"🟢 **{poll.option_one}**\n"
            f"**{votes_one} głosów** "
            f"({percentage_one:.1f}%)\n\n"
            f"🔵 **{poll.option_two}**\n"
            f"**{votes_two} głosów** "
            f"({percentage_two:.1f}%)"
        ),
        color=discord.Color.from_rgb(
            46,
            204,
            113
        )
    )

    embed.add_field(
        name="📊 Łącznie głosów",
        value=f"**{total_votes}**",
        inline=True
    )

    embed.add_field(
        name="⏱️ Czas trwania",
        value=f"**{poll.duration_minutes} min**",
        inline=True
    )

    embed.set_footer(
        text="666.6MC • System ankiet"
    )

    return embed


class PollView(discord.ui.View):

    def __init__(self, poll):

        super().__init__(
            timeout=None
        )

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

    async def vote_one(
        self,
        interaction: discord.Interaction
    ):

        await self.handle_vote(
            interaction,
            1
        )

    async def vote_two(
        self,
        interaction: discord.Interaction
    ):

        await self.handle_vote(
            interaction,
            2
        )

    async def handle_vote(
        self,
        interaction,
        option
    ):

        if self.poll.finished:

            await safe_response(
                interaction,
                "🔴 Ta ankieta już się zakończyła."
            )

            return

        user_id = interaction.user.id

        if (
            user_id in self.poll.votes_one
            or user_id in self.poll.votes_two
        ):

            await safe_response(
                interaction,
                "⚠️ Możesz oddać tylko jeden głos."
            )

            return

        if option == 1:
            self.poll.votes_one.add(user_id)
        else:
            self.poll.votes_two.add(user_id)

        try:

            await interaction.message.edit(
                embed=create_poll_embed(
                    self.poll
                ),
                view=self
            )

            await safe_response(
                interaction,
                "✅ Twój głos został zapisany!"
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd aktualizacji ankiety: {error}"
            )


async def finish_poll_after_delay(
    poll,
    view
):

    await asyncio.sleep(
        poll.duration_minutes * 60
    )

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

        except discord.NotFound:
            pass

        except discord.HTTPException as error:

            print(
                f"❌ Błąd kończenia ankiety: {error}"
            )


class PollModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="📊 Nowa ankieta"
        )

        self.question = discord.ui.TextInput(
            label="Tytuł ankiety",
            placeholder="Np. Czy dodać nowy tryb?",
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
            label="Czas trwania w minutach",
            placeholder="Np. 60",
            required=True,
            max_length=6
        )

        self.add_item(self.question)
        self.add_item(self.option_one)
        self.add_item(self.option_two)
        self.add_item(self.duration)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            duration_minutes = int(
                self.duration.value
            )

        except ValueError:

            await safe_response(
                interaction,
                "❌ Czas trwania musi być liczbą."
            )

            return

        if duration_minutes < 1:

            await safe_response(
                interaction,
                "❌ Ankieta musi trwać minimum 1 minutę."
            )

            return

        if duration_minutes > 10080:

            await safe_response(
                interaction,
                "❌ Maksymalny czas to 10080 minut."
            )

            return

        if interaction.guild is None:
            return

        poll_channel = interaction.guild.get_channel(
            POLL_CHANNEL_ID
        )

        if poll_channel is None:

            await safe_response(
                interaction,
                "❌ Nie znaleziono kanału ankiet."
            )

            return

        poll = PollData(
            question=self.question.value,
            option_one=self.option_one.value,
            option_two=self.option_two.value,
            duration_minutes=duration_minutes,
            creator_id=interaction.user.id
        )

        view = PollView(poll)

        try:

            message = await poll_channel.send(
                embed=create_poll_embed(poll),
                view=view
            )

            poll.message = message

            await safe_response(
                interaction,
                f"✅ Ankieta została utworzona: {message.jump_url}"
            )

            asyncio.create_task(
                finish_poll_after_delay(
                    poll,
                    view
                )
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd tworzenia ankiety: {error}"
            )

            await safe_response(
                interaction,
                "❌ Wystąpił błąd podczas tworzenia ankiety."
            )


@bot.tree.command(
    name="ankieta",
    description="Tworzy nową ankietę."
)
async def ankieta(
    interaction: discord.Interaction
):

    if interaction.guild is None:
        await safe_response(
            interaction,
            "❌ Komenda dostępna tylko na serwerze."
        )
        return

    ceo_role = interaction.guild.get_role(
        CEO_ROLE_ID
    )

    if ceo_role is None:

        await safe_response(
            interaction,
            "❌ Rola CEO nie została znaleziona."
        )

        return

    if ceo_role not in interaction.user.roles:

        await safe_response(
            interaction,
            "❌ Tylko CEO może korzystać z tej komendy."
        )

        return

    await interaction.response.send_modal(
        PollModal()
    )


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

        self.end_time = (
            datetime.now()
            + timedelta(minutes=duration_minutes)
        )


def create_contest_embed(contest):

    participant_count = len(
        contest.participants
    )

    end_timestamp = int(
        contest.end_time.timestamp()
    )

    if contest.finished:

        status = "🔴 **KONKURS ZAKOŃCZONY**"

    else:

        status = (
            "🟢 **KONKURS TRWA**\n"
            f"⏰ Kończy się: <t:{end_timestamp}:R>"
        )

    return discord.Embed(
        title="🎉 KONKURS — 666.6MC",
        description=(
            f"{status}\n\n"
            "🎁 **Nagroda:**\n"
            f"> {contest.prize}\n\n"
            "🏆 **Liczba zwycięzców:**\n"
            f"> **{contest.winners_count}**\n\n"
            "🎉 Kliknij przycisk **🎉**, aby wziąć udział.\n\n"
            f"👥 **Uczestnicy:** {participant_count}"
        ),
        color=discord.Color.from_rgb(
            46,
            204,
            113
        )
    )


class ContestView(discord.ui.View):

    def __init__(self, contest):

        super().__init__(
            timeout=None
        )

        self.contest = contest

        self.join_button = discord.ui.Button(
            emoji="🎉",
            style=discord.ButtonStyle.success,
            custom_id=f"contest_join_{id(contest)}"
        )

        self.join_button.callback = self.join_contest

        self.add_item(
            self.join_button
        )

    async def join_contest(
        self,
        interaction: discord.Interaction
    ):

        if self.contest.finished:

            await safe_response(
                interaction,
                "🔴 Ten konkurs już się zakończył."
            )

            return

        user_id = interaction.user.id

        if user_id in self.contest.participants:

            await safe_response(
                interaction,
                "⚠️ Już bierzesz udział w tym konkursie!"
            )

            return

        self.contest.participants.add(
            user_id
        )

        try:

            await interaction.message.edit(
                embed=create_contest_embed(
                    self.contest
                ),
                view=self
            )

            await safe_response(
                interaction,
                "🎉 **Dołączyłeś do konkursu!**"
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd aktualizacji konkursu: {error}"
            )


async def finish_contest_after_delay(
    contest,
    view
):

    await asyncio.sleep(
        contest.duration_minutes * 60
    )

    if contest.finished:
        return

    contest.finished = True

    view.join_button.disabled = True

    winners = []

    if contest.participants:

        winners_count = min(
            contest.winners_count,
            len(contest.participants)
        )

        winners = random.sample(
            list(contest.participants),
            winners_count
        )

    if contest.message is None:
        return

    try:

        await contest.message.edit(
            embed=create_contest_embed(contest),
            view=view
        )

        if winners:

            mentions = []

            for winner_id in winners:

                member = (
                    contest.message.guild.get_member(
                        winner_id
                    )
                )

                if member is not None:
                    mentions.append(
                        member.mention
                    )
                else:
                    mentions.append(
                        f"<@{winner_id}>"
                    )

            winners_text = "\n".join(
                f"🏆 {mention}"
                for mention in mentions
            )

            result_embed = discord.Embed(
                title="🏆 KONKURS ZAKOŃCZONY!",
                description=(
                    "Dziękujemy wszystkim za udział! 🎉\n\n"
                    f"🎁 **Nagroda:**\n> {contest.prize}\n\n"
                    f"🏆 **Zwycięzcy:**\n{winners_text}"
                ),
                color=discord.Color.from_rgb(
                    46,
                    204,
                    113
                )
            )

            await contest.message.channel.send(
                content="🎉 **Gratulacje dla zwycięzców!**",
                embed=result_embed
            )

        else:

            await contest.message.channel.send(
                embed=discord.Embed(
                    title="🔴 KONKURS ZAKOŃCZONY",
                    description=(
                        "Niestety nikt nie wziął udziału.\n\n"
                        f"🎁 **Nagroda:**\n> {contest.prize}"
                    ),
                    color=discord.Color.red()
                )
            )

    except discord.NotFound:
        pass

    except discord.HTTPException as error:

        print(
            f"❌ Błąd kończenia konkursu: {error}"
        )


class ContestModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="🎉 Nowy konkurs"
        )

        self.prize = discord.ui.TextInput(
            label="Nagroda",
            placeholder="Np. Ranga VIP na 30 dni",
            required=True,
            max_length=200
        )

        self.winners_count = discord.ui.TextInput(
            label="Liczba zwycięzców",
            placeholder="Np. 3",
            required=True,
            max_length=3
        )

        self.duration = discord.ui.TextInput(
            label="Czas trwania w minutach",
            placeholder="Np. 1440",
            required=True,
            max_length=7
        )

        self.add_item(self.prize)
        self.add_item(self.winners_count)
        self.add_item(self.duration)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            winners_count = int(
                self.winners_count.value
            )

            duration_minutes = int(
                self.duration.value
            )

        except ValueError:

            await safe_response(
                interaction,
                "❌ Liczby muszą być poprawne."
            )

            return

        if winners_count < 1 or winners_count > 100:

            await safe_response(
                interaction,
                "❌ Liczba zwycięzców musi wynosić 1-100."
            )

            return

        if duration_minutes < 1 or duration_minutes > 43200:

            await safe_response(
                interaction,
                "❌ Czas musi wynosić 1-43200 minut."
            )

            return

        if interaction.guild is None:
            return

        channel = interaction.guild.get_channel(
            CONTEST_CHANNEL_ID
        )

        if channel is None:

            await safe_response(
                interaction,
                "❌ Nie znaleziono kanału konkursów."
            )

            return

        contest = ContestData(
            prize=self.prize.value,
            winners_count=winners_count,
            duration_minutes=duration_minutes,
            creator_id=interaction.user.id
        )

        view = ContestView(contest)

        try:

            message = await channel.send(
                embed=create_contest_embed(contest),
                view=view
            )

            contest.message = message

            await safe_response(
                interaction,
                f"✅ Konkurs został utworzony: {message.jump_url}"
            )

            asyncio.create_task(
                finish_contest_after_delay(
                    contest,
                    view
                )
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd konkursu: {error}"
            )

            await safe_response(
                interaction,
                "❌ Wystąpił błąd podczas tworzenia konkursu."
            )


@bot.tree.command(
    name="konkurs",
    description="Tworzy nowy konkurs."
)
async def konkurs(
    interaction: discord.Interaction
):

    if interaction.guild is None:
        await safe_response(
            interaction,
            "❌ Komenda dostępna tylko na serwerze."
        )
        return

    ceo_role = interaction.guild.get_role(
        CEO_ROLE_ID
    )

    if ceo_role is None:

        await safe_response(
            interaction,
            "❌ Rola CEO nie została znaleziona."
        )

        return

    if ceo_role not in interaction.user.roles:

        await safe_response(
            interaction,
            "❌ Tylko CEO może korzystać z tej komendy."
        )

        return

    await interaction.response.send_modal(
        ContestModal()
    )


# =========================================================
# REGULAMIN
# =========================================================

def create_rules_embed():

    return discord.Embed(
        title="📜 OFICJALNY REGULAMIN — 666.6MC.PL",
        description=(
            "Nieznajomość regulaminu nie zwalnia z jego przestrzegania. "
            "Wejście na serwer oznacza akceptację zasad."
        ),
        color=discord.Color.from_rgb(
            46,
            204,
            113
        )
    )


@bot.tree.command(
    name="regulamin",
    description="Wysyła oficjalny regulamin serwera."
)
async def regulamin(
    interaction: discord.Interaction
):

    if interaction.guild is None:
        await safe_response(
            interaction,
            "❌ Komenda dostępna tylko na serwerze."
        )
        return

    ceo_role = interaction.guild.get_role(
        CEO_ROLE_ID
    )

    if ceo_role is None:

        await safe_response(
            interaction,
            "❌ Rola CEO nie została znaleziona."
        )

        return

    if ceo_role not in interaction.user.roles:

        await safe_response(
            interaction,
            "❌ Tylko CEO może korzystać z tej komendy."
        )

        return

    channel = interaction.guild.get_channel(
        RULES_CHANNEL_ID
    )

    if channel is None:

        await safe_response(
            interaction,
            "❌ Nie znaleziono kanału regulaminu."
        )

        return

    try:

        embed = create_rules_embed()

        embed.add_field(
            name="━━━ I. ZASADY OGÓLNE ━━━",
            value=(
                "**1.** Szanuj każdego gracza.\n"
                "**2.** Zakaz wyzywania i toksyczności.\n"
                "**3.** Zakaz spamowania i floodowania.\n"
                "**4.** Zakaz reklamowania bez zgody Administracji.\n"
                "**5.** Zakaz treści NSFW.\n"
                "**6.** Stosuj się do poleceń Administracji."
            ),
            inline=False
        )

        embed.add_field(
            name="━━━ II. DISCORD ━━━",
            value=(
                "**1.** Pisz na odpowiednich kanałach.\n"
                "**2.** Nie pinguj Administracji bez powodu.\n"
                "**3.** Zakaz crashujących botów, skryptów i exploitów.\n"
                "**4.** Zakaz podszywania się.\n"
                "**5.** Szanuj użytkowników i ekipę."
            ),
            inline=False
        )

        embed.add_field(
            name="━━━ III. MINECRAFT ━━━",
            value=(
                "**1.** Zakaz cheatów i wspomagaczy.\n"
                "**2.** Zakaz griefowania.\n"
                "**3.** Zakaz kradzieży.\n"
                "**4.** Zakaz celowego powodowania lagów.\n"
                "**5.** PvP tylko w wyznaczonych strefach.\n"
                "**6.** Zakaz multi-kont."
            ),
            inline=False
        )

        embed.add_field(
            name="━━━ IV. SYSTEM KAR ━━━",
            value=(
                "🟡 **Warn**\n"
                "🔇 **Mute**\n"
                "👢 **Kick**\n"
                "⏳ **TempBan**\n"
                "🔴 **PermBan**"
            ),
            inline=False
        )

        await channel.send(
            embed=embed
        )

        await safe_response(
            interaction,
            "✅ Regulamin został wysłany."
        )

    except discord.HTTPException as error:

        print(
            f"❌ Błąd regulaminu: {error}"
        )

        await safe_response(
            interaction,
            "❌ Wystąpił błąd."
        )


# =========================================================
# CHANGELOG
# =========================================================

class ChangelogModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="📝 Nowy changelog"
        )

        self.change_description = discord.ui.TextInput(
            label="Co zostało zmienione?",
            placeholder="Opisz zmianę...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )

        self.add_item(
            self.change_description
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        channel = interaction.guild.get_channel(
            CHANGELOG_CHANNEL_ID
        )

        if channel is None:

            await safe_response(
                interaction,
                "❌ Nie znaleziono kanału changelogu."
            )

            return

        now = datetime.now()
        timestamp = int(
            now.timestamp()
        )

        embed = discord.Embed(
            title="📝 666.6MC — CHANGELOG",
            description=(
                "### 🚀 Co nowego?\n\n"
                f"{self.change_description.value}"
            ),
            color=discord.Color.from_rgb(
                46,
                204,
                113
            ),
            timestamp=now
        )

        embed.set_author(
            name=(
                f"Opublikowane przez "
                f"{interaction.user.display_name}"
            ),
            icon_url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="📅 Data wdrożenia",
            value=(
                f"<t:{timestamp}:F>\n"
                f"<t:{timestamp}:R>"
            ),
            inline=False
        )

        embed.add_field(
            name="👤 Autor",
            value=interaction.user.mention,
            inline=True
        )

        embed.set_footer(
            text="666.6MC • Oficjalny changelog"
        )

        try:

            await channel.send(
                embed=embed
            )

            await safe_response(
                interaction,
                "✅ Changelog został opublikowany!"
            )

        except discord.HTTPException as error:

            print(
                f"❌ Błąd changelogu: {error}"
            )

            await safe_response(
                interaction,
                "❌ Wystąpił błąd."
            )


@bot.tree.command(
    name="changelog",
    description="Publikuje nowy wpis w changelogu."
)
async def changelog(
    interaction: discord.Interaction
):

    if interaction.guild is None:
        await safe_response(
            interaction,
            "❌ Komenda dostępna tylko na serwerze."
        )
        return

    ceo_role = interaction.guild.get_role(
        CEO_ROLE_ID
    )

    if ceo_role is None:

        await safe_response(
            interaction,
            "❌ Rola CEO nie została znaleziona."
        )

        return

    if ceo_role not in interaction.user.roles:

        await safe_response(
            interaction,
            "❌ Tylko CEO może korzystać z tej komendy."
        )

        return

    await interaction.response.send_modal(
        ChangelogModal()
    )


# =========================================================
# PLUS / MINUS
# =========================================================

class PlusMinusModal(discord.ui.Modal):

    def __init__(self, action_type):

        self.action_type = action_type

        emoji = "➕" if action_type == "plus" else "➖"
        title = "PLUS" if action_type == "plus" else "MINUS"

        super().__init__(
            title=f"{emoji} {title} — 666.6MC"
        )

        self.target = discord.ui.TextInput(
            label="Dla kogo?",
            placeholder="Np. @użytkownik lub nick",
            required=True,
            max_length=100
        )

        self.reason = discord.ui.TextInput(
            label="Za co? / Powód",
            placeholder="Wpisz dokładny powód...",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )

        self.add_item(self.target)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):

        if interaction.channel is None:
            await safe_response(
                interaction,
                "❌ Nie znaleziono kanału."
            )
            return

        is_plus = self.action_type == "plus"
        emoji = "➕" if is_plus else "➖"
        title = "PLUS" if is_plus else "MINUS"

        embed = discord.Embed(
            title=f"{emoji} {title}",
            color=(
                discord.Color.green()
                if is_plus
                else discord.Color.red()
            )
        )

        embed.add_field(
            name="👤 Dla kogo",
            value=self.target.value,
            inline=False
        )

        embed.add_field(
            name="🛡️ Od kogo",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="📝 Powód",
            value=self.reason.value,
            inline=False
        )

        embed.set_footer(
            text="666.6MC • System plusów i minusów"
        )

        try:
            await interaction.channel.send(embed=embed)
            await safe_response(
                interaction,
                f"✅ {title} został dodany na {interaction.channel.mention}."
            )

        except discord.HTTPException as error:
            print(
                f"❌ Błąd wysyłania {title.lower()}: {error}"
            )

            await safe_response(
                interaction,
                "❌ Nie udało się wysłać wpisu."
            )


async def open_plus_minus_modal(interaction, action_type):

    if interaction.guild is None:
        await safe_response(
            interaction,
            "❌ Komenda dostępna tylko na serwerze."
        )
        return

    ceo_role = interaction.guild.get_role(
        CEO_ROLE_ID
    )

    if ceo_role is None:
        await safe_response(
            interaction,
            "❌ Rola CEO nie została znaleziona."
        )
        return

    if ceo_role not in interaction.user.roles:
        await safe_response(
            interaction,
            "❌ Tylko CEO może korzystać z tej komendy."
        )
        return

    await interaction.response.send_modal(
        PlusMinusModal(action_type)
    )


@bot.tree.command(
    name="plus",
    description="Dodaje plusa użytkownikowi."
)
async def plus(interaction: discord.Interaction):

    await open_plus_minus_modal(
        interaction,
        "plus"
    )


@bot.tree.command(
    name="minus",
    description="Dodaje minusa użytkownikowi."
)
async def minus(interaction: discord.Interaction):

    await open_plus_minus_modal(
        interaction,
        "minus"
    )


# =========================================================
# PROPOZYCJE + FILTRY
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

        await punish_everyone_violation(
            message
        )

        return

    # =====================================================
    # PROPOZYCJE
    # =====================================================

    if message.channel.id == PROPOSAL_CHANNEL_ID:

        content = message.content.strip()

        if not content:

            await bot.process_commands(
                message
            )

            return

        try:

            await message.delete()

            now = datetime.now()
            timestamp = int(
                now.timestamp()
            )

            embed = discord.Embed(
                title="💡 NOWA PROPOZYCJA",
                description=(
                    "```text\n"
                    f"{content}\n"
                    "```"
                ),
                color=discord.Color.from_rgb(
                    46,
                    204,
                    113
                ),
                timestamp=now
            )

            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )

            embed.add_field(
                name="👤 Autor",
                value=message.author.mention,
                inline=True
            )

            embed.add_field(
                name="📅 Data",
                value=f"<t:{timestamp}:F>",
                inline=True
            )

            embed.set_footer(
                text="666.6MC • System propozycji"
            )

            proposal_message = await message.channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none()
            )

            await proposal_message.add_reaction("✅")
            await proposal_message.add_reaction("❌")

        except discord.HTTPException as error:

            print(
                f"❌ Błąd propozycji: {error}"
            )

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
                title="🏖️ URLOP GRACZA",
                description=(
                    "```text\n"
                    f"{content}\n"
                    "```"
                ),
                color=discord.Color.from_rgb(52, 152, 219),
                timestamp=now
            )

            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )

            embed.add_field(
                name="👤 Gracz",
                value=message.author.mention,
                inline=True
            )

            embed.add_field(
                name="📅 Data zgłoszenia",
                value=f"<t:{timestamp}:F>",
                inline=True
            )

            embed.set_footer(
                text="666.6MC • System urlopów"
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

                if attachment.filename.lower().endswith(
                    ".gif"
                ):

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

    await bot.process_commands(
        message
    )


# =========================================================
# POWITANIE
# =========================================================

@bot.event
async def on_member_join(
    member: discord.Member
):

    if LOBBY_CHANNEL_ID == 0:
        return

    channel = bot.get_channel(
        LOBBY_CHANNEL_ID
    )

    if channel is None:
        return

    member_count = member.guild.member_count

    embed = discord.Embed(
        title="👋 Witaj na 666.6MC!",
        description=(
            f"Miło Cię widzieć, {member.mention}! 💚\n\n"
            "Życzymy świetnej zabawy na naszym serwerze!\n\n"
            f"Jesteś **{member_count}. osobą** "
            "na naszym Discordzie. 🎉"
        ),
        color=discord.Color.from_rgb(
            46,
            204,
            113
        )
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text="666.6MC • Witamy na serwerze!"
    )

    try:

        await channel.send(
            embed=embed
        )

    except discord.HTTPException as error:

        print(
            f"❌ Błąd powitania: {error}"
        )


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        f"✅ Zalogowano jako {bot.user} "
        f"(ID: {bot.user.id})"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    # =====================================================
    # PERSISTENT VIEWS
    # =====================================================

    try:

        bot.add_view(
            VerificationView()
        )

        bot.add_view(
            TicketPanelView()
        )

        bot.add_view(
            CloseTicketView()
        )

        bot.add_view(
            MediaView()
        )

        bot.add_view(
            RecruitmentView()
        )

        print(
            "✅ Zarejestrowano persistent views."
        )

    except Exception as error:

        print(
            f"❌ Błąd persistent views: {error}"
        )

    # =====================================================
    # SLASH COMMANDS
    # =====================================================

    try:

        synced = await bot.tree.sync()

        print(
            f"✅ Zsynchronizowano "
            f"{len(synced)} komend."
        )

    except Exception as error:

        print(
            f"❌ Błąd synchronizacji komend: {error}"
        )

    # =====================================================
    # PANEL WERYFIKACJI
    # =====================================================

    try:

        channel = bot.get_channel(
            VERIFICATION_CHANNEL_ID
        )

        if channel is None:

            print(
                "❌ Nie znaleziono kanału weryfikacji."
            )

        else:

            exists = False

            async for message in channel.history(
                limit=50
            ):

                if (
                    message.author == bot.user
                    and message.embeds
                    and message.embeds[0].title
                    == "💚 WERYFIKACJA 666.6MC"
                ):

                    exists = True
                    break

            if not exists:

                await channel.send(
                    embed=create_verification_embed(),
                    view=VerificationView()
                )

                print(
                    "✅ Wysłano panel weryfikacji."
                )

            else:

                print(
                    "✅ Panel weryfikacji już istnieje."
                )

    except discord.HTTPException as error:

        print(
            f"❌ Błąd panelu weryfikacji: {error}"
        )

    # =====================================================
    # PANEL TICKETÓW
    # =====================================================

    try:

        channel = bot.get_channel(
            TICKET_PANEL_CHANNEL_ID
        )

        if channel is None:

            print(
                "❌ Nie znaleziono kanału panelu ticketów."
            )

        else:

            panel_exists = False

            async for message in channel.history(
                limit=50
            ):

                if (
                    message.author == bot.user
                    and message.embeds
                    and message.embeds[0].title
                    == "🎫 CENTRUM TICKETÓW 666.6MC"
                ):

                    panel_exists = True
                    break

            if not panel_exists:

                await channel.send(
                    embed=create_ticket_embed(),
                    view=TicketPanelView()
                )

                print(
                    "✅ Panel ticketów został wysłany."
                )

            else:

                print(
                    "✅ Panel ticketów już istnieje."
                )

    except discord.HTTPException as error:

        print(
            f"❌ Błąd panelu ticketów: {error}"
        )

    # =====================================================
    # PANEL REKRUTACJI
    # =====================================================

    try:

        if bot.guilds:

            for guild in bot.guilds:

                success = await update_recruitment_panel(
                    guild
                )

                if success:

                    print(
                        "✅ Panel rekrutacji został sprawdzony."
                    )

    except Exception as error:

        print(
            f"❌ Błąd panelu rekrutacji: {error}"
        )


# =========================================================
# START
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "❌ Brak DISCORD_TOKEN."
    )


bot.run(TOKEN)
