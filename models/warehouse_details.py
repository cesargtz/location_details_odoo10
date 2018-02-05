# -*- coding: utf-8 -*-

from odoo import models, fields, api

class WarehouseDetails(models.Model):
    _inherit = "stock.warehouse"

    locations = fields.Many2many('stock.location')

    in_tons = fields.Float(compute="_compute_in", readonly=True, store=False)
    out_tons = fields.Float(compute="_compute_out", readonly=True, store=False)
    available_tons = fields.Float(compute="_compute_available", readonly=True, store=False)


    @api.one
    @api.depends('locations')
    def _compute_in(self):
        for record in self.locations:
            self.in_tons += record.total_tons_reception

    @api.one
    @api.depends('locations')
    def _compute_out(self):
        for record in self.locations:
            self.out_tons += record.total_tons_outlet

    @api.one
    @api.depends('locations')
    def _compute_available(self):
        for record in self.locations:
            self.available_tons += record.total_tons_available
