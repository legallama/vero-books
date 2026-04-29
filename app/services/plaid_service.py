import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from flask import current_app
from datetime import datetime, timedelta

class PlaidService:
    @staticmethod
    def get_client():
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox if current_app.config['PLAID_ENV'] == 'sandbox' else plaid.Environment.Development,
            api_key={
                'clientId': current_app.config['PLAID_CLIENT_ID'],
                'secret': current_app.config['PLAID_SECRET'],
            }
        )
        api_client = plaid.ApiClient(configuration)
        return plaid_api.PlaidApi(api_client)

    @staticmethod
    def create_link_token(user_id, org_id):
        client = PlaidService.get_client()
        
        request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            country_codes=[CountryCode('US')],
            language='en',
            client_name='VeroBooks',
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id))
        )
        
        response = client.link_token_create(request)
        return response.to_dict()['link_token']

    @staticmethod
    def exchange_public_token(public_token):
        client = PlaidService.get_client()
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(request)
        return response.to_dict() # access_token, item_id

    @staticmethod
    def get_transactions(access_token, start_date, end_date):
        client = PlaidService.get_client()
        
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions()
        )
        
        response = client.transactions_get(request)
        return response.to_dict()['transactions']
