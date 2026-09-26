import urllib.request, json, re
from datetime import datetime, timezone

webhook_url = "https://discord.com/api/webhooks/1553388229225480293/J2W99-4z0CUnlYisb3RbHfwqcpFjiTSBJ_LX5xwSJrv4f3ggWOPa85LZAdSNe1Bt74lD"

def send_minimal_style(action, bucket, trader, price, shares, usdc, url):
    is_buy = "BUY" in action
    color = 0x2ecc71 if is_buy else 0xe74c3c # Clean modern green / red
    
    # Ultra-minimal layout: Zero clutter, high breathing room
    embed = {
        "title": f"{action}  •  {bucket}",
        "url": url,
        "color": color,
        "description": (
            f"👤 **{trader}**\n\n"
            f"💰 **${price:.3f}** ({price*100:.0f}%)  •  📦 **${usdc:,.2f}** ({shares:,.0f} shares)\n\n"
            f"👉 **[เปิดดูบน Polymarket]({url})**"
        ),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps({"username": "Polymarket Signal", "avatar_url": "https://polymarket.com/favicon.ico", "embeds": [embed]}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Sent minimal style:", resp.getcode())

# Test sending minimal style
send_minimal_style(
    action="🟢 BUY NO",
    bucket="Amsterdam 21°C",
    trader="Weather Sniper",
    price=0.910,
    shares=25.0,
    usdc=22.85,
    url="https://polymarket.com/event/highest-temperature-in-amsterdam-on-september-26-2026"
)
