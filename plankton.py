#!/usr/bin/env python3
"""
Plankton - Secure Drive Sanitisation Tool
Author: dx73r
"""

#importing required libraries
import os, sys
from rich.console import Console
from rich.panel import Panel
import pyfiglet


#constructors of the classes
console = Console()




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



if __name__ == "__main__":
    
    #check_root()
    display_banner()
    
