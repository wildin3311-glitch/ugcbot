import os
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

# ========= LOAD TOKEN =========
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ========= DISCORD CLIENT =========
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ========= CONSTANTS =========

RATE = 100.0  # 100r = $1
PASTEL_PINK = 0xF8C8DC

# Thumbnail bunny image
UNIBUN_IMG = (
    "https://cdn.discordapp.com/attachments/1400237180135411885/"
    "1438740770013184071/Untitled32_20251112212618.png?ex=6917fb42&is=6916a9c2&"
    "hm=36dc9c3f14106172de264786228da2ffbb134b522fc53c21b7ee9d9202dec55a"
)

# Big bottom image for embeds
BIG_IMG = (
    "https://media.discordapp.net/attachments/1431892425034567721/"
    "1431892425248604210/image.png?ex=691774fd&is=6916237d&"
    "hm=587cbc418d82d4938b829788dcbb75bbd69892543c8c3b07301ef55b00f8318f&"
    "&format=webp&quality=lossless&width=1235&height=579"
)

# ========= PRICE TABLES =========

# Necklaces
NECKLACE_BASE = {
    "one-name": 400,
    "two-name": 500,
    "three-name": 600,
    "pearl-small": 400,
    "pearl-jumbo": 500,
    "basic-necklace": 100,
    "cuban-chains": 500,
}
BEADED_ALLOWED = {"one-name", "two-name", "three-name"}

# Other UGC
OTHER_BASE = {
    "bows": 150,
    "bracelet": 250,
    "hair-clips": 100,
    "head-sign": 200,
}
OTHER_ADDON = {
    "bows": {"add-name": 50},
    "bracelet": {"add-charm-or-name": 50},
    "hair-clips": {"add-charm-or-name": 50},
    "head-sign": {},  # free
}

# Upload / fast pass (for necklace & ugc)
UPLOADS_R = {
    "none": 0,
    "limited-upload": 1700,
    "normal-upload": 2500,
    "fast-pass-week": 500,
    "fast-pass-day": 1000,
}
UPLOADS_USD = {
    "none": 0,
    "limited-upload": 12,
    "normal-upload": 18,
    "fast-pass-week": 5,
    "fast-pass-day": 10,
}

# ========= STAFF ROLE IDS =========

ALLOWED_ROLE_IDS = {
    1431025682913165322,
    1430841958708019272,
    1432580761143480330,
    1430750454375251978,
    1438754771992576120,
}

# ========= HELPERS =========

def r_to_usd(r: int) -> float:
    return round(r / RATE, 2)


def pastel_embed(title: str, desc: Optional[str] = None) -> discord.Embed:
    e = discord.Embed(
        title=title,
        description=desc or "Prices",
        color=PASTEL_PINK,
    )
    e.set_footer(text="")
    return e


def is_staff(user: discord.Member) -> bool:
    """Returns True if the member has ANY of the allowed staff role IDs."""
    try:
        for role in user.roles:
            if role.id in ALLOWED_ROLE_IDS:
                return True
    except Exception:
        pass
    return False

# ========= /NECKLACE =========

