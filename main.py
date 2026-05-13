import sys
sys.path.insert(0, 'discord.py-self-master')
import asyncio
import discord
from discord.ext import commands
import json
import random
from collections import defaultdict

def load_cfg(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Missing config: {path}")
        raise
    except json.JSONDecodeError:
        print(f"[ERROR] Bad JSON in: {path}")
        raise

cfg = load_cfg('config/config.json')

tokens = cfg.get('tokens') or [cfg.get('token')]
channel = int(cfg.get('channel_id'))
prefix = cfg.get('prefix', '!')
delay_min = cfg.get('min_delay', 10)
delay_max = cfg.get('max_delay', 300)

clicked = defaultdict(set)

stats = {
    'detected': 0,
    'joined': 0,
    'errors': 0
}

acct_stats = {}

def find_btn(components):
    try:
        for row in components:
            if hasattr(row, 'children'):
                for btn in row.children:
                    if hasattr(btn, 'label') and btn.label and btn.label.lower() == 'entry':
                        return btn
    except:
        pass
    return None

def get_embed_info(embed):
    try:
        info = []
        if embed.title:
            info.append(f"Title: {embed.title}")
        if embed.description:
            desc = embed.description[:100] + "..." if len(embed.description) > 100 else embed.description
            info.append(f"Description: {desc}")
        return " | ".join(info) if info else "Giveaway"
    except:
        return "Giveaway"

async def join_giveaway(btn, msg, name, idx):
    try:
        delay = random.uniform(delay_min, delay_max)
        print(f"[{name}] 🎯 Found giveaway! Waiting {delay:.1f}s...")
        await asyncio.sleep(delay)
        print(f"[{name}] 📤 Clicking entry...")
        await btn.click()
        acct_stats[idx]['joined'] += 1
        stats['joined'] += 1
        print(f"[{name}] ✓ Joined! (Total: {acct_stats[idx]['joined']})")
    except discord.errors.NotFound:
        print(f"[{name}] ✗ Button gone")
        acct_stats[idx]['errors'] += 1
        stats['errors'] += 1
    except discord.errors.Forbidden:
        print(f"[{name}] ✗ No perms")
        acct_stats[idx]['errors'] += 1
        stats['errors'] += 1
    except Exception as e:
        print(f"[{name}] ✗ Failed: {str(e)}")
        acct_stats[idx]['errors'] += 1
        stats['errors'] += 1

def make_bot(token, idx, name):
    bot = commands.Bot(command_prefix=prefix, self_bot=True)

    @bot.event
    async def on_ready():
        username = bot.user.name
        user_id = bot.user.id
        print(f"\n[{name}] ✓ Logged in as: {username}#{bot.user.discriminator} (ID: {user_id})")
        print(f"[{name}] ✓ Watching channel: {channel}")
        print(f"[{name}] ✓ Status: Ready\n")

    @bot.event
    async def on_message(msg):
        if msg.channel.id != channel:
            return
        if msg.author == bot.user:
            return

        try:
            if not msg.embeds or not msg.components:
                return

            btn = find_btn(msg.components)
            if not btn:
                return

            if msg.id in clicked[idx]:
                return

            clicked[idx].add(msg.id)
            acct_stats[idx]['detected'] += 1
            stats['detected'] += 1

            print(f"\n[{name}] 🎁 Giveaway! Message ID: {msg.id}")
            print(f"[{name}] By: {msg.author.name}")
            info = get_embed_info(msg.embeds[0]) if msg.embeds else "No info"
            print(f"[{name}] {info}")

            await join_giveaway(btn, msg, name, idx)

        except Exception as e:
            acct_stats[idx]['errors'] += 1
            stats['errors'] += 1
            print(f"[{name}] ✗ Error: {str(e)}")

    return bot, token

def show_stats():
    print("\n" + "="*70)
    print("STATS")
    print("="*70)
    
    for idx, info in acct_stats.items():
        name = f"Account {idx + 1}"
        print(f"\n[{name}]")
        print(f"  Detected: {info['detected']}")
        print(f"  Joined: {info['joined']}")
        print(f"  Errors: {info['errors']}")
    
    print(f"\n[TOTALS]")
    print(f"  Detected: {stats['detected']}")
    print(f"  Joined: {stats['joined']}")
    print(f"  Errors: {stats['errors']}")
    print("="*70 + "\n")

async def run_bots():
    tasks = []
    for idx, token in enumerate(tokens):
        name = f"Account {idx + 1}"
        acct_stats[idx] = {'detected': 0, 'joined': 0, 'errors': 0}
        bot, _ = make_bot(token, idx, name)
        tasks.append(bot.start(token))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        print("\n" + "="*70)
        print(f"[INFO] Giveaway Joiner - {len(tokens)} account(s) loading")
        print(f"[INFO] Channel: {channel}")
        print(f"[INFO] Delay: {delay_min}s - {delay_max}s")
        print("="*70)
        print("\n[ACCOUNTS STARTING]\n")
        asyncio.run(run_bots())
    except KeyboardInterrupt:
        print("\n[INFO] Stopped")
        show_stats()
    except Exception as e:
        print(f"[ERROR] Failed: {str(e)}")
        raise

