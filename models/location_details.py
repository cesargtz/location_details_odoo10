# -*- coding: utf-8 -*-

from odoo import models, fields, api

class location_details(models.Model):
    _inherit = 'stock.location'

    truck_reception = fields.One2many('truck.reception','location_id')
    truck_outlet = fields.One2many('truck.outlet','location_id')
    wagon_outlet = fields.One2many('wagon.outlet','location_id')
    truck_internal = fields.One2many('truck.internal','location_id')
    truck_internal_dest = fields.One2many('truck.internal','location_dest_id')
    truck_outlet_surplus = fields.One2many('return.truck','location_id')

    total_tons_reception = fields.Float(compute="_compute_total_reception", store=False, readonly=True, help="Kilos Limpios")
    total_tons_outlet = fields.Float(compute="_compute_total_outlet", store=False, readonly=True, help="Kilos Netos")
    total_tons_available = fields.Float(compute="_compute_total_available", store=False, readonly=True,help="El calculo incluye las transferencias")

    percentage_quality_reception = fields.Float(compute="_compute_quality_reception", store=False, readonly=True,help="Calculo con recepcion de camiones y transferencias de destino") #humedad
    percentage_quality_damaged = fields.Float(compute="_compute_quality_damaged", store=False, readonly=True, help="Calculo con recepcion de camiones y transferencias de destino")
    percentage_quality_impurity = fields.Float(compute="_compute_quality_impurity", store=False, readonly=True, help="Calculo con recepcion de camiones y transferencias de destino")
    percentage_quality_break = fields.Float(compute="_compute_quality_break", store=False, readonly=True,help="Calculo con recepcion de camiones y transferencias de destino")

    wet_kilos_discount = fields.Float(compute="_compute_wet_kilos", store=False, readonly=True,help="Calculo con recepcion de camiones y transferencias de destino")
    damaged_kilos_discount = fields.Float(compute="_compute_damaged_kilos", store=False, readonly=True,help="Calculo con recepcion de camiones y transferencias de destino")
    impure_kilos_discount = fields.Float(compute="_compute_impure_kilos", store=False, readonly=True,help="Calculo con recepcion de camiones y transferencias de destino")
    broken_kilos_discount = fields.Float(compute="_compute_broken_kilos", store=False, readonly=True,help="Calculo con recepcion de camiones y transferencias de destino")

    transfer_origin = fields.Float(compute="_compute_transfer_origin", store=False, readonly=True)
    transfer_dest = fields.Float(compute="_compute_transfer_dest", store=False, readonly=True)

    total_outlet_surplus = fields.Float(compute="_compute_outlet_surplus", store=False, readonly=True)
    discount = fields.Float(compute="_compute_discount", store=False, readonly=True)
    existence = fields.Float(compute="_compute_existence", store=False, readonly=True)

    def _wizard(self):
        data = self.env['locationcalculate.wizard'].search([], order='id desc', limit=1)
        data = {
            'method_Istransfer': data[0].calculate_tranfer,
            'calculate_Cleankilos': data[0].calculate_clean_kilos,
        }
        return data

    @api.one
    @api.depends('truck_reception')
    def _compute_total_reception(self):
        if len(self.truck_reception) > 0:
            data = self._wizard()
            tons = 0
            if data['method_Istransfer'] == False:
                if data['calculate_Cleankilos'] == True:
                    tons = sum(record.clean_kilos for record in self.truck_reception)
                else:
                    tons = sum(record.raw_kilos for record in self.truck_reception)
            else:
                for record in self.truck_reception:
                    if record.stock_picking_id:
                        if data['calculate_Cleankilos'] == True:
                            tons += record.clean_kilos
                        else:
                            tons += record.raw_kilos
            self.total_tons_reception = tons / 1000
        else:
            self.total_tons_reception = 0


    @api.one
    @api.depends('truck_outlet','wagon_outlet')
    def _compute_total_outlet(self):
        data = self._wizard()
        tons_truck = 0
        tons_wagon = 0
        if len(self.truck_outlet) > 0 or len(self.wagon_outlet) > 0:
            if data['method_Istransfer'] == False:
                tons_truck = sum(record.raw_kilos for record in self.truck_outlet)
                tons_wagon = sum(record.raw_kilos for record in self.wagon_outlet)
                self.total_tons_outlet = (tons_truck + tons_wagon) / 1000
            else:
                for record in self.truck_outlet:
                    if record.stock_picking_id:
                        tons_truck += record.raw_kilos
                for record in self.wagon_outlet:
                     if record.stock_picking_id:
                         tons_wagon += record.raw_kilos
                self.total_tons_outlet = (tons_truck + tons_wagon) / 1000
        else:
            self.total_tons_outlet = 0


    @api.one
    @api.depends('truck_reception', 'truck_internal_dest') #'truck_internal_dest'
    def _compute_quality_reception(self):
        sum_total = 0
        total_tons = 0
        if len(self.truck_reception) > 0 or len(self.truck_internal_dest) > 0:
            for record in self.truck_reception:
                quality = record.humidity_rate
                tons = record.raw_kilos / 1000
                total_tons += tons
                total = tons * quality
                sum_total += total
            for record in self.truck_internal_dest:
                if record.humidity_rate_dest > 0:
                    if record.stock_destination:
                        quality = record.humidity_rate_dest
                        tons = record.raw_kilos_dest / 1000
                    else:
                        quality = record.humidity_rate
                        tons = record.raw_kilos / 1000
                    total_tons += tons
                    total = tons * quality
                    sum_total += total
            if sum_total > 0 and total_tons > 0:
                self.percentage_quality_reception = float(sum_total / total_tons)
            else:
                self.percentage_quality_reception = 0
        else:
            self.percentage_quality_reception = 0

    @api.one
    @api.depends('truck_reception') #'truck_internal_dest'
    def _compute_wet_kilos(self):
        # if len(self.truck_reception) > 0 or len(self.truck_internal_dest) > 0:
        if len(self.truck_reception) > 0:
            tons = 0
            data = self._wizard()
            for record in self.truck_reception:
                if data['method_Istransfer'] == False:
                    tons += record.humid_kilos
                else:
                    if record.stock_picking_id:
                        tons += record.humid_kilos
            # for record in self.truck_internal_dest:
            #     if record.stock_destination:
            #         tons += record.humid_kilos_dest
            #     else:
            #         tons += record.humid_kilos
            self.wet_kilos_discount = tons
        else:
            self.wet_kilos_discount = 0

    @api.one
    @api.depends('truck_reception') #,'truck_internal_dest'
    def _compute_damaged_kilos(self):
        if len(self.truck_reception) > 0: #or len(self.truck_internal_dest) > 0:
            tons = 0
            data = self._wizard()
            for record in self.truck_reception:
                if data['method_Istransfer'] == False:
                    tons += record.damaged_kilos
                else:
                    if record.stock_picking_id:
                        tons += record.damaged_kilos
                # for record in self.truck_internal_dest:
                #     if record.stock_destination:
                #         tons += record.damaged_kilos_dest
                #     else:
                #         tons += record.damaged_kilos
            self.damaged_kilos_discount = tons
        else:
            self.damaged_kilos_discount = 0

    @api.one
    @api.depends('truck_reception') #,'truck_internal_dest'
    def _compute_impure_kilos(self):
        if len(self.truck_reception) > 0: #or len(self.truck_internal_dest) > 0:
            tons = 0
            data = self._wizard()
            for record in self.truck_reception:
                if data['method_Istransfer'] == False:
                    tons += record.impure_kilos
                else:
                    if record.stock_picking_id:
                        tons += record.impure_kilos
            # for record in self.truck_internal_dest:
            #     if record.stock_destination:
            #         tons += record.impure_kilos_dest
            #     else:
            #         tons += record.impure_kilos
            self.impure_kilos_discount = tons
        else:
            self.impure_kilos_discount = 0

    @api.one
    @api.depends('truck_reception') #,'truck_internal_dest'
    def _compute_broken_kilos(self):
        if len(self.truck_reception) > 0: #or len(self.truck_internal_dest) > 0
            tons = 0
            data = self._wizard()
            for record in self.truck_reception:
                if data['method_Istransfer'] == False:
                    tons += record.broken_kilos
                else:
                    if record.stock_picking_id:
                        tons += record.broken_kilos
            # for record in self.truck_internal_dest:
            #     if record.stock_destination:
            #         tons += record.broken_kilos_dest
            #     else:
            #         tons += record.broken_kilos
            self.broken_kilos_discount = tons
        else:
            self.broken_kilos_discount = 0

    @api.one
    @api.depends('truck_reception','truck_internal_dest')
    def _compute_quality_damaged(self):
        if len(self.truck_reception) > 0 or len(self.truck_internal_dest) > 0:
            sum_total = 0
            total_tons = 0
            for record in self.truck_reception:
                quality = record.damage_rate
                tons = record.raw_kilos / 1000
                total_tons += tons
                total = tons * quality
                sum_total += total
            for record in self.truck_internal_dest:
                if record.damage_rate_dest > 0:
                    if record.stock_destination:
                        quality = record.damage_rate_dest
                        tons = record.raw_kilos_dest / 1000
                    else:
                        quality = record.damage_rate
                        tons = record.raw_kilos / 1000
                    total_tons += tons
                    total = tons * quality
                    sum_total += total
            if sum_total > 0 and total_tons > 0:
                self.percentage_quality_damaged = float(sum_total / total_tons)
            else:
                self.percentage_quality_damaged = 0
        else:
            self.percentage_quality_damaged = 0


    @api.one
    @api.depends('truck_reception','truck_internal_dest')
    def _compute_quality_impurity(self):
        if len(self.truck_reception) > 0 or len(self.truck_internal_dest) > 0:
            sum_total = 0
            total_tons = 0
            for record in self.truck_reception:
                quality = record.impurity_rate
                tons = record.raw_kilos / 1000
                total_tons += tons
                total = tons * quality
                sum_total += total
            for record in self.truck_internal_dest:
                if record.impurity_rate_dest > 0:
                    if record.stock_destination:
                        quality = record.impurity_rate_dest
                        tons = record.raw_kilos_dest / 1000
                    else:
                        quality = record.impurity_rate
                        tons = record.raw_kilos / 1000
                    total_tons += tons
                    total = tons * quality
                    sum_total += total
            if sum_total > 0 and total_tons > 0:
                self.percentage_quality_impurity = float(sum_total / total_tons)
            else:
                self.percentage_quality_impurity = 0
        else:
            self.percentage_quality_impurity = 0


    @api.one
    @api.depends('truck_reception','truck_internal_dest')
    def _compute_quality_break(self):
        if len(self.truck_reception) > 0  or len(self.truck_internal_dest) > 0:
            sum_total = 0
            total_tons = 0
            for record in self.truck_reception:
                quality = record.break_rate
                tons = record.raw_kilos / 1000
                total_tons += tons
                total = tons * quality
                sum_total += total
            for record in self.truck_internal_dest:
                if record.break_rate_dest > 0:
                    if record.stock_destination:
                        quality = record.break_rate_dest
                        tons = record.raw_kilos_dest / 1000
                    else:
                        quality = record.break_rate
                        tons = record.raw_kilos / 1000
                    total_tons += tons
                    total = tons * quality
                    sum_total += total
            if sum_total > 0 and total_tons > 0:
                self.percentage_quality_break = float(sum_total / total_tons)
            else:
                self.percentage_quality_break = 0
        else:
            self.percentage_quality_break = 0


    @api.one
    @api.depends('total_tons_reception','total_tons_outlet','discount')
    def _compute_total_available(self):
        self.total_tons_available = self.total_tons_reception  - self.total_tons_outlet

    @api.one
    @api.depends('truck_internal')
    def _compute_transfer_origin(self):
        if len(self.truck_internal) > 0:
            data = self._wizard()
            tons_origin = 0
            for record in self.truck_internal:
                if data['method_Istransfer'] == False:
                    if record.stock_destination:
                        tons_origin += record.raw_kilos_dest / 1000
                    else:
                        tons_origin += record.raw_kilos / 1000
                else:
                    if record.stock_picking_id:
                        if record.stock_destination:
                            tons_origin += record.raw_kilos_dest / 1000
                        else:
                            tons_origin += record.raw_kilos / 1000
            self.transfer_origin = tons_origin
        else:
            self.transfer_origin = 0.0

    @api.one
    @api.depends('truck_internal_dest')
    def _compute_transfer_dest(self):
         if len(self.truck_internal_dest) > 0:
            data = self._wizard()
            tons_dest = 0
            for record in self.truck_internal_dest:
                if data['method_Istransfer'] == False:
                    if record.stock_destination:
                        tons_dest += record.raw_kilos_dest / 1000
                    else:
                        tons_dest += record.raw_kilos / 1000
                else:
                    if record.stock_picking_id:
                        if record.stock_destination:
                            tons_dest += record.raw_kilos_dest / 1000
                        else:
                            tons_dest += record.raw_kilos / 1000
            self.transfer_dest = tons_dest
         else:
            self.transfer_dest = 0.0


    @api.one
    @api.depends('truck_outlet_surplus')
    def _compute_outlet_surplus(self):
        if len(self.truck_outlet_surplus) > 0:
            data = self._wizard()
            tons = 0
            if data['method_Istransfer'] == False:
                tons = sum(record.raw_kilos for record in self.truck_outlet_surplus)
            else:
                for record in self.truck_outlet_surplus:
                    if record.stock_picking_id:
                        tons += record.raw_kilos
            self.total_outlet_surplus = tons / 1000
        else:
            self.total_outlet_surplus = 0

    @api.one
    @api.depends('wet_kilos_discount','damaged_kilos_discount','impure_kilos_discount','broken_kilos_discount')
    def _compute_discount(self):
        tons = (self.wet_kilos_discount + self.damaged_kilos_discount + self.impure_kilos_discount + self.broken_kilos_discount)
        self.discount  = tons/1000


    @api.one
    @api.depends('existence')
    def _compute_existence(self):
        self.existence = float(self.total_tons_available + self.transfer_dest) - (self.transfer_origin + self.total_outlet_surplus)
        # self.existence  = tons if tons > 0 else 0