@tree.command(
    name="necklace",
    description="Necklace price calculator (upload + fast pass + discount)"
)
@app_commands.describe(
    style="Choose necklace style",
    upload="Upload option",
    fast_pass="Fast pass option",
    beaded="Add beaded +100r (name necklaces only)",
    quantity="How many?",
    discount="Discount % (0–100)",
    notes="Optional notes (for you only)",
)
@app_commands.choices(
    style=[
        app_commands.Choice(name="one-name (400r)", value="one-name"),
        app_commands.Choice(name="two-name (500r)", value="two-name"),
        app_commands.Choice(name="three-name (600r)", value="three-name"),
        app_commands.Choice(name="pearl small (400r)", value="pearl-small"),
        app_commands.Choice(name="pearl jumbo (500r)", value="pearl-jumbo"),
        app_commands.Choice(name="basic necklace (100r)", value="basic-necklace"),
        app_commands.Choice(name="cuban chains (500r)", value="cuban-chains"),
    ]
)
@app_commands.choices(
    upload=[
        app_commands.Choice(name="I'll upload it myself (no fee)", value="none"),
        app_commands.Choice(name="Limited upload (1700r)", value="limited-upload"),
        app_commands.Choice(name="Normal upload (2500r)", value="normal-upload"),
    ]
)
@app_commands.choices(
    fast_pass=[
        app_commands.Choice(name="No fast pass", value="none"),
        app_commands.Choice(name="Fast pass week (500r)", value="fast-pass-week"),
        app_commands.Choice(name="Fast pass day (1000r)", value="fast-pass-day"),
    ]
)
async def necklace(
    interaction: discord.Interaction,
    style: app_commands.Choice[str],
    upload: app_commands.Choice[str],
    fast_pass: app_commands.Choice[str],
    beaded: bool = False,
    quantity: app_commands.Range[int, 1, 10] = 1,
    discount: app_commands.Range[int, 0, 100] = 0,
    notes: Optional[str] = None,
):
    # STAFF CHECK
    if not isinstance(interaction.user, discord.Member) or not is_staff(interaction.user):
        await interaction.response.send_message(
            "Only staff can use this command ",
            ephemeral=True,
        )
        return

    # Base + beaded
    base = NECKLACE_BASE[style.value]
    extra = 100 if (beaded and style.value in BEADED_ALLOWED) else 0

    necklace_r = (base + extra) * quantity
    necklace_usd = r_to_usd(necklace_r)

    upload_r = UPLOADS_R[upload.value]
    fast_r = UPLOADS_R[fast_pass.value]

    upload_usd = UPLOADS_USD[upload.value]
    fast_usd = UPLOADS_USD[fast_pass.value]

    # Subtotal before discount
    subtotal_r = necklace_r + upload_r + fast_r
    subtotal_usd = r_to_usd(subtotal_r)

    # Apply discount
    if discount > 0:
        final_r = int(round(subtotal_r * (100 - discount) / 100))
    else:
        final_r = subtotal_r

    final_usd = r_to_usd(final_r)

    discount_r = subtotal_r - final_r
    discount_usd = r_to_usd(discount_r)

    # Build embed
    e = pastel_embed("/unibun")
    e.set_thumbnail(url=UNIBUN_IMG)
    e.set_image(url=BIG_IMG)

    # Style
    e.add_field(name="Style", value=style.name, inline=False)

    # Necklace calc
    calc = f"base {base}r"
    if extra:
        calc += " + beaded 100r"
    calc += f" × {quantity}"
    e.add_field(name="Necklace calc", value=calc, inline=False)

    e.add_field(
        name="Necklace subtotal",
        value=f"{necklace_r}r ≈ ${necklace_usd:.2f}",
        inline=False,
    )

    # Upload
    e.add_field(
        name="Upload option",
        value=f"{upload.name}\nCost: {upload_r}r ≈ ${upload_usd:.2f}",
        inline=False,
    )

    # Fast pass
    e.add_field(
        name="Fast pass",
        value=f"{fast_pass.name}\nCost: {fast_r}r ≈ ${fast_usd:.2f}",
        inline=False,
    )

    # Subtotal + discount + final
    e.add_field(
        name="Subtotal (before discount)",
        value=f"{subtotal_r}r ≈ ${subtotal_usd:.2f}",
        inline=False,
    )

    if discount > 0:
        e.add_field(
            name="Discount Applied",
            value=f"{discount}% → -{discount_r}r ≈ -${discount_usd:.2f}",
            inline=False,
        )

    e.add_field(
        name="Final Total",
        value=f"**{final_r}r** ≈ **${final_usd:.2f}**",
        inline=False,
    )

    if notes:
        e.add_field(name="Notes", value=notes, inline=False)

    await interaction.response.send_message(embed=e)

# ========= /UGC =========

