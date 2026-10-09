#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KMJ DOWNLOADER — yt-dlp based all-social-media video downloader for Termux
Made By KMJ TIPS CHANNEL
"""
import os
import re
import sys
import time
import shutil
import threading
import subprocess

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn, TextColumn
    from rich.align import Align
    from rich.text import Text
except ImportError:
    print("rich module missing! Run: pip install rich")
    sys.exit(1)

try:
    from yt_dlp import YoutubeDL
    HAVE_YTDLP = True
except ImportError:
    HAVE_YTDLP = False

console = Console()

BANNER = r"""
██╗  ██╗███╗   ███╗     ██╗
██║ ██╔╝████╗ ████║     ██║
█████╔╝ ██╔████╔██║     ██║
██╔═██╗ ██║╚██╔╝██║██   ██║
██║  ██╗██║ ╚═╝ ██║╚█████╔╝
╚═╝  ╚═╝╚═╝     ╚═╝ ╚════╝ 
"""

SUB = "D O W N L O A D E R"

COLORS = ["red", "yellow", "green", "cyan", "magenta", "blue"]


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def banner_animate(cycles=1):
    """Animated KMJ banner with cycling colors."""
    for i in range(cycles * len(COLORS)):
        clear()
        color = COLORS[i % len(COLORS)]
        t = Text(BANNER, style=f"bold {color}")
        s = Text(SUB, style=f"bold {color}")
        console.print(Align.center(t))
        console.print(Align.center(s))
        console.print(Align.center(Text("Made By KMJ TIPS CHANNEL", style="bold white")))
        time.sleep(0.12)
    clear()
    t = Text(BANNER, style="bold cyan")
    console.print(Align.center(t))
    console.print(Align.center(Text(SUB, style="bold yellow")))
    console.print(Align.center(Text("Made By KMJ TIPS CHANNEL", style="bold white")))
    console.print()


def get_download_dir():
    """KMJ TIPS folder — prefers shared Downloads, falls back to $HOME."""
    cands = [
        os.path.expanduser("~/storage/downloads/KMJ TIPS"),
        os.path.expanduser("~/storage/shared/Download/KMJ TIPS"),
        os.path.expanduser("~/KMJ TIPS"),
    ]
    for p in cands:
        try:
            os.makedirs(p, exist_ok=True)
            return p
        except OSError:
            continue
    return os.getcwd()


def loading_spinner(stop_event, label="Fetching video info"):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{frames[i % len(frames)]} {label}... ")
        sys.stdout.flush()
        i += 1
        time.sleep(0.08)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()


def fetch_info(url):
    """Return (info_dict, is_playlist) or (None, False) on error."""
    stop = threading.Event()
    th = threading.Thread(target=loading_spinner, args=(stop,))
    th.start()
    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": False,
            "socket_timeout": 20,
            "listformats": False,
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info, info.get("_type") == "playlist"
    except Exception as e:
        msg = str(e)
        hint = ""
        if "not a bot" in msg or "Sign in to confirm" in msg:
            hint = ("\n[yellow]💡 YouTube ne bot-check lagaya hai. Phone par apne net se try karo.[/]")
        console.print(Panel(f"[bold red]Error:[/] {msg[:200]}" + hint, title="Failed", border_style="red"))
        return None, False
    finally:
        stop.set()
        th.join()


def show_info(info):
    tbl = Table(show_header=False, box=None, padding=(0, 2))
    tbl.add_column(style="bold cyan")
    tbl.add_column(style="white")
    title = (info.get("title") or "Unknown")[:70]
    uploader = info.get("uploader") or info.get("channel") or "Unknown"
    dur = info.get("duration")
    dur_s = f"{int(dur // 60)}:{int(dur % 60):02d}" if dur else "Live/Unknown"
    views = info.get("view_count")
    views_s = f"{views:,}" if views else "N/A"
    tbl.add_row("🎬 Title", title)
    tbl.add_row("👤 Uploader", str(uploader)[:40])
    tbl.add_row("⏱ Duration", dur_s)
    tbl.add_row("👁 Views", views_s)
    tbl.add_row("🌐 Site", str(info.get("extractor_key") or info.get("extractor") or ""))
    console.print(Panel(tbl, title="[bold green]Video Found[/]", border_style="green"))


def fmt_size(f):
    s = f.get("filesize") or f.get("filesize_approx")
    if not s:
        return "~"
    if s >= 1 << 30:
        return f"{s / (1 << 30):.1f} GB"
    if s >= 1 << 20:
        return f"{s / (1 << 20):.1f} MB"
    return f"{s / 1024:.0f} KB"


def pick_format_from_list(info):
    """Show ALL available qualities, let user pick. Returns yt-dlp format string."""
    formats = info.get("formats") or []
    vids = [f for f in formats if f.get("vcodec") not in (None, "none")]
    # de-dupe by height, keep best per height
    seen_h, rows = set(), []
    for f in sorted(vids, key=lambda x: (x.get("height") or 0, x.get("fps") or 0), reverse=True):
        h = f.get("height")
        key = (h, f.get("fps"), f.get("vcodec"))
        if h and key not in seen_h:
            seen_h.add(key)
            rows.append(f)
        if len(rows) >= 15:
            break

    tbl = Table(title="📋 All Available Qualities", show_header=True, header_style="bold magenta")
    tbl.add_column("#", style="bold cyan", width=4)
    tbl.add_column("Format", style="white")
    tbl.add_column("Resolution", style="green")
    tbl.add_column("FPS", style="yellow")
    tbl.add_column("Size≈", style="cyan")
    tbl.add_column("Codec", style="dim")
    for i, f in enumerate(rows, 1):
        h, w = f.get("height"), f.get("width")
        res = f"{w}x{h}" if w and h else f"{h}p" if h else "?"
        tbl.add_row(str(i), str(f.get("format_id")), res,
                    str(f.get("fps") or "-"), fmt_size(f),
                    str(f.get("vcodec") or "")[:12])
    tbl.add_row("A", "bestaudio", "MP3 🎵", "-", "-", "audio")
    console.print(tbl)

    ch = console.input("[bold cyan]👉 Pick number (or A for MP3, B for best): [/]").strip().lower()
    if ch == "a":
        return "audio"
    if ch == "b" or not ch:
        return "best"
    try:
        f = rows[int(ch) - 1]
    except (ValueError, IndexError):
        console.print("[yellow]⚠ Invalid — using Best quality.[/]")
        return "best"
    fid = str(f["format_id"])
    # video-only stream? merge with best audio
    if f.get("acodec") in (None, "none"):
        return f"{fid}+bestaudio/best"
    return fid


def quality_menu():
    console.print(Panel(
        "[1] 🚀 Best Quality (max)\n"
        "[2] 📺 1080p Full HD\n"
        "[3] 📺 720p HD\n"
        "[4] 📺 480p\n"
        "[5] 📱 360p (small size)\n"
        "[6] 🎵 Audio Only (MP3)\n"
        "[7] 📋 All Qualities (full list)",
        title="[bold yellow]Select Quality[/]", border_style="yellow"))
    ch = console.input("[bold cyan]👉 Choice [1-7]: [/]").strip()
    return {
        "1": "best", "2": "1080", "3": "720",
        "4": "480", "5": "360", "6": "audio", "7": "all",
    }.get(ch, "best")


def resolve_quality(choice, info):
    if choice == "all":
        return pick_format_from_list(info)
    return choice


def build_opts(quality, outdir, progress_hook):
    outtmpl = os.path.join(outdir, "%(title).120s [%(id)s].%(ext)s")
    if quality == "audio":
        fmt = "bestaudio/best"
        post = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
    elif quality == "best":
        fmt = "bestvideo+bestaudio/best"
        post = []
    elif re.fullmatch(r"\d+", quality or ""):
        h = quality
        fmt = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        post = []
    else:
        fmt = quality  # explicit format_id from all-qualities list
        post = []
    return {
        "format": fmt,
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 5,
        "postprocessors": post,
        "progress_hooks": [progress_hook],
        "merge_output_format": "mp4",
    }


def download(url, quality, outdir, label=None):
    with Progress(
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        TextColumn("[bold green]{task.fields[percent]}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"⬇ {label or 'Downloading'}", total=100, percent="0%")

        def hook(d):
            st = d.get("status")
            if st == "downloading":
                tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                dl = d.get("downloaded_bytes") or 0
                if tot:
                    pct = dl / tot * 100
                    progress.update(task, total=tot, completed=dl, percent=f"{pct:.1f}%")
                else:
                    progress.update(task, completed=dl, percent="...")
            elif st == "finished":
                t = progress.tasks[0].total or 1
                progress.update(task, completed=t, percent="100%")

        opts = build_opts(quality, outdir, hook)
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as e:
            console.print(Panel(f"[bold red]Download failed:[/] {str(e)[:250]}",
                                title="Error", border_style="red"))
            return False
    return True


def valid_url(u):
    return bool(re.match(r"^https?://", u.strip()))


def single_flow(audio_only=False):
    console.print(Panel(
        "Paste video link from [bold]YouTube, Instagram, Facebook,\nTikTok, Twitter/X, Snapchat, Pinterest[/] & 1000+ sites",
        title="🔗 Enter URL", border_style="magenta"))
    url = console.input("[bold cyan]👉 URL (or 'b' to go back): [/]").strip()
    if not url or url.lower() == "b":
        return
    if not valid_url(url):
        console.print("[bold red]❌ Invalid URL! Must start with http:// or https://[/]")
        time.sleep(1.2)
        return

    info, is_playlist = fetch_info(url)
    if not info:
        time.sleep(1.5)
        return
    if is_playlist:
        c = console.input("[bold yellow]📃 Playlist detected! Download whole playlist? [y/N]: [/]").strip().lower()
        if c != "y":
            console.print("[yellow]Single-video mode only for now. Paste a direct video link.[/]")
            time.sleep(1.5)
            return
    show_info(info)
    choice = "audio" if audio_only else quality_menu()
    quality = resolve_quality(choice, info)
    outdir = get_download_dir()
    console.print(f"[dim]📁 Saving to: {outdir}[/]")
    time.sleep(0.5)
    if download(url, quality, outdir):
        console.print(Panel("[bold green]✅ Download Complete![/]\n"
                            f"[dim]📁 Saved in: {outdir}[/]",
                            title="Done", border_style="green"))
    console.input("[dim]Press Enter to continue...[/]")


def batch_flow():
    console.print(Panel(
        "Paste [bold]multiple links[/] — one per line.\n"
        "Blank line + Enter = start download.\n"
        "Type [bold]'b'[/] to go back.",
        title="📦 Batch Download (Bulk)", border_style="blue"))
    links = []
    n = 1
    while True:
        u = console.input(f"[cyan][{n}] 👉 [/]").strip()
        if u.lower() == "b":
            return
        if not u:
            break
        # allow comma/space separated paste too
        parts = [p.strip() for p in re.split(r"[\s,]+", u) if p.strip()]
        for p in parts:
            if valid_url(p):
                links.append(p)
                n += 1
            else:
                console.print(f"[red]  ✖ skipped (bad url): {p[:50]}[/]")
    # de-dupe, keep order
    links = list(dict.fromkeys(links))
    if not links:
        console.print("[yellow]⚠ No valid links![/]")
        time.sleep(1.2)
        return

    console.print(Panel(f"[bold green]{len(links)} links[/] ready for bulk download",
                        title="Batch", border_style="green"))
    console.print(Panel(
        "[1] 🚀 Best Quality\n[2] 📺 720p HD\n[3] 📺 480p\n[4] 🎵 Audio MP3 (all)",
        title="[bold yellow]Quality for ALL[/]", border_style="yellow"))
    ch = console.input("[bold cyan]👉 Choice [1-4]: [/]").strip()
    quality = {"1": "best", "2": "720", "3": "480", "4": "audio"}.get(ch, "best")
    outdir = get_download_dir()
    console.print(f"[dim]📁 Saving to: {outdir}[/]\n")
    time.sleep(0.5)

    ok_count, fail_count = 0, 0
    for i, url in enumerate(links, 1):
        console.print(Panel(f"[bold cyan][{i}/{len(links)}][/] {url[:80]}",
                            border_style="dim"))
        if download(url, quality, outdir, label=f"[{i}/{len(links)}] Downloading"):
            ok_count += 1
            console.print("[green]  ✅ done[/]")
        else:
            fail_count += 1
            console.print("[red]  ❌ failed — next...[/]")
    console.print(Panel(
        f"[bold green]✅ {ok_count} downloaded[/]" +
        (f"   [bold red]❌ {fail_count} failed[/]" if fail_count else "") +
        f"\n[dim]📁 Saved in: {outdir}[/]",
        title="Batch Done", border_style="green"))
    console.input("[dim]Press Enter to continue...[/]")


def sites_list():
    sites = ["YouTube", "Instagram", "Facebook", "TikTok", "Twitter / X",
             "Snapchat", "Pinterest", "Reddit", "Dailymotion", "Vimeo",
             "Twitch", "Likee", "Moj", "Josh", "Roposo", "+ 1000 more..."]
    tbl = Table(title="🌐 Supported Sites", show_header=False, box=None)
    for i in range(0, len(sites), 2):
        row = sites[i:i + 2]
        tbl.add_row(*[f"[cyan]• {s}[/]" for s in row])
    console.print(Panel(tbl, border_style="blue"))


def main_menu():
    while True:
        banner_animate(cycles=1)
        console.print(Panel(
            "[1] 🎬 Download Video\n"
            "[2] 📦 Batch Download (bulk links)\n"
            "[3] 🎵 Download Audio (MP3)\n"
            "[4] 🌐 Supported Sites\n"
            "[5] 📁 Open Download Folder\n"
            "[6] ❌ Exit",
            title="[bold magenta]KMJ DOWNLOADER — Main Menu[/]",
            border_style="magenta"))
        ch = console.input("[bold cyan]👉 Choice [1-6]: [/]").strip()
        if ch == "1":
            single_flow(audio_only=False)
        elif ch == "2":
            batch_flow()
        elif ch == "3":
            single_flow(audio_only=True)
        elif ch == "4":
            sites_list()
            console.input("[dim]Press Enter to continue...[/]")
        elif ch == "5":
            d = get_download_dir()
            console.print(f"[green]📁 {d}[/]")
            if shutil.which("termux-open"):
                subprocess.run(["termux-open", d])
            console.input("[dim]Press Enter to continue...[/]")
        elif ch == "6":
            console.print(Align.center(Text("Thanks for using KMJ DOWNLOADER 💛", style="bold yellow")))
            console.print(Align.center(Text("Made By KMJ TIPS CHANNEL", style="bold white")))
            break
        else:
            console.print("[bold red]❌ Wrong choice![/]")
            time.sleep(0.8)


def main():
    if not HAVE_YTDLP:
        console.print("[bold red]yt-dlp not found! Run setup.sh first.[/]")
        sys.exit(1)
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Bye! Made By KMJ TIPS CHANNEL[/]")


if __name__ == "__main__":
    main()
