from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import logging
import daphne
from hypercorn.config import Config
from hypercorn.asyncio import serve
from bc_nav_connector import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# Mock credentials for authentication - Only for 
VALID_CREDENTIALS = {
    "Tenwekcred": "2025#@Tenwek"  
}

def validate_headers(headers_data):
    """Validate required headers"""
    required_fields = ['serviceName', 'messageID', 'connectionID', 'connectionPassword']
    
    for field in required_fields:
        if field not in headers_data:
            return False, f"Missing required header field: {field}"
    
    # Validate credentials
    connection_id = headers_data.get('connectionID')
    connection_password = headers_data.get('connectionPassword')
    
    if connection_id not in VALID_CREDENTIALS:
        return False, "Invalid connectionID"
    
    if VALID_CREDENTIALS[connection_id] != connection_password:
        return False, "Invalid connectionPassword"
    
    return True, "Valid headers"

def create_error_response(message_id, status_code, status_description):
    """Create standardized error response"""
    return {
        "header": {
            "messageID": message_id or str(uuid.uuid4()),
            "statusCode": str(status_code),
            "statusDescription": status_description
        },
        "response": {}
    }

@app.route('/api/v1/account', methods=['POST'])
def validate_account():
    """B2B Validation Interface - getAccountValidation for Tenwek college students"""
    try:
        # Parse request JSON
        data = request.get_json()
        
        if not data:
            return jsonify(create_error_response(None, 400, "Invalid JSON payload")), 400
        
        # Extract header and request data
        header = data.get('header', {})
        request_data = data.get('request', {})
        
        # Validate headers
        is_valid, validation_message = validate_headers(header)
        if not is_valid:
            return jsonify(create_error_response(
                header.get('messageID'), 401, validation_message
            )), 401
        
        # Validate required request fields
        required_fields = ['TransactionReferenceCode', 'TransactionDate', 'InstitutionCode']
        for field in required_fields:
            if field not in request_data:
                return jsonify(create_error_response(
                    header.get('messageID'), 400, f"Missing required field: {field}"
                )), 400
        
        transaction_ref = request_data['TransactionReferenceCode']
        transaction_date = request_data['TransactionDate']
        institution_code = request_data['InstitutionCode']
        #amount = request_data["TotalAmount"]
        
        logger.info(f"Validating sacco member: {transaction_ref}")
        
        # Check if sacco member exists in our mock database
        validation_response = BusinessCentral.ValidateStudent(transaction_ref)
        print(f"Final valida")
        if validation_response!= "":
            member = BusinessCentral.GetStudentName(validation_response)
            
            
            
            # Create successful response
            response = {
                "header": {
                    "messageID": header.get('messageID'),
                    "statusCode": "200",
                    "statusDescription": "Successfully validated sacco member"
                },
                "response": {
                    "TransactionReferenceCode": transaction_ref,
                    "TransactionDate": transaction_date,
                    "TotalAmount": 0.0,
                    "Currency": "",
                    "AdditionalInfo": member['name'],
                    "AccountNumber": transaction_ref,
                    "AccountName": member['name'],
                    "InstitutionCode": institution_code,
                    "InstitutionName": "Tenwek Hospital"
                }
            }
            
            logger.info(f"Successfully validated Tenwek hospital college student: {member['name']}. ")
            return jsonify(response), 200
        
        else:
            # Member not found
            return jsonify(create_error_response(
                header.get('messageID'), 404, "college student not found"
            )), 404
            
    except Exception as e:
        logger.error(f"Error in validate_account: {str(e)}")
        return jsonify(create_error_response(
            None, 405, "A severe problem has occurred"
        )), 500

@app.route('/api/v1/advise', methods=['POST'])
def payment_advice():
    """B2B Payment Advice Interface - sendAccountPaymentAdvise for Sacco Members"""
    try:
        # Parse request JSON
        data = request.get_json()
        
        if not data:
            return jsonify(create_error_response(None, 400, "Invalid JSON payload")), 400
        
        # Extract header and request data
        header = data.get('header', {})
        request_data = data.get('request', {})
        
        # Validate headers
        is_valid, validation_message = validate_headers(header)
        if not is_valid:
            return jsonify(create_error_response(
                header.get('messageID'), 401, validation_message
            )), 401
        
        # Validate required request fields
        required_fields = [
            'TransactionReferenceCode', 'TransactionDate', 'TotalAmount',
            'DocumentReferenceNumber', 'PaymentDate', 'PaymentAmount',
            'AccountNumber', 'InstitutionCode'
        ]
        
        for field in required_fields:
            if field not in request_data:
                return jsonify(create_error_response(
                    header.get('messageID'), 400, f"Missing required field: {field}"
                )), 400
        
        transaction_ref = request_data['TransactionReferenceCode']
        document_ref = request_data['DocumentReferenceNumber']
        total_amount = request_data['TotalAmount']
        payment_amount = request_data['PaymentAmount']
        
        logger.info(f"Processing payment advice for: {document_ref}, Amount: {total_amount}")
        
        # Validate amounts match
        if total_amount != payment_amount:
            return jsonify(create_error_response(
                header.get('messageID'), 400, "TotalAmount and PaymentAmount must match"
            )), 400
        
        # Check if document reference exists (sacco member exists)
        #if document_ref not in MOCK_MEMBERS:
        if BusinessCentral.ValidateStudent(document_ref) =="":
            return jsonify(create_error_response(
                header.get('messageID'), 404, "Tenwek College student reference not found"
            )), 404
        update_result = BusinessCentral.insertcoopdeposit(transaction_ref,document_ref,payment_amount)
        if update_result != 'TRUE':
            return jsonify(create_error_response(
            None, 405, f"A severe problem has occurred: {update_result}"
        )), 500
        # Simple duplicate check - in production, store processed transactions
        # For now, we'll just log and accept all transactions
        
        # Create successful response
        response = {
            "header": {
                "messageID": header.get('messageID'),
                "statusCode": "200",
                "statusDescription": "Payment successfully received"
            },
            "response": {
                "TransactionReferenceCode": transaction_ref,
                "TransactionDate": request_data['TransactionDate'],
                "TransactionAmount": total_amount,
                "AccountNumber": request_data['AccountNumber'],
                "AccountName": request_data.get('AccountName', ''),
                "InstitutionCode": request_data['InstitutionCode'],
                "InstitutionName": request_data.get('InstitutionName', '')
            }
        }
        
        logger.info(f"Successfully processed payment advice: {transaction_ref}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in payment_advice: {str(e)}")
        return jsonify(create_error_response(
            None, 405, "A severe problem has occurred"
        )), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Tenwek Hospital College B2B API"
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "header": {
            "messageID": str(uuid.uuid4()),
            "statusCode": "404",
            "statusDescription": "The task/operation does not exist"
        },
        "response": {}
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "header": {
            "messageID": str(uuid.uuid4()),
            "statusCode": "405",
            "statusDescription": "Method not allowed"
        },
        "response": {}
    }), 405

if __name__ == '__main__':
    config = Config()
    config.bind = ["127.0.0.1:55812"]  # Bind to your IP address and port

    # Serve the app using Hypercorn (Daphne server alternative)
    import asyncio
    from hypercorn.asyncio import serve

# Running the app with Daphne (via hypercorn)
if __name__ == '__main__':
    config = Config()
    config.bind = ["127.0.0.1:55812"]  # Bind to your IP address and port

    # Serve the app using Hypercorn (Daphne server alternative)
    import asyncio
    from hypercorn.asyncio import serve

    asyncio.run(serve(app, config))
