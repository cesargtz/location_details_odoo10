# -*- coding: utf-8 -*-

from odoo import models, fields, api

class WarehouseDetails(models.Model):
    _name = "groups.location"

    name = fields.Char()
    location_in_ids = fields.Many2many('stock.location')
