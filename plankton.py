#!/usr/bin/env python3
"""
Plankton - Secure Drive Sanitisation Tool
Author: dx73r
"""

#importing libs
import os, sys, psutil
import pyfiglet
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn


#constructors
console = Console()


#functions
def display_banner():
    banner = pyfiglet.figlet_format("Plankton", font="slant")
    console.print("\n\n", banner, style="bold cyan", justify="center")
    console.print(Panel(
        "Secure Drive Sanitisation Tool\nAuthor: dx73r\nversion: 1.0", 
        style="cyan", border_style="cyan"), 
        justify="center")


def check_root():
    if os.geteuid() != 0:
        console.print("\nError: Plankton must be run as root!\n", style="bold red")
        console.print("Try: sudo python3 plankton.py\n", style="bold")
        sys.exit(1)



def list_drives():
    console.print("\nScanning for block devices...", style="bold cyan")
    partitions = psutil.disk_partitions(all=False)
    
    table = Table(title="Detected Devices", border_style="cyan", header_style="bold cyan")
    table.add_column("#",          style="bold white",  width=4)
    table.add_column("Device",     style="bold green",  width=15)
    table.add_column("Mount Point", style="white",      width=20)
    table.add_column("File System", style="yellow",     width=10)
    table.add_column("Total Size",  style="cyan",       width=12)
    table.add_column("Used",        style="magenta",    width=12)
    table.add_column("Free",        style="green",      width=12)
    
    for idx, part in enumerate(partitions, start=1):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total = f"{usage.total / (1024**3):.2f} GB"
            used  = f"{usage.used / (1024**3):.2f} GB"
            free  = f"{usage.free / (1024**3):.2f} GB"
        except Exception as e:
            total = used = free = "N/A"
            
        table.add_row(
            str(idx),
            part.device,
            part.mountpoint,
            part.fstype,
            total,
            used,
            free,
        )
    console.print(table)
    return partitions



def _get_passes(method_name):
    
    Z = lambda size: bytes(size)             # zeros
    O = lambda size: b'\xff' * size          # ones  
    R = lambda size: os.urandom(size)        # random

    passes = {
        "Zero Fill":          [("Zero",   Z)],
        "Random Fill":        [("Random", R)],
        "DoD 5220.22-M Short":[("Zero",   Z), ("Ones", O), ("Random", R)],
        "DoD 5220.22-M Full": [("Zero",   Z), ("Ones", O), ("Random", R),
                               ("Zero",   Z), ("Ones", O), ("Random", R), ("Zero", Z)],
        "Schneier 7-pass":    [("Ones",   O), ("Zero", Z), ("Random", R),
                               ("Random", R), ("Random", R), ("Random", R), ("Random", R)],
        "Gutmann 35-pass":    [("Random", R)] * 4 +
                              [("Zero",   Z), ("Ones", O), ("Random", R)] * 9 +
                              [("Random", R)] * 4,
    }

    return passes.get(method_name, [("Random", R)])



def wipe_device(partition, method):
    device = partition.device

    console.print(f"\n[bold red]WARNING:[/bold red] This will permanently erase [bold]{device}[/bold]")
    console.print(f"[bold]Method:[/bold] {method['name']} — {method['passes']} pass(es)\n")

    confirm = Prompt.ask(f"[bold]Type the device name [cyan]{device}[/cyan] to confirm[/bold]")

    if confirm.strip() != device:
        console.print("\n[green]Operation cancelled.[/green]")
        return False

    console.print(f"\n[bold cyan]Starting wipe on {device}...[/bold cyan]\n")

    try:
        # get device size
        device_size = os.path.getsize(device)
        if device_size == 0:
            fd = os.open(device, os.O_RDONLY)
            device_size = os.lseek(fd, 0, os.SEEK_END)
            os.close(fd)

        chunk_size = 4 * 1024 * 1024  # 4MB chunks

        passes = _get_passes(method["name"])

        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=40),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console
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

        console.print(f"\n[bold green]Wipe completed on {device}[/bold green]")
        return True

    except PermissionError:
        console.print("\n[bold red]Permission denied. Run as root (sudo).[/bold red]")
        return False
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        return False









if __name__ == "__main__":
    
    #check_root()
    #display_banner()
    list_drives()
    dev=Prompt.ask("Enter the device name to wipe (e.g. /dev/sdb)")
    console.print(f"You entered: {dev}")