@tree.command(
    name="ugc",
    description="UGC price calculator (bows, bracelets, hair clips, head signs)"
)
@app_commands.describe(
    item="Choose the UGC item",
    addon="Add-on (if allowed)",
    upload="Upload option",
    fast_pass="Fast pass",
    quantity="How many?",
    discount="Discount % (0–100)",
    notes="Optional notes",
)
@app_commands.choices(
    item=[
        app_commands.Choice(name="bows (150r)", value="bows"),
        app_commands.Choice(name="bracelet (250r)", value="bracelet"),
        app_commands.Choice(name="hair clips (100r)", value="hair-clips"),
        app_commands.Choice(name="head sign (200r)", value="head-sign"),
    ]
)
@app_commands.choices(
    addon=[
        app_commands.Choice(name="none", value="none"),
        app_commands.Choice(name="add name (bows) +50r", value="add-name"),
        app_commands.Choice(
            name="add charm or name (bracelet/hair) +50r",
            value="add-charm-or-name",
        ),
    ]
)
@app_commands.choices(
    upload=[
        app_commands.Choice(name="I'll upload it myself (no fee)", value="none"),
        app_commands.Choice(name="Limited upload (1700r)", value="limited-upload"),
        app_commands.Choice(name="Normal upload (2500r)", value="normal-upload"),
    ]
)
@app_commands.choices(
    fast_pass=[
        app_commands.Choice(name="No fast pass", value="none"),
        app_commands.Choice(name="Fast pass week (500r)", value="fast-pass-week"),
        app_commands.Choice(name="Fast pass day (1000r)", value="fast-pass-day"),
    ]
)
async def ugc(
    interaction: discord.Interaction,
    item: app_commands.Choice[str],
    addon: app_commands.Choice[str],
    upload: app_commands.Choice[str],
    fast_pass: app_commands.Choice[str],
    quantity: app_commands.Range[int, 1, 10] = 1,
    discount: app_commands.Range[int, 0, 100] = 0,
    notes: Optional[str] = None,
):
    # STAFF CHECK
    if not isinstance(interaction.user, discord.Member) or not is_staff(interaction.user):
        await interaction.response.send_message(
            "Only staff can use this command 💗",
            ephemeral=True,
        )
        return

    # Base + addon
    base = OTHER_BASE[item.value]
    charge = 0
    allowed_addons = OTHER_ADDON[item.value]
    if addon.value != "none" and addon.value in allowed_addons:
        charge = allowed_addons[addon.value]

    item_r = (base + charge) * quantity
    item_usd = r_to_usd(item_r)

    upload_r = UPLOADS_R[upload.value]
    fast_r = UPLOADS_R[fast_pass.value]

    upload_usd = UPLOADS_USD[upload.value]
    fast_usd = UPLOADS_USD[fast_pass.value]

    # Subtotal
    subtotal_r = item_r + upload_r + fast_r
    subtotal_usd = r_to_usd(subtotal_r)

    # Discount
    if discount > 0:
        final_r = int(round(subtotal_r * (100 - discount) / 100))
    else:
        final_r = subtotal_r

    final_usd = r_to_usd(final_r)
    discount_r = subtotal_r - final_r
    discount_usd = r_to_usd(discount_r)

    # Embed
    e = pastel_embed("/unibun UGC")
    e.set_thumbnail(url=UNIBUN_IMG)
    e.set_image(url=BIG_IMG)

    e.add_field(name="Item", value=item.name, inline=False)

    # Calc
    calc = f"base {base}r"
    if charge:
        calc += f" + add-on {charge}r"
    calc += f" × {quantity}"
    e.add_field(name="UGC calc", value=calc, inline=False)

    e.add_field(
        name="UGC subtotal",
        value=f"{item_r}r ≈ ${item_usd:.2f}",
        inline=False,
    )

    # Upload
    e.add_field(
        name="Upload option",
        value=f"{upload.name}\nCost: {upload_r}r ≈ ${upload_usd:.2f}",
        inline=False,
    )

    # Fast pass
    e.add_field(
        name="Fast pass",
        value=f"{fast_pass.name}\nCost: {fast_r}r ≈ ${fast_usd:.2f}",
        inline=False,
    )

    # Subtotal + discounts
    e.add_field(
        name="Subtotal (before discount)",
        value=f"{subtotal_r}r ≈ ${subtotal_usd:.2f}",
        inline=False,
    )

    if discount > 0:
        e.add_field(
            name="Discount Applied",
            value=f"{discount}% → -{discount_r}r ≈ -${discount_usd:.2f}",
            inline=False,
        )

    e.add_field(
        name="Final Total",
        value=f"**{final_r}r** ≈ **${final_usd:.2f}**",
        inline=False,
    )

    if notes:
        e.add_field(name="Notes", value=notes, inline=False)

    await interaction.response.send_message(embed=e)


# ========= BOT READY =========

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot online as {bot.user} & commands synced!")


# ========= RUN BOT =========

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Missing DISCORD_TOKEN in .env!")
    bot.run(TOKEN)
