import { serverState } from "../../mock_server_state.hoot";
import * as fields from "../mock_fields";
import { ServerModel } from "../mock_model";

export class ResCompany extends ServerModel {
    _name = "res.company";

    name = fields.Char();
    active = fields.Boolean({ default: true });
    partner_id = fields.Many2one({ relation: "res.partner" });
    description = fields.Text();

    _records = serverState.companies.map((company) => ({
        id: company.id,
        active: true,
        name: company.name,
        partner_id: company.id,
    }));
}
