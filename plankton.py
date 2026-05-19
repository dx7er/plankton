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


def main_menu():
    pass



def wipe_device(partition, method):
    device = partition.device
    console.print(f"\n[bold red]WARNING:[/bold red] This will permanently erase [bold]{device}[/bold]")
    console.print(f"[bold]Method:[/bold] {method['name']} — {method['passes']} pass(es)\n")
    confirm = Prompt.ask(f"[bold]Type the device name [cyan]{device}[/cyan] to confirm[/bold]")
    
    if confirm.strip() != device:
        console.print("\n[green]Operation cancelled.[/green]\n")
        return False







if __name__ == "__main__":
    
    #check_root()
    #display_banner()
    list_drives()
    dev=Prompt.ask("Enter the device name to wipe (e.g. /dev/sdb)")
    console.print(f"You entered: {dev}")


