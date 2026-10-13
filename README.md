# Insilos Enterprise Platform

Sovereign Industrial AI & Enterprise Execution Platform.

Insilos is an integrated suite of web-based enterprise applications designed for mission-critical industrial manufacturing, supply chain telemetry, and regulatory compliance.

## Key Capabilities

- **Platform Architecture**: Model-driven enterprise architecture with sub-15ms P99 transaction throughput.
- **Enterprise Execution**: Real-time integration spanning MES, WMS, CRM, FSM, and TT 200/78 compliance accounting.
- **Data Lineage & Auditability**: Tamper-proof cryptographic event logs and verifiable state transitions.
- **Modern User Experience**: Fluid responsive web client powered by Phosphor Icons, accessible UI standards, and high-density telemetry consoles.

## Getting Started

### Local Development Environment
```bash
./start_dev.sh
```

The enterprise web interface will be accessible at `http://localhost:28069`.

## Telemetry & Incident Reporting Gateway

Insilos Platform operates a dedicated, security-hardened headless incident reporting gateway:
- **Central Reporting Ingress**: `POST https://report.insilos.com/api/v1/runtime-report`
- **Gateway Health Status**: `GET https://report.insilos.com/api/v1/health`
- **Architecture**: Pure NoDB Headless Gateway (0 Database Binding, Zero Web/UI Modules, sub-15ms P99 latency)
- **Protocol**: AL2C-v1 with HMAC-SHA256 attestation signatures and sliding-window deduplication
- **Detailed Documentation**: See [RUNTIME_REPORTING_GATEWAY.md](file:///home/zen/O20/docs/RUNTIME_REPORTING_GATEWAY.md)

## Security

Please report vulnerabilities privately to `security@insilos.com`.

