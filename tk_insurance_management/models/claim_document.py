# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields
from ..utils import _display_notification


class ClaimDocuments(models.Model):
    """Claim Documents"""
    _name = 'claim.documents'
    _description = __doc__
    _rec_name = 'claim_document_type_id'

    claim_document_type_id = fields.Many2one('claim.document.type', string="Document Type")
    file_name = fields.Char(string="File Name", translate=True)
    description = fields.Char(string="Description", translate=True)
    avatar = fields.Binary(string="Document")
    claim_information_id = fields.Many2one('claim.information')
    state = fields.Selection([
        ('draft', "Draft"),
        ('verified', "Verified"),
        ('rejected', "Rejected")],
        string="Status", default='draft')

    def document_resubmit(self):
        """Draft stage"""
        self.state = 'draft'

    def verified_claim(self):
        """Verified claim"""
        if not self.avatar:
            message = _display_notification(
                message='Please upload the document, then proceed with verification.',
                message_type='warning')
            return message
        self.state = 'verified'
        return True

    def rejected_claim(self):
        """Rejected claim"""
        if not self.avatar:
            message = _display_notification(
                message='Upload the required document before rejecting.',
                message_type='warning')
            return message
        self.state = 'rejected'
        return True
