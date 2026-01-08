#!/usr/bin/env python3

import requests
import json
import time

# ============ 配置区（只需改这里）============
API_TOKEN = "你的_API_TOKEN_在这里"          # Edit zone DNS 权限的 Token
ZONE_ID   = "你的_Zone_ID_在这里"            # Cloudflare 域名 Overview 页面找

# 要更新的子域名列表（子域名部分，如 "home", "nas"）
SUBDOMAINS = ["home", "nas", "vpn"]

MAIN_DOMAIN = "example.com"                  # 你的主域名（如 example.com）

PROXIED = False                              # False = DNS Only（家用推荐），True = 橙色云代理
TTL = 300                                    # TTL 秒数，推荐 300

UPDATE_IPV4 = True                           # 是否更新 A 记录
UPDATE_IPV6 = True                           # 是否更新 AAAA 记录（没 IPv6 改 False）

# 获取公网 IP 的服务（可靠）
IPV4_URL = "https://v4.ident.me"                     #  "https://api.ipify.org"
IPV6_URL = "https://api64.ipify.org"
# ===========================================

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

API_BASE = "https://api.cloudflare.com/client/v4"

def get_current_ips():
    ipv4 = None
    ipv6 = None
    if UPDATE_IPV4:
        try:
            ipv4 = requests.get(IPV4_URL).text.strip()
        except:
            print("获取 IPv4 失败")
    if UPDATE_IPV6:
        try:
            ipv6 = requests.get(IPV6_URL).text.strip()
        except:
            print("获取 IPv6 失败")
    return ipv4, ipv6

def get_dns_records(record_type):
    url = f"{API_BASE}/zones/{ZONE_ID}/dns_records"
    params = {"type": record_type, "per_page": 100}
    resp = requests.get(url, headers=HEADERS, params=params)
    data = resp.json()
    if not data["success"]:
        raise Exception(f"API 错误: {data['errors']}")
    return data["result"]

def update_or_create_record(name, record_type, ip):
    fqdn = f"{name}.{MAIN_DOMAIN}" if name != "@" else MAIN_DOMAIN
    records = get_dns_records(record_type)
    
    # 找匹配的记录
    existing = None
    for rec in records:
        if rec["name"] == fqdn:
            existing = rec
            break
    
    data = {
        "type": record_type,
        "name": fqdn,
        "content": ip,
        "ttl": TTL,
        "proxied": PROXIED
    }
    
    if existing:
        if existing["content"] == ip:
            print(f"{fqdn} ({record_type}) 无变化: {ip}")
            return
        # 更新
        url = f"{API_BASE}/zones/{ZONE_ID}/dns_records/{existing['id']}"
        resp = requests.patch(url, headers=HEADERS, json=data)
    else:
        # 创建
        url = f"{API_BASE}/zones/{ZONE_ID}/dns_records"
        resp = requests.post(url, headers=HEADERS, json=data)
    
    result = resp.json()
    if result["success"]:
        action = "更新" if existing else "创建"
        print(f"{action} {fqdn} ({record_type}) -> {ip}")
    else:
        print(f"失败 {fqdn}: {result['errors']}")

def main():
    print(f"开始检查 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    ipv4, ipv6 = get_current_ips()
    
    for sub in SUBDOMAINS:
        if UPDATE_IPV4 and ipv4:
            update_or_create_record(sub, "A", ipv4)
        if UPDATE_IPV6 and ipv6:
            update_or_create_record(sub, "AAAA", ipv6)

if __name__ == "__main__":
    main()
