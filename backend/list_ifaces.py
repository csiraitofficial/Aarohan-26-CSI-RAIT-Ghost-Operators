from scapy.arch.windows import get_windows_if_list
for i in get_windows_if_list():
    print(f"{i.get('name')} -> {i.get('description')}")
