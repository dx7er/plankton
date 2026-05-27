#!/usr/bin/env python3
"""
Plankton - Secure Drive Sanitisation Tool
Author: dx73r
Version: 1.0
"""

import os
import sys
import time
import subprocess
import psutil
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich import box


console = Console()


PLANKTON_ART = [
    r"⣾⠿⣦⣠⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣄⣴⠿⣷",
    r"⢹⣷⣿⠿⣧⣀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣼⠿⣿⣾⡏",
    r"⠈⠋⢻⣶⣿⣿⡃⠀⠀⠀⠀⠀⠀⢘⣿⣿⣶⡟⠙⠁",
    r"⠀⠀⠘⢿⣧⣬⣿⡿⠀⠀⠀⠀⢿⣿⣥⣼⡿⠃⠀⠀",
    r"⠀⠀⠀⢾⣿⡟⠙⣷⡀⣀⣀⢀⣾⠋⢻⣿⡷⠀⠀⠀",
    r"⠀⠀⠀⠀⢸⣧⡶⠟⠛⠛⠛⠛⠻⢶⣼⡇⠀⠀⠀⠀",
    r"⠀⠀⠀⣰⡿⠋⢀⣀⣀⣤⣤⣴⣦⠀⠙⢿⣆⠀⠀⠀",
    r"⠀⠀⢰⡟⠀⠀⠈⠛⠛⠛⠋⠉⠁⠀⠀⠀⢻⡆⠀⠀",
    r"⠀⠀⢸⡇⠀⠀⢀⣴⣶⣾⣷⣶⣦⡀⠀⠀⢸⡇⠀⠀",
    r"⠀⠀⢸⡇⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⢸⡇⠀⠀",
    r"⠀⠀⢸⡇⠀⣾⡏⠉⢹⣿⣿⡏⠉⢹⣷⠀⢸⡇⠀⠀",
    r"⠀⠀⢸⡇⠀⠸⣧⠀⠘⠻⠟⠃⠀⣼⠇⠀⢸⡇⠀⠀",
    r"⠀⠀⢸⡇⠀⠀⠙⢷⣦⣤⣤⣴⡾⠋⠀⠀⢸⡇⠀⠀",
    r"⠀⠀⢸⡇⠀⢸⣇⠀⠀⠉⠉⠀⠀⠀⠀⠀⢸⡇⠀⠀",
    r"⠀⠀⢸⡇⠐⠟⠙⠷⢶⣦⣤⣤⣶⠶⠀⠀⢸⡇⠀⠀",
]


def animate_banner():
    """Typewriter reveal — appears once cleanly."""
    console.clear()

    # print each line with typewriter effect
    for line in PLANKTON_ART:
        console.print(line, style="bold green", justify="center")
        time.sleep(0.05)

    time.sleep(0.3)

    # title appears after art is fully drawn
    title = pyfiglet.figlet_format("PLANKTON", font="small")
    console.print(title, style="bold cyan", justify="center")

    console.print(Panel(
        "[cyan]Secure Drive Sanitisation Tool[/cyan]  •  "
        "[green]Author: dx73r[/green]  •  "
        "[yellow]Version: 1.0[/yellow]",
        border_style="cyan",
        box=box.ROUNDED,
    ), justify="center")
    console.print()


def check_root():
    if os.geteuid() != 0:
        console.print("\n[bold red]ERROR:[/bold red] Plankton must be run as root.")
        console.print("Try: [bold]sudo python3 plankton.py[/bold]\n")
        sys.exit(1)


