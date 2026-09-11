"""Exact-order, proxy-only reads/cancellations for pending-order expiry.

This module never places or modifies an order and never refreshes login tokens.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation
import re
from zoneinfo import ZoneInfo

import requests
from django.utils.dateparse import parse_datetime
from main.broker_registry import normalize_broker_name
from main.brokers.utils import get_access_token

IST = ZoneInfo('Asia/Kolkata')
SUPPORTED = {'zerodha', 'upstox', 'angel one', 'alice blue', 'dhan', 'fyers', 'groww', '5paisa'}
PENDING = {'OPEN', 'PENDING', 'TRIGGER_PENDING', 'VALIDATION_PENDING', 'PUT_ORDER_REQ_RECEIVED',
           'MODIFY_PENDING', 'TRANSIT', 'NEW', 'ACKED', 'APPROVED', 'PLACED', 'PARTIALLY_FILLED',
           'PARTIAL', 'PENDING_EXECUTION', 'AMO_REQ_RECEIVED'}
CANCELLING = {'CANCEL_PENDING', 'CANCELLATION_REQUESTED'}
CANCELLED = {'CANCELLED', 'CANCELED', 'REJECTED', 'FAILED', 'EXPIRED'}
FILLED = {'COMPLETE', 'COMPLETED', 'EXECUTED', 'TRADED', 'FILLED', 'FULLY_EXECUTED', 'DELIVERY_AWAITED'}


def first(row, *keys):
    for key in keys:
        if row.get(key) not in (None, ''):
            return row[key]
    return None


def integer(value):
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or n != n.to_integral_value():
            raise ValueError
        return int(n)
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError('Broker order quantity is missing or invalid.') from None


def broker_time(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value)
        match = re.fullmatch(r'/Date\((\d+)(?:[+-]\d+)?\)/', text)
        if match:
            return datetime.fromtimestamp(int(match[1])/1000, dt_timezone.utc)
        try:
            dt = parse_datetime(text)
        except (ValueError, TypeError):
            dt = None
        if not dt:
            for fmt in ('%d-%b-%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
        if not dt:
            return None
    return dt.replace(tzinfo=IST) if dt.tzinfo is None else dt


@dataclass(frozen=True)
class PendingBrokerOrder:
    order_id: str
    side: str
    status: str
    quantity: int
    filled: int
    symbol: str
    instrument_id: str
    exchange: str
    product: str
    average_price: str = ''
    created_at: datetime = None
    executed_at: datetime = None
    variety: str = ''
    segment: str = ''
    exchange_order_id: str = ''

    @property
    def remaining(self):
        return self.quantity - self.filled

    def snapshot(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['executed_at'] = self.executed_at.isoformat() if self.executed_at else None
        return data


def normalize_order(broker, row, expected_id, expected_side):
    order_id = str(first(row, 'order_id', 'orderid', 'orderId', 'brokerOrderId', 'groww_order_id', 'BrokerOrderId', 'BrokerOrderID', 'id') or '')
    if order_id != str(expected_id):
        raise ValueError('Broker returned a different order ID.')
    side = str(first(row, 'transaction_type', 'transactiontype', 'transactionType', 'BuySell', 'side') or '').upper()
    side = {'B':'BUY', 'S':'SELL', '1':'BUY', '-1':'SELL'}.get(side, side)
    if side != str(expected_side).upper():
        raise ValueError('Broker order side does not match the system order.')
    raw_status = first(row, 'order_status', 'orderstatus', 'orderStatus', 'OrderStatus', 'status')
    if broker == 'fyers':
        raw_status = {1:'CANCELLED', 2:'FILLED', 3:'OPEN', 4:'TRANSIT', 5:'REJECTED', 6:'PENDING', 7:'EXPIRED'}.get(raw_status, raw_status)
    status = re.sub(r'[\s-]+', '_', str(raw_status or '').upper())
    status = {'PARTIALLY_EXECUTED':'PARTIALLY_FILLED', 'PARTIALLY_EXECUTED_ORDER':'PARTIALLY_FILLED'}.get(status, status)
    quantity = integer(first(row, 'quantity', 'qty', 'OrderQty', 'Qty'))
    fill = first(row, 'filled_quantity', 'filledshares', 'filledQuantity', 'filledQty', 'tradedQuantity', 'TradedQty', 'ExecutedQty')
    # 5paisa reports the remainder rather than a fill count in OrderBook.
    if fill is None and broker == '5paisa' and first(row, 'PendingQty') is not None:
        fill = quantity - integer(row['PendingQty'])
    filled = integer(fill)
    if filled > quantity or quantity == 0:
        raise ValueError('Broker fill quantity is inconsistent.')
    return PendingBrokerOrder(
        order_id=order_id, side=side, status=status, quantity=quantity, filled=filled,
        symbol=str(first(row, 'tradingsymbol', 'trading_symbol', 'tradingSymbol', 'symbol', 'ScripName') or ''),
        instrument_id=str(first(row, 'instrument_token', 'instrument_key', 'symboltoken', 'instrumentId', 'securityId', 'ScripCode') or ''),
        exchange=str(first(row, 'exchange', 'exchangeSegment', 'Exch') or ''),
        product=str(first(row, 'product', 'producttype', 'productType', 'product_type', 'DelvIntra') or ''),
        average_price=str(first(row, 'average_price', 'averageprice', 'averagePrice', 'AveragePrice', 'averageTradedPrice', 'average_fill_price', 'tradedPrice', 'AvgRate', 'tradedAvgPrice') or ''),
        # Modification/last-update time is deliberately not an order creation time.
        created_at=broker_time(first(row, 'order_timestamp', 'orderentrytime', 'orderEntryTime', 'createTime', 'created_at', 'orderDateTime', 'OrderDateTime', 'BrokerOrderTime')),
        executed_at=broker_time(first(row, 'exchange_update_timestamp', 'exchorderupdatetime', 'updatetime', 'updateTime', 'trade_time')),
        variety=str(first(row, 'variety') or ''), segment=str(first(row, 'segment') or ''),
        exchange_order_id=str(first(row, 'ExchOrderID', 'exchange_order_id') or ''),
    )


class PendingOrderClient:
    def __init__(self, details, proxy):
        if not proxy:
            raise ValueError('Assigned broker proxy is required.')
        self.details, self.proxy = details, proxy
        self.broker = normalize_broker_name(details.broker_name.broker_name)
        if self.broker not in SUPPORTED:
            raise ValueError('Pending-order cancellation is unsupported for this broker.')
        self.token = get_access_token(details)
        if not self.token:
            raise ValueError('Broker token is missing.')

    def _request(self, method, url, **kwargs):
        # No automatic HTTP retry for financial mutations. The monitor reads
        # the exact order again after an ambiguous response.
        response = requests.request(method, url, proxies=self.proxy, timeout=10, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def _headers(self):
        return {'Authorization': f'Bearer {self.token}', 'Accept':'application/json', 'Content-Type':'application/json'}

    def _angel_headers(self):
        return {**self._headers(), 'X-PrivateKey':self.details.broker_API_KEY,
                'X-UserType':'USER', 'X-SourceID':'WEB', 'X-ClientLocalIP':'127.0.0.1',
                'X-ClientPublicIP':str(getattr(self.details.execution_node,'ip_address','127.0.0.1')),
                'X-MACAddress':'00:00:00:00:00:00'}

    def read(self, order_id, side, *, segment=''):
        if self.broker == 'zerodha':
            payload = self._request('GET', 'https://api.kite.trade/orders', headers={
                'X-Kite-Version':'3', 'Authorization':f'token {self.details.broker_API_KEY}:{self.token}'})
            rows = payload.get('data') if payload.get('status')=='success' else None
        elif self.broker == 'upstox':
            payload = self._request('GET','https://api.upstox.com/v2/order/retrieve-all',headers=self._headers())
            rows = payload.get('data') if payload.get('status')=='success' else None
        elif self.broker == 'angel one':
            payload = self._request('GET','https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getOrderBook',headers=self._angel_headers())
            rows = payload.get('data') if payload.get('status') is True else None
        elif self.broker == 'alice blue':
            from main.Alice_Blue_Api import A3_OPEN_API_BASE_URL
            payload = self._request('GET',A3_OPEN_API_BASE_URL+'orders/book',headers=self._headers())
            rows = payload.get('result') if str(payload.get('status') or payload.get('stat')).lower() in {'ok','success'} else None
        elif self.broker == 'dhan':
            rows = self._request('GET','https://api.dhan.co/v2/orders',headers={'access-token':self.token,'Accept':'application/json'})
        elif self.broker == 'fyers':
            payload=self._request('GET','https://api-t1.fyers.in/api/v3/orders',headers={'Authorization':f'{self.details.broker_API_KEY}:{self.token}'})
            rows=payload.get('orderBook') if payload.get('s')=='ok' else None
        elif self.broker == 'groww':
            if segment not in {'CASH','FNO'}:
                raise ValueError('Groww segment must come from the saved system order.')
            payload=self._request('GET',f'https://api.groww.in/v1/order/detail/{order_id}',params={'segment':segment},headers={**self._headers(),'X-API-VERSION':'1.0'})
            rows=[payload.get('payload')] if payload.get('status')=='SUCCESS' else None
        else:
            payload=self._request('POST','https://Openapi.5paisa.com/VendorsAPI/Service1.svc/V3/OrderBook',headers=self._headers(),json={
                'head':{'key':self.details.broker_API_KEY},'body':{'ClientCode':self.details.broker_API_UID or self.details.broker_Demate_User_Name}})
            rows=(payload.get('body') or {}).get('OrderBookDetail') if str((payload.get('head') or {}).get('status'))=='0' else None
        if not isinstance(rows,list):
            raise ValueError('Broker order book unavailable or session rejected.')
        matches=[r for r in rows if isinstance(r,dict) and str(first(r,'order_id','orderid','orderId','brokerOrderId','groww_order_id','BrokerOrderId','BrokerOrderID','id'))==str(order_id)]
        if len(matches)!=1:
            raise ValueError('Exact system order is missing or ambiguous in broker records.')
        return normalize_order(self.broker,matches[0],order_id,side)

    def cancel(self, order):
        # Callers must establish age, exact identity and fresh pending status.
        if order.status not in PENDING or order.remaining <= 0:
            raise ValueError('Only a verified pending remainder can be cancelled.')
        oid=order.order_id
        if self.broker=='zerodha':
            variety=order.variety or 'regular'
            if variety not in {'regular','amo'}:
                raise ValueError('Special-variety order requires broker review.')
            return self._request('DELETE',f'https://api.kite.trade/orders/{variety}/{oid}',headers={
                'X-Kite-Version':'3','Authorization':f'token {self.details.broker_API_KEY}:{self.token}'})
        if self.broker=='upstox':
            return self._request('DELETE','https://api-hft.upstox.com/v3/order/cancel',params={'order_id':oid},headers=self._headers())
        if self.broker=='angel one':
            return self._request('POST','https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/cancelOrder',headers=self._angel_headers(),json={'variety':order.variety or 'NORMAL','orderid':oid})
        if self.broker=='alice blue':
            from main.Alice_Blue_Api import A3_OPEN_API_BASE_URL
            return self._request('POST',A3_OPEN_API_BASE_URL+'orders/cancel',headers=self._headers(),json={'brokerOrderId':oid})
        if self.broker=='dhan':
            return self._request('DELETE',f'https://api.dhan.co/v2/orders/{oid}',headers={'access-token':self.token})
        if self.broker=='fyers':
            return self._request('DELETE','https://api-t1.fyers.in/api/v3/orders/sync',headers={'Authorization':f'{self.details.broker_API_KEY}:{self.token}'},json={'id':oid})
        if self.broker=='groww':
            if order.segment not in {'CASH','FNO'}:
                raise ValueError('Broker segment missing; cancellation blocked.')
            return self._request('POST','https://api.groww.in/v1/order/cancel',headers={**self._headers(),'X-API-VERSION':'1.0'},json={'groww_order_id':oid,'segment':order.segment})
        if not order.exchange_order_id or order.exchange_order_id=='0':
            raise ValueError('5paisa exchange order ID is missing.')
        return self._request('POST','https://Openapi.5paisa.com/VendorsAPI/Service1.svc/V1/CancelOrderRequest',headers=self._headers(),json={'head':{'key':self.details.broker_API_KEY},'body':{'ExchOrderID':order.exchange_order_id}})
