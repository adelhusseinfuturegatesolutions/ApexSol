# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields
from ..utils import _display_notification


class InsuredDocuments(models.Model):
    """Insured Documents"""
    _name = 'insured.documents'
    _description = __doc__
    _rec_name = 'insured_info_id'

    insured_info_id = fields.Many2one("insurance.information", string="Insured No", readonly=True)
    insured_id = fields.Many2one('res.partner', string="Policy Holder",
                                 domain="[('is_agent', '=', False)]")
    file_name = fields.Char(string="filename", translate=True)
    avatar = fields.Binary(string="Document")
    insured_document_type_id = fields.Many2one('insured.document.type', string="Document Type")
    state = fields.Selection([
        ('draft', "Draft"),
        ('verified', "Verified"),
        ('rejected', "Rejected")],
        string="Status", default='draft')

    def _check_document_and_notify(self):
        """Check if the document is uploaded"""
        if not self.avatar:
            message = _display_notification(
                message='Please first upload the insured document',
                message_type='warning')
            return message
        return None

    def document_resubmit(self):
        """Document resubmit"""
        message = self._check_document_and_notify()
        if message:
            return message
        self.state = 'draft'
        return None

    def verified_claim(self):
        """Verified claim"""
        message = self._check_document_and_notify()
        if message:
            return message
        self.state = 'verified'
        return None

    def rejected_claim(self):
        """Rejected claim"""
        message = self._check_document_and_notify()
        if message:
            return message
        self.state = 'rejected'
        return None