def get_device_type(device_path):
    """Detect device type — works on both Mac and Linux."""

    # ── Mac (diskutil) ──
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["diskutil", "info", device_path],
                capture_output=True, text=True
            )
            output = result.stdout.lower()

            if "solid state" in output or "ssd" in output:
                if "internal" in output:
                    return "Internal SSD"
                return "External SSD"

            if "rotational" in output or "hard disk" in output or "hdd" in output:
                if "internal" in output:
                    return "Internal HDD"
                return "External HDD"

            if "external" in output or "removable" in output:
                return "USB / External Drive"

            if "nvme" in output:
                return "NVMe SSD"

            if "disk0" in device_path:
                return "Internal Drive"
            else:
                return "External Drive"

        except Exception:
            return "Unknown"

    # ── Linux (/sys/block) ──
    dev_name = os.path.basename(device_path)

    if "nvme" in dev_name:
        return "NVMe SSD"

    try:
        with open(f"/sys/block/{dev_name}/removable", "r") as f:
            if f.read().strip() == "1":
                return "USB / External Drive"
    except FileNotFoundError:
        pass

    try:
        with open(f"/sys/block/{dev_name}/queue/rotational", "r") as f:
            return "Internal HDD" if f.read().strip() == "1" else "Internal SSD"
    except FileNotFoundError:
        pass

    return "Unknown"


def get_device_label(device_path):
    dev_name = os.path.basename(device_path)
    dtype = get_device_type(device_path)
    return f"{dev_name}: {dtype}"


