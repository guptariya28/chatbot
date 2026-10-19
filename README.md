1. How to verify the Cloud Connector mapping
Ask the administrator to open the Cloud Connector Administration UI.
1. Open Cloud To On-Premise → Access Control.
2. Find the entry whose Virtual Host is mdd.
3. Check the Internal Host, Internal Port, Virtual Port, and protocol columns.
4. Confirm the mapping is accessible and that the Cloud Connector is connected to the correct BTP subaccount.
How will they know it works? The mapping exists, the connector is connected, and the internal HANA endpoint is reachable from the connector machine. The screen alone does not prove that Python in BAS can connect.

2. How to verify the BTP connection
In SAP BTP Cockpit, the administrator should:
1. Open the relevant subaccount.
2. Go to Connectivity → Cloud Connectors.
3. Check that the expected Cloud Connector appears and is connected.
If it is missing or disconnected, the administrator must investigate the subaccount registration or connector connection. SAP documents this relationship in its Cloud Connector TCP configuration guide. 

3. How to verify the destination
The administrator should open Connectivity → Destinations in that same subaccount and check whether a destination for the on-premises system exists.
- If it exists, inspect its URL, proxy type, and configuration.
- If it doesn't exist, determine whether one is needed and create it for the intended connection method.
SAP BAS uses configured destinations for its built-in on-premises web proxy. Your successful curl to localhost:8887 only proves the local proxy responds; it does not prove a HANA destination is configured. 


4. How to verify Python can connect
This requires a separate test. Ask the administrator:
“Is raw TCP connectivity to the HANA SQL port supported from my BAS terminal, or do I need to run Python in a deployed application using SAP BTP Connectivity?”
