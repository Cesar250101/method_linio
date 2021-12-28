# -*- coding: utf-8 -*-

from odoo import models, fields, api
import urllib.parse
import hashlib
import hmac
from datetime import datetime, timedelta
import requests
import dicttoxml
import xml.etree.ElementTree as ET


class ModuleName(models.Model):
    _inherit = 'res.company'

    user_id = fields.Char(string='User ID')
    version = fields.Char(string='Versión',default='1.0')
    json_format = fields.Char(string='json_format',default='JSON')
    api_key = fields.Char(string='Api Key')
    dias_desde=fields.Integer('Dias desde')
    ubicacion_stock = fields.Many2one(comodel_name='stock.location', 
                                string='Ubicación Inventario', 
                                domain = "[('usage','=','internal')]")