def list_devices():
    console.print("\n[bold cyan]Scanning for devices...[/bold cyan]\n")

    partitions = psutil.disk_partitions(all=False)

    table = Table(
        title="Detected Devices",
        border_style="cyan",
        header_style="bold cyan",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("#",           style="bold white",  width=4)
    table.add_column("Device",      style="bold green",  width=14)
    table.add_column("Label",       style="bold yellow", width=26)
    table.add_column("Mount Point", style="white",       width=20)
    table.add_column("Filesystem",  style="yellow",      width=8)
    table.add_column("Total",       style="cyan",        width=9)
    table.add_column("Used",        style="magenta",     width=9)
    table.add_column("Free",        style="green",       width=9)

    for i, part in enumerate(partitions, start=1):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total = f"{usage.total / (1024**3):.1f} GB"
            used  = f"{usage.used  / (1024**3):.1f} GB"
            free  = f"{usage.free  / (1024**3):.1f} GB"
        except PermissionError:
            total = used = free = "N/A"

        label = get_device_label(part.device)

        table.add_row(
            str(i),
            part.device,
            label,
            part.mountpoint,
            part.fstype,
            total,
            used,
            free,
        )

    console.print(table)
    return partitions


def select_wipe_method():
    methods = {
        "1": {"name": "Zero Fill",           "passes": 1,  "desc": "Single pass of zeros. Fast, basic."},
        "2": {"name": "Random Fill",          "passes": 1,  "desc": "Single pass of random data."},
        "3": {"name": "DoD 5220.22-M Short",  "passes": 3,  "desc": "Zero, One, Random."},
        "4": {"name": "DoD 5220.22-M Full",   "passes": 7,  "desc": "Full US DoD standard."},
        "5": {"name": "Schneier 7-pass",      "passes": 7,  "desc": "Bruce Schneier's method."},
        "6": {"name": "Gutmann 35-pass",      "passes": 35, "desc": "Maximum security. Very slow."},
    }

    table = Table(
        title="Wipe Methods",
        border_style="cyan",
        header_style="bold cyan",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("#",           style="bold white",  width=4)
    table.add_column("Method",      style="bold yellow", width=22)
    table.add_column("Passes",      style="cyan",        width=8, justify="center")
    table.add_column("Description", style="white",       width=35)

    for key, method in methods.items():
        table.add_row(key, method["name"], str(method["passes"]), method["desc"])

    console.print(table)

    choice = Prompt.ask(
        "\n[bold cyan]Select wipe method[/bold cyan] (or [bold red]b[/bold red] to go back)",
        default="b"
    )

    if choice.lower() == "b":
        return None
    if choice in methods:
        return methods[choice]

    console.print("[red]Invalid choice.[/red]")
    return None


def _get_passes(method_name):
    Z = lambda size: bytes(size)        # zeros
    O = lambda size: b'\xff' * size     # ones
    R = lambda size: os.urandom(size)   # random

    passes = {
        "Zero Fill":           [("Zero",   Z)],
        "Random Fill":         [("Random", R)],
        "DoD 5220.22-M Short": [("Zero",   Z), ("Ones", O), ("Random", R)],
        "DoD 5220.22-M Full":  [("Zero",   Z), ("Ones", O), ("Random", R),
                                ("Zero",   Z), ("Ones", O), ("Random", R), ("Zero", Z)],
        "Schneier 7-pass":     [("Ones",   O), ("Zero", Z), ("Random", R),
                                ("Random", R), ("Random", R), ("Random", R), ("Random", R)],
        "Gutmann 35-pass":     [("Random", R)] * 4 +
                               [("Zero",   Z), ("Ones", O), ("Random", R)] * 9 +
                               [("Random", R)] * 4,
    }

    return passes.get(method_name, [("Random", R)])


def wipe_device(partition, method):
    device = partition.device

    console.print(Panel(
        f"[bold]Device:[/bold]  [green]{device}[/green]  ({get_device_label(device)})\n"
        f"[bold]Method:[/bold]  [yellow]{method['name']}[/yellow]  ({method['passes']} pass(es))\n\n"
        f"[bold red]ALL DATA WILL BE PERMANENTLY DESTROYED.[/bold red]",
        title="[bold red]⚠  WARNING[/bold red]",
        border_style="red",
    ))

    confirm = Prompt.ask(
        f"\n[bold]Type the device name [cyan]{device}[/cyan] to confirm[/bold]"
    )

    if confirm.strip() != device:
        console.print("\n[green]Operation cancelled.[/green]")
        return False

    console.print(f"\n[bold cyan]Starting wipe on {device}...[/bold cyan]\n")

    try:
        device_size = os.path.getsize(device)
        if device_size == 0:
            fd = os.open(device, os.O_RDONLY)
            device_size = os.lseek(fd, 0, os.SEEK_END)
            os.close(fd)

        chunk_size = 4 * 1024 * 1024
        passes = _get_passes(method["name"])

        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="green"),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            for pass_num, (label, data_fn) in enumerate(passes, start=1):
                task = progress.add_task(
                    f"Pass {pass_num}/{len(passes)} — {label}",
                    total=device_size
                )
                fd = os.open(device, os.O_WRONLY | os.O_SYNC)
                try:
                    written = 0
                    while written < device_size:
                        remaining = device_size - written
                        chunk = data_fn(min(chunk_size, remaining))
                        os.write(fd, chunk)
                        written += len(chunk)
                        progress.update(task, completed=written)
                    os.fsync(fd)
                finally:
                    os.close(fd)

        console.print(Panel(
            f"[bold green]Wipe completed successfully![/bold green]\n\n"
            f"[bold]Device:[/bold]  [cyan]{device}[/cyan]\n"
            f"[bold]Method:[/bold]  [yellow]{method['name']}[/yellow]\n"
            f"[bold]Passes:[/bold]  {method['passes']}",
            title="[bold green]✔  Done[/bold green]",
            border_style="green",
        ))
        return True

    except PermissionError:
        console.print("\n[bold red]Permission denied. Run as root (sudo).[/bold red]")
        return False
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        return False


def main_menu():
    while True:
        console.print("\n[bold cyan]━━━━━━━━━━━━━━━━ Main Menu ━━━━━━━━━━━━━━━━[/bold cyan]\n")
        console.print("  [bold green]1[/bold green] — Scan devices")
        console.print("  [bold green]2[/bold green] — Wipe a device")
        console.print("  [bold red]q[/bold red] — Quit\n")

        choice = Prompt.ask("[bold]Enter choice[/bold]")

        if choice == "1":
            list_devices()

        elif choice == "2":
            partitions = list_devices()
            if not partitions:
                console.print("[red]No devices found.[/red]")
                continue

            device_choice = Prompt.ask(
                "\n[bold cyan]Select device number[/bold cyan] (or [bold red]b[/bold red] to go back)",
                default="b"
            )
            if device_choice.lower() == "b":
                continue
            try:
                selected = partitions[int(device_choice) - 1]
            except (IndexError, ValueError):
                console.print("[red]Invalid device selection.[/red]")
                continue

            method = select_wipe_method()
            if not method:
                continue

            wipe_device(selected, method)

        elif choice.lower() == "q":
            console.print("\n[bold cyan]Goodbye![/bold cyan]\n")
            break

        else:
            console.print("\n[red]Invalid choice, try again.[/red]")


if __name__ == "__main__":
    #check_root()
    animate_banner()
    main_menu()