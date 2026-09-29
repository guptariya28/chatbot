import socket

host = "://azure.com"

try:
    print(f"Testing DNS resolution for {host}...")
    ip = socket.gethostbyname(host)
    print(f"Success! Server IP address is: {ip}")
except socket.gaierror as e:
    print(f"\n❌ Connection Blocked: Your computer cannot find this server on the internet.")
    print(f"Error Details: {e}")
    print("\nPlease verify that the Server Name is spelled correctly in the Azure Portal.")
