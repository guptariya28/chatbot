import socket
import threading
import os
import time
 
def get_proxy_config():
    """Get proxy config from environment"""
    proxy_url = os.getenv('DESTINATION_PROXY_URL', '')
    # Parse http://secure-outbound-connectivity.webide-system.eu10.hana.ondemand.com
    if '://' in proxy_url:
        proxy_url = proxy_url.split('://')[1]
    if ':' in proxy_url:
        host, port = proxy_url.split(':')
        return host, int(port)
    return proxy_url, 80
 
def handle_client(client_socket, target_host, target_port, proxy_host, proxy_port):
    """Handle connection through HTTP CONNECT proxy"""
    try:
        # Connect to SAP proxy
        proxy = socket.create_connection((proxy_host, proxy_port), timeout=10)
        
        # Send HTTP CONNECT to reach mdd:30015
        connect_req = (
            f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
            f"Host: {target_host}:{target_port}\r\n"
            f"Proxy-Connection: keep-alive\r\n"
            f"\r\n"
        )
        proxy.sendall(connect_req.encode())
        
        # Read proxy response
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = proxy.recv(4096)
            if not chunk:
                break
            response += chunk
        
        print(f"Proxy response: {response.split()[0] if response else 'No response'}")
        
        if b"200" in response.split(b"\r\n")[0]:
            print(f"✅ Tunnel established: localhost:30015 -> {target_host}:{target_port}")
            
            # Bidirectional forwarding
            def forward(src, dst):
                try:
                    while True:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.sendall(data)
                except:
                    pass
                finally:
                    src.close()
                    dst.close()
            
            # Start forwarding in both directions
            threading.Thread(target=forward, args=(client_socket, proxy), daemon=True).start()
            forward(proxy, client_socket)
        else:
            print(f"❌ Proxy rejected connection: {response}")
            client_socket.close()
            
    except Exception as e:
        print(f"❌ Tunnel error: {e}")
        client_socket.close()
 
def start_tunnel(target_host='mdd', target_port=30015, local_port=30015):
    """Start local tunnel to target via SAP proxy"""
    proxy_host, proxy_port = get_proxy_config()
    print(f"Using proxy: {proxy_host}:{proxy_port}")
    print(f"Target: {target_host}:{target_port}")
    print(f"Local: localhost:{local_port}")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', local_port))
    server.listen(5)
    
    print(f"🚀 Tunnel listening on 127.0.0.1:{local_port}")
    print("Keep this running while you connect to HANA")
    
    while True:
        try:
            client, addr = server.accept()
            print(f"New connection from {addr}")
            threading.Thread(
                target=handle_client, 
                args=(client, target_host, target_port, proxy_host, proxy_port),
                daemon=True
            ).start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Accept error: {e}")
 
if __name__ == "__main__":
    # Test the tunnel
    start_tunnel()
 
