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


class Productos(models.Model):
    _inherit = 'product.template'

    sellersku = fields.Char(string='SellerSku')
    shopsku=fields.Char(string='ShopSku')
    name=fields.Char(string='Name')
    variation=fields.Char(string='Variation')
    parentSku=fields.Char(string='ParentSku')
    price=fields.Char(string='Price')
    status=fields.Char(string='Status')
    productid=fields.Char(string='ProductId')
    url=fields.Char(string='Url')
    image = fields.Binary(string='Image')
    description=fields.Char(string='description')
    brand=fields.Char(string='brand')
    primarycategory=fields.Char(string='PrimaryCategory')
    categories=fields.Char(string='Categories')
        

    # Método para la obtención de un listado de productos de acuerdo a ciertos filtros
    @api.model
    def get_products(self):
        company=self.env.user.company_id    
        action = 'GetProducts' # Es la acción que se solicitará al sistema
        days = company.dias_desde
        created_after = self.get_created_after_date(days) # Filtrará solo los productos creados en los últimos X días enviados por parámetro, se puede cambiar el valor para mostrar productos anteriores.
        USER_ID=company.user_id
        VERSION=company.version
        JSON_FORMAT=company.json_format
        API_KEY=company.api_key
        TIME_STAMP_NOW=datetime.now().isoformat()
        
        url = self.get_signature_url(USER_ID, VERSION, JSON_FORMAT, API_KEY, TIME_STAMP_NOW, action, created_after, None, None)
        response = requests.get(url)
        try:
            products = response.json()["SuccessResponse"]["Body"]["Products"]["Product"]
            #products = response.json()["SuccessResponse"]["Body"]["Products"]
            for p in products:
                sellersku=p['SellerSku']
                shopsku=p['ShopSku']                
                if p['Variation']=='...':
                    name=p['Name']
                    variation=p['Variation']
                else:
                    name=p['Name']+' '+p['Variation']
                    variation=""
                parentSku=p['ParentSku']
                price=p['Price']
                status=p['Status']
                productid=p['ProductId']
                url=p['Url']
                try:
                    image = base64.b64encode(requests.get(p['MainImage'].replace('\/', '/')).content)
                except:
                    image=""
                description=p['Description']
                brand=p['Brand']
                primarycategory=p['PrimaryCategory']
                product_id=self.env['product.template'].search([('default_code','=',sellersku)],limit=1)
                try:
                    categories=p['Categories']                
                    category_id=self.env['product.category'].search([('name','=',categories)],limit=1)
                except:
                    category_id=self.env['product.category'].search([('id','=',1)],limit=1)
                if not category_id:
                    values={
                        'name':categories
                    }
                    category_id=category_id.create(values)                

                values={
                            'sellersku':sellersku,
                            'shopsku':shopsku,
                            'name':name,
                            'default_code':sellersku,
                            'categ_id':category_id.id,
                            'type':'product',
                            'variation':variation,
                            'parentSku':parentSku,
                            'price':price,
                            'list_price':price,
                            'status':status,
                            'productid':productid,
                            'url':url,
                            'image':image,
                            'description':description,
                            'brand':brand,
                            'primarycategory':primarycategory,
                            'categories':categories
                    }
                if not product_id:
                    product_id=product_id.create(values)
                else:
                    product_id=product_id.write(values)
        except:
            return print(f"An error ocurred: No hay productos para los filtros aplicados, Días: {days} Proucto {name}")
        return products

    #print(get_products())

    # Método para la obtención de un producto particular
    @api.model
    def get_product_by_id(self,product_id):
        company=self.env.user.company_id 
        USER_ID=company.user_id
        VERSION=company.version
        JSON_FORMAT=company.json_format
        API_KEY=company.api_key
        TIME_STAMP_NOW=datetime.now().isoformat()
        action = 'GetProducts' # Es la acción que se solicitará al sistema
        url = self.get_signature_url(USER_ID, VERSION, JSON_FORMAT, API_KEY, TIME_STAMP_NOW, action, None, None, None, product_id)
        response = requests.get(url)
        try:
            product = response.json()["SuccessResponse"]["Body"]["Products"]["Product"]
        except:
            return print(f"An error ocurred: No se encontró el producto con SellerSku: {product_id}")
        return product

    #print(get_product_by_id("H11-32")) #El valor por el que se busca un producto es el "SellerSku"

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

    #Actualizar stock
    def actualizar_stock(self):
        company=self.env.user.company_id   
        productos_linio=self.search([('sellersku','!=',False)])
        for p in productos_linio:
            product_product=self.env['product.product'].search([('product_tmpl_id','=',p.id)],limit=1).id
            stock=self.env['stock.quant'].search([('product_id','=',product_product),('location_id','=',company.ubicacion_stock.id)],limit=1).quantity
            product=self.update_product_stock(p.sellersku,stock)

    # Método para actualizar el stock de un producto
    @api.model
    def update_product_stock(self,product_id, stock):
        product_to_update = self.get_product_by_id(product_id)
        company=self.env.user.company_id           
        USER_ID=company.user_id
        VERSION=company.version
        JSON_FORMAT=company.json_format
        API_KEY=company.api_key
        TIME_STAMP_NOW=datetime.now().isoformat()        
        #print(product_to_update)

        # if product_to_update["Quantity"] == str(stock):
        #     return print(f"No se actualizó el producto: {product_id} a {stock} unidades ya que es el valor actual")
        product_to_update["Quantity"] == stock
        data = { "SellerSku" : product_to_update["SellerSku"], "Quantity": product_to_update["Quantity"]}
        product = {"Product": data }	
        request = {"Request": product }

        xml = dicttoxml.dicttoxml(request, attr_type = False)
        new_xml = list( ET.fromstring(xml) )[0] 
        xml_final = ET.tostring(new_xml, encoding='utf8', method='xml')

        action = 'ProductUpdate'
        url = self.get_signature_url(USER_ID, VERSION, JSON_FORMAT, API_KEY, TIME_STAMP_NOW, action, None, None, None, None)

        response = requests.post(url, data = xml_final)
        try:
            product = response.json()["SuccessResponse"]
            return print(f"Se actualizó existoramente el stock del producto: {product_id} a {stock} unidades")
        except:
            return print(f"An error ocurred: No se encontró el producto con SellerSku: {product_id}")