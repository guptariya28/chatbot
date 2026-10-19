Step 1 — Verify the Cloud Connector mapping
Open the Cloud Connector administration UI and navigate to Cloud To On-Premise → Access Control.

Check the existing HANA mapping:
Setting	What you need
BTP subaccount	The same subaccount associated with your BAS environment
Internal host	Actual HANA VM hostname/IP reachable from Cloud Connector
Internal port	Actual HANA SQL port
Virtual host	mdd
Virtual port	The mapped port that the client must use
Status	Mapping and internal host should be reachable
SAP's Configure Access Control (TCP) guide explains each of these fields and the internal-host reachability check.


Important: If the mapping uses TCP or TCP TLS, do not assume the protocol setting means BAS can directly connect to the virtual host. It configures the backend mapping; the client still needs a supported connectivity route.
Step 2 — Confirm the BTP subaccount and destination
Ask your BTP administrator to confirm:
- Cloud Connector is connected to the intended subaccount.
- The BAS subscription and destination are associated with the correct subaccount.
- The destination points to the intended virtual host and port.
- The destination type and proxy settings match the intended protocol.
SAP's BAS — Access On Premise Systems documentation describes this destination setup for the built-in web proxy. 


If the destination was created after your dev space started, reload its destination configuration:
curl http://localhost:8887/reload


This refreshes the destinations used by BAS's built-in proxy. It does not create a generic TCP tunnel for hdbcli. 

Step 3 — Choose the actual Python-to-HANA connection method
For hdbcli, you need a TCP connection. SAP's Connectivity documentation confirms that TCP is supported for cloud-to-on-premises communication, but the client must use the appropriate connectivity mechanism. 


You have two realistic paths:

Option A — Run Python directly in BAS

First, ask your administrator whether the BAS dev space has an approved TCP route to the HANA VM. If your company provides direct network access, use the hostname and port that are reachable from BAS.

Test hostname resolution:
python -c "import socket; print(socket.getaddrinfo('mdd', None))"


printenv \| grep -i -E 'destination\|connectivity\|proxy'	Displays environment variables related to proxies and connectivity.	BAS has a local proxy configured at 127.0.0.1:8887.
python -c "import socket; print(socket.getaddrinfo('mdd', None))"	Checks whether Python can resolve mdd as a hostname.	Failed with Name or service not known; normal hostname resolution does not recognize mdd.
curl -i http://localhost:8887/	Sends an HTTP request to the local BAS proxy and displays the response headers and body.	The proxy responds with 200 OK and identifies itself as the On Premise Web Proxy.
curl -i http://localhost:8887/reload	Requests the BAS proxy to reload its destination configuration.	It returned Destination reloaded..., confirming the reload endpoint responded successfully. It does not prove a HANA destination exists.


##things to know
Step 1 — What needs to be configured in the cloud?
Ask your SAP BTP administrator to configure the following items.
Step 2 — Configure the Cloud Connector
Your SAP administrator must open the Cloud Connector administration UI and check the existing mapping.
1. Open Cloud To On-Premises → Access Control.
2. Find the mapping for virtual host mdd.
3. Confirm the internal HANA hostname/IP and SQL port are correct.
4. Confirm the protocol is TCP or TCP TLS, as appropriate for the HANA connection.
5. Confirm the mapping is connected and that Cloud Connector can reach the internal HANA server.
SAP's guide: Configure TCP access control. The virtual host can be an alias; it does not have to be a real domain. 


Step 3 — Configure SAP BTP
Your administrator must open SAP BTP Cockpit and:
1. Open the correct Global Account → Subaccount linked to the Cloud Connector.
2. Open Connectivity → Cloud Connectors and confirm the Cloud Connector is connected to that subaccount.
3. Open Connectivity → Destinations and check whether a destination already exists for HANA.
4. If one is needed, configure it using the appropriate supported connection method, the virtual host mdd, the mapped virtual port, and the required authentication settings.
5. If your Python application will run in Cloud Foundry, confirm the required Connectivity service and, if needed, Destination service instances are created and bound to the application.
SAP explains that on-premises connectivity uses the Cloud Connector together with the appropriate BTP connectivity configuration. 


Step 4 — Decide where Python will run
This is the important part:
- If Python must run directly in the BAS terminal: the administrator must confirm that your BAS environment has an approved route for raw TCP to HANA. The existing local web proxy does not prove this.
- If direct access is unavailable: use an approved application environment with a supported connectivity setup. Do not assume that creating an ordinary HTTP destination makes hdbcli work.
