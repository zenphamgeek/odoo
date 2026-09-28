# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos import http, _
from insilos.fields import Domain
from insilos.http import Controller, request
from insilos.exceptions import ValidationError


class DomainController(Controller):

    @http.route('/web/domain/validate', type='jsonrpc', auth="user")
    def validate(self, model, domain):
        """ Parse `domain` and verify that it can be used to search on `model`
        :return: True when the domain is valid, otherwise False
        :raises ValidationError: if `model` is invalid
        """
        Model = request.env.get(model)
        if Model is None:
            raise ValidationError(_('Invalid model: %s', model))
        try:
            Domain(domain).validate(Model.sudo())
            return True
        except (ValueError, TypeError):  # noqa: BLE001
            return False
