# -*- coding: utf-8 -*-

from odoo import models, fields, api
import urllib.parse
import hashlib
import hmac
from datetime import datetime, timedelta
import requests
import dicttoxml
import xml.etree.ElementTree as ET
from PIL import Image
from io import BytesIO
import io
import base64

class Ordenes(models.Model):
    _inherit = 'sale.order'


    orderid = fields.Char(string='OrderId')
    ordernumber = fields.Char(string='OrderNumber')
    paymentmethod= fields.Char(string='PaymentMethod')
    statuses= fields.Char(string='Statuses')

    # Método para obtener un listado de ordenes de acuerdo a diferentes filtros
    @api.model
    def get_orders(self):
        company=self.env.user.company_id    
        action = 'GetProducts' # Es la acción que se solicitará al sistema
        days = company.dias_desde
        created_after = self.get_created_after_date(days) # Filtrará solo los productos creados en los últimos X días enviados por parámetro, se puede cambiar el valor para mostrar productos anteriores.
        USER_ID=company.user_id
        VERSION=company.version
        JSON_FORMAT=company.json_format
        API_KEY=company.api_key
        TIME_STAMP_NOW=datetime.now().isoformat()        
        action = 'GetOrders' # Es la acción que se solicitará al sistema
        status = 'delivered' # El estado se deberá setear de acuerdo al estado de las órdenes que se desean obtener. Los estados pueden ser: pending, canceled, ready_to_ship, delivered, returned, shipped and failed.

        created_after = self.get_created_after_date(days) # Filtrará solo las órdenes creadas en los últimos XX días, se puede cambiar el valor para mostrar órdenes anteriores.

        url = self.get_signature_url(USER_ID, VERSION, JSON_FORMAT, API_KEY, TIME_STAMP_NOW, action, created_after, status, None)
        response = requests.get(url)
        orders = response.json()["SuccessResponse"]["Body"]["Orders"]["Order"]
        self.procesar_orden(orders)
        return orders

    #print(get_orders())

    @api.model
    def procesar_orden(self,orders):
        for p in orders:
            nombre=p['AddressBilling']['FirstName']+" "+p['AddressBilling']['LastName']
            cliente=self.env['res.partner'].search([('name','=',nombre)],limit=1)
            if not cliente:
                values={
                    'name':nombre,
                    'phone':p['AddressBilling']['Phone'],
                    'mobile':p['AddressBilling']['Phone2'],
                    'street':p['AddressBilling']['Address1'],
                    'email':p['AddressBilling']['CustomerEmail'],
                    'city':p['AddressBilling']['City'],
                    'zip':p['AddressBilling']['PostCode']
                }
                cliente=cliente.create(values)
            lineas=self.get_order_items_by_order_id(p['OrderId'])
            order_line=[] 
            try:
                product_id=self.env['product.template'].search([('sellersku','=',lineas['OrderItem']['Sku'])],limit=1)
                product_id=self.env['product.product'].search([('product_tmpl_id','=',product_id.id)],limit=1)
                if product_id:
                    descuento=0
                    precio=int(float(lineas['OrderItem']['ItemPrice']))                
                    precioneto=precio/1.19
                    order_line.append(
                                        (0, 0, {
                                            "product_id": product_id.id,
                                            "product_uom_qty":1,
                                            "price_unit": precioneto,
                                            "discount": descuento,
                                            #"order_id":id_order.id,
                                            "product_uom":product_id.product_tmpl_id.uom_id.id,
                                            "name":product_id.product_tmpl_id.name,   
                                        }))
            except:
                for l in lineas['OrderItem']:
                    product_id=self.env['product.template'].search([('sellersku','=',l['Sku'])],limit=1)
                    product_id=self.env['product.product'].search([('product_tmpl_id','=',product_id.id)],limit=1)
                    if product_id:
                        descuento=0
                        precio=int(float(l['ItemPrice']))      
                        precioneto=precio/1.19
                        order_line.append(
                                            (0, 0, {
                                                "product_id": product_id.id,
                                                "product_uom_qty":1,
                                                "price_unit": precioneto,
                                                "discount": descuento,
                                                #"order_id":id_order.id,
                                                "product_uom":product_id.product_tmpl_id.uom_id.id,
                                                "name":product_id.product_tmpl_id.name,   
                                            }))
            status=p['Statuses']['Status']
            precio=int(float(p['Price']))
            precioneto=int(float(p['Price']))/1.19
            impuesto=precio-precioneto
            values={
                'name':p['OrderNumber'],
                'create_date':p['CreatedAt'],
                'orderid':p['OrderId'],
                'ordernumber':p['OrderNumber'],
                'paymentmethod':p['PaymentMethod'],
                'statuses':status,
                'amount_total':precio,
                'amount_untaxed':precioneto,
                'amount_tax':impuesto,
                'partner_id':cliente.id,
                "order_line":order_line,
            }
            order=self.search([('orderid','=',p['OrderId'])],limit=1)
            if not order:
                order=order.create(values)
            else:
                order=order.write(values)


    # Método para obtener lineas de orden por ID
    @api.model
    # Método para obtener una orden por ID con el detalle de los Items
    def get_order_items_by_order_id(self,order_id):
        company=self.env.user.company_id    
        days = company.dias_desde
        created_after = self.get_created_after_date(days) # Filtrará solo los productos creados en los últimos X días enviados por parámetro, se puede cambiar el valor para mostrar productos anteriores.
        USER_ID=company.user_id
        VERSION=company.version
        JSON_FORMAT=company.json_format
        API_KEY=company.api_key
        TIME_STAMP_NOW=datetime.now().isoformat()    
        action = 'GetOrderItems' # Es la acción que se solicitará al sistema

        url = self.get_signature_url(USER_ID, VERSION, JSON_FORMAT, API_KEY, TIME_STAMP_NOW, action, None, None, order_id) 
        response = requests.get(url)
        try:
            order_line = response.json()["SuccessResponse"]["Body"]["OrderItems"]
        except:
            return print(f"An error ocurred: No se encontró orden con ID: {order_id}")
        return order_line

    #order_id = "7607750"
    #print(get_order_items_by_order_id(order_id))

    # Método para obtener una orden por ID
    @api.model
    def get_order_by_id(self,order_id):
        company=self.env.user.company_id            
        USER_ID=company.user_id
        VERSION=company.version
        JSON_FORMAT=company.json_format
        API_KEY=company.api_key
        TIME_STAMP_NOW=datetime.now().isoformat()        

        action = 'GetOrder' # Es la acción que se solicitará al sistema

        url = self.get_signature_url(USER_ID, VERSION, JSON_FORMAT, API_KEY, TIME_STAMP_NOW, action, None, None, order_id) 
        response = requests.get(url)
        try:
            order = response.json()["SuccessResponse"]["Body"]["Orders"]["Order"]
        except:
            return print(f"An error ocurred: No se encontró orden con ID: {order_id}")
        return order

    #order_id = "7568549"
    #print(get_order_by_id(order_id))    

    @api.model
    def get_created_after_date(self,days):
        created_after = (datetime.now() - timedelta(days=days)).isoformat()
        return created_after

    # Método para obtener la url a la que se va a realizar la consulta de acuerdo a los diferentes parámetros y datos que se necesitan 
    @api.model
    def get_signature_url(self,user_id, version, json_format, api_key, time_stamp_now, action, created_after=None, status=None, order_id=None, product_id=None):
        parameters = {
        'UserID': user_id,
        'Version': version,
        'Action': action ,
        'Format': json_format,
        'Timestamp': time_stamp_now
        }
        
        url = f'https://sellercenter-api.linio.cl/?Version={version}&Action={action}&Format={json_format}&Timestamp={time_stamp_now}&UserID={user_id}'
        if status:
            parameters["Status"] = status
            url += f'&Status={status}'
        if created_after:
            parameters["CreatedAfter"] = created_after
            url += f'&CreatedAfter={created_after}'
        if order_id:
            parameters["OrderId"] = order_id
            url += f'&OrderId={order_id}'
        if product_id:
            parameters["Search"] = product_id
            url += f'&Search={product_id}'
        api_endoced = api_key.encode()
        concatenated = (urllib.parse.urlencode(sorted(parameters.items()))).encode()
        signature = hmac.new(api_endoced, concatenated, hashlib.sha256).hexdigest()
        url += f'&Signature={signature}'
        return url



