# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.http import request


def force_guest_env(guest_token=None):
    if guest_token and request:
        guest = request.env['mail.guest']._get_guest_from_token(guest_token)
        if guest:
            request.update_context(guest=guest)
    return
