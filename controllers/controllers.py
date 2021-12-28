# -*- coding: utf-8 -*-
from odoo import http

# class MethodLinio(http.Controller):
#     @http.route('/method_linio/method_linio/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/method_linio/method_linio/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('method_linio.listing', {
#             'root': '/method_linio/method_linio',
#             'objects': http.request.env['method_linio.method_linio'].search([]),
#         })

#     @http.route('/method_linio/method_linio/objects/<model("method_linio.method_linio"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('method_linio.object', {
#             'object': obj
#         })