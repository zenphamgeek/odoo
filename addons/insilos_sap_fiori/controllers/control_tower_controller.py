# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import json
import logging
from insilos import http
from insilos.http import request, Response

_logger = logging.getLogger("insilos.control_tower.controller")


class ControlTowerController(http.Controller):
    """
    Executive Control Tower Gateway Controller
    ===========================================
    Exposes /insilos/api/v1/control_tower/kpis endpoint.
    Guarantees:
    - 'Server: insilos/20.0' response header on all responses.
    - CORS enabled ('Access-Control-Allow-Origin: *').
    - Multi-method support: GET, POST, OPTIONS, and JSON-RPC.
    - User authentication ('auth=user').
    """

    @http.route(
        [
            "/insilos/api/v1/control_tower/kpis",
            "/insilos/api/v1/control_tower/kpis/<string:timeframe>",
        ],
        type="http",
        auth="user",
        methods=["GET", "POST", "OPTIONS"],
        csrf=False,
        cors="*",
    )
    def api_control_tower_kpis_http(self, timeframe=None, **kwargs):
        """
        HTTP REST Gateway endpoint returning Executive Control Tower KPI metrics.
        """
        # Handle CORS pre-flight
        if request.httprequest.method == "OPTIONS":
            headers = [
                ("Server", "insilos/20.0"),
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With"),
            ]
            return Response(status=204, headers=headers)

        try:
            # Parse parameters from URL, query string, or JSON body
            tf = timeframe or kwargs.get("timeframe")
            filters = {}

            if request.httprequest.content_type and "application/json" in request.httprequest.content_type:
                try:
                    payload = request.get_json_data()
                    if isinstance(payload, dict):
                        # Support standard payload or JSON-RPC params
                        if "params" in payload and isinstance(payload["params"], dict):
                            payload = payload["params"]
                        tf = tf or payload.get("timeframe")
                        if isinstance(payload.get("filters"), dict):
                            filters = payload.get("filters")
                except Exception as json_err:
                    _logger.debug("Non-fatal JSON parse notice: %s", json_err)

            if not tf:
                tf = "7d"

            if not filters and "domain" in kwargs:
                filters = {"domain": kwargs.get("domain")}
            if "company_id" in kwargs:
                try:
                    filters["company_id"] = int(kwargs["company_id"])
                except (ValueError, TypeError):
                    pass

            result = request.env["insilos.control.tower"].get_executive_kpi_metrics(
                timeframe=tf, filters=filters
            )

            # Ensure data envelope key is present for standard Insilos envelope compatibility
            if "data" not in result:
                result["data"] = {
                    "kpis": result.get("kpis"),
                    "industrial_mes": result.get("industrial_mes"),
                    "logistics_hub": result.get("logistics_hub"),
                    "process_pipelines": result.get("process_pipelines"),
                }

            body = json.dumps(result, indent=2, ensure_ascii=False)
            headers = [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Server", "insilos/20.0"),
                ("X-Content-Type-Options", "nosniff"),
                ("Access-Control-Allow-Origin", "*"),
            ]
            return Response(response=body, status=200, headers=headers, mimetype="application/json")

        except Exception as e:
            _logger.exception("Error serving Control Tower KPIs: %s", e)
            err_payload = {
                "success": False,
                "error": {
                    "code": 500,
                    "message": "Internal error retrieving Executive Control Tower metrics.",
                },
            }
            body = json.dumps(err_payload, indent=2, ensure_ascii=False)
            headers = [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Server", "insilos/20.0"),
                ("X-Content-Type-Options", "nosniff"),
                ("Access-Control-Allow-Origin", "*"),
            ]
            return Response(response=body, status=500, headers=headers, mimetype="application/json")

    @http.route(
        ["/insilos/api/v1/control_tower/kpis/rpc"],
        type="jsonrpc",
        auth="user",
        methods=["POST"],
        cors="*",
    )
    def api_control_tower_kpis_rpc(self, timeframe="7d", filters=None, **kwargs):
        """
        JSON-RPC endpoint returning Executive Control Tower KPI metrics.
        """
        return request.env["insilos.control.tower"].get_executive_kpi_metrics(
            timeframe=timeframe, filters=filters
        )
