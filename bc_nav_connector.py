# business_central.py
import base64
from zeep import Client
from zeep.transports import Transport
# from requests_ntlm import HttpNtlmAuth
from requests.auth import HTTPBasicAuth
from datetime import datetime
import os
from requests import Session
import json


# test_wsdl_url = "http://80.240.200.6:21047/BC210/WS/COPY%20OF%20LIVE(USERNAME%20SACCO)/Codeunit/MobileAppIntergration"
wsdl_url = "http://ctc-navapp-svr.tenwekctc.local:8047/Tenwek/WS/CTC%20Accounts/Codeunit/coop_integration_2"
bc_username = "navadmin"
bc_password = "Tenwek@2021"

class BusinessCentral:
    
    @staticmethod
    def create_soap_client(wsdl_url):
        # Set up a session with authentication
        session = Session()
        session.auth = HTTPBasicAuth(bc_username, bc_password)
        session.verify = False  # Disable SSL verification for testing
        
        # Configure the transport with the session
        transport = Transport(session=session)
        
        # Initialize the SOAP client
        client = Client(wsdl_url, transport=transport)
        return client

    

    @staticmethod
    def insertCoopDeposit(documentno,accountNo,amount):
     
        try:
            client = BusinessCentral.create_soap_client(wsdl_url)
            result = client.service.insertcoopdeposit(documentno=documentno,acountNo=accountNo,keyword=accountNo[:3],amount = amount)
            print(f"Update Results: {result}")
            return result
        except Exception as e:
            print(f"Error: {e}")
        
    
    @staticmethod
    def Validate_Student(StudentNo):
        try:
            client = BusinessCentral.create_soap_client(wsdl_url)
            response = client.service.Validate_Student(StudentNo)
            print(f"Validation response: {response}")
            if len(response) > 20 or len(response) < 3:
                return ""
            return response
        except Exception as e:
            print(f"Error: {e}")
            return ""

    @staticmethod
    def PostCOOPDeposit():
        try:
            client = BusinessCentral.create_soap_client(wsdl_url)
            response = client.service.Post_COOP_Deposit()
            return response
        except Exception as e:
            print(f"An error occured: {e}")
            return "An error occured:{e}"
      
    @staticmethod
    def GetStudentName(memberno):
        try:
            print(f"Member No: {memberno}")
            client = BusinessCentral.create_soap_client(wsdl_url)
            response = client.service.GetStudentName(StudentNo=memberno)
            print("Response: ", response)
            if response is None:
                return None
            data = {}
            count = 1
            for item in response.split('.:'):
                if count == 1:
                    data.update({"StudentNo": item})
                if count == 2:
                    data.update({"Name": item})  
                # if count == 3:
                #     data.update({"email": item})
                # if count == 4:
                #     data.update({"status": item})
                # if count == 5:
                #     data.update({"category": item})
                # if count == 6:
                #     data.update({"phone": item})
                # if count == 7:
                #     data.update({"id_no": item})
                # if count == 8:
                #     data.update({"fosa": item})
                # if count == 9:
                #     data.update({"mobile_defaulter": item})
                # if count == 10:
                #     data.update({"defaulter": item})
                # if count == 11:
                #     data.update({"fosa_bal": item})
                count += 1
            return data
        except Exception as e:
            print(f"Error fetching member details: {e}")
            return None

def humanize_float(value, decimal_places=2):
    """
    Formats a float value to be more human-readable.
    
    Args:
        value: The float value to format
        decimal_places: Number of decimal places to round to (default: 2)
    
    Returns:
        A formatted string representation of the float
    """
    if value is None:
        return "N/A"
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    rounded = round(float_value, decimal_places)
    
    if rounded == int(rounded):
        formatted = f"{int(rounded):,}"
    else:
        formatted = f"{rounded:,}"
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
    
    return formatted
