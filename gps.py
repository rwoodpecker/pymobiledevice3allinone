import subprocess
import re
import sys
import time
import signal

def start_rsd_tunnel():
    print("[*] Starting RSD tunnel...")
    proc = subprocess.Popen(
        ["sudo", "python3", "-m", "pymobiledevice3", "lockdown", "start-tunnel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    host, port = None, None

    for line in proc.stdout:
        print("[TUNNEL]", line.strip())
        if "RSD Address:" in line:
            match = re.search(r'RSD Address:\s*([\w:]+)', line)
            if match:
                host = match.group(1)
        elif "RSD Port:" in line:
            match = re.search(r'RSD Port:\s*(\d+)', line)
            if match:
                port = match.group(1)
        if host and port:
            print(f"[+] Tunnel ready: {host}:{port}")
            return proc, host, port

    print("[!] Failed to extract RSD tunnel info.")
    proc.kill()
    sys.exit(1)

def stop_rsd_tunnel(proc):
    print("[*] Stopping RSD tunnel...")
    try:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=5)
        print("[+] Tunnel stopped.")
    except Exception as e:
        proc.kill()
        print("[!] Tunnel force killed due to:", e)

def set_gps_location(host, port, lat, lon):
    print(f"[*] Setting GPS location to Latitude: {lat}, Longitude: {lon}...")
    try:
        subprocess.run([
            "pymobiledevice3", "developer", "dvt", "simulate-location", "set",
            "--rsd", host, port,
            "--", str(lat), str(lon)
        ], check=True)
        print("[+] Location successfully set.")
    except subprocess.CalledProcessError as e:
        print("[!] Failed to set location:", e)
        sys.exit(1)

def parse_input(args):
    joined = ' '.join(args).strip().replace('\n', '').replace('\r', '')
    joined = joined.replace(',', ' ')
    parts = joined.split()

    if len(parts) != 2:
        print("[!] Invalid input. Provide: LAT,LON or LAT LON")
        sys.exit(1)

    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return lat, lon
    except ValueError:
        print("[!] Invalid coordinates:", parts)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: sudo python3 {sys.argv[0]} <LAT,LON> or <LAT LON>")
        sys.exit(1)

    lat, lon = parse_input(sys.argv[1:])
    proc = None

    try:
        proc, host, port = start_rsd_tunnel()
        time.sleep(1)
        set_gps_location(host, port, lat, lon)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
    finally:
        if proc:
            stop_rsd_tunnel(proc)

if __name__ == "__main__":
    main()
