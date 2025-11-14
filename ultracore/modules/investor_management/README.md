# Investor Management Module

**Author:** Manus AI  
**Date:** November 13, 2025

## 1. Overview

This module adds a comprehensive **Investor Management** capability to UltraCore, enabling the platform to support loan sales, investor tracking, and secondary market functionality. It is designed to be fully integrated with UltraCore's event-sourcing, Kafka-first architecture.

### Key Features

- **Investor Lifecycle Management**: Onboard, verify (KYC/AML), and manage external investors.
- **Loan Transfer Operations**: Full support for loan sales, buybacks, intermediary sales, and securitization.
- **Event-Sourced Architecture**: All operations are captured as immutable events in Kafka for a complete audit trail.
- **AI-Powered Matching & Pricing**: Machine learning models to match loans with suitable investors and recommend purchase prices.
- **Fraud Detection**: AI-powered fraud detection for suspicious transactions.
- **Payment Routing**: Automatic routing of loan repayments to the new owner.
- **MCP Integration**: A full suite of MCP tools for AI agents to interact with the module.
- **RESTful API**: A comprehensive set of FastAPI endpoints for programmatic access.

## 2. Architecture

The module follows UltraCore's microservices-ready architecture and is composed of several services:

- **Investor Service**: Manages the investor lifecycle.
- **Transfer Service**: Handles all loan transfer operations.
- **AI Matching Engine**: Matches loans to investors.
- **AI Pricing Engine**: Recommends loan sale prices.
- **Fraud Detection Engine**: Assesses risk in transfers.
- **Kafka Event Producer**: Publishes all events to Kafka.

### Kafka Topics

The module uses the following Kafka topics for event streaming:

- `investor-events`: Investor lifecycle events
- `transfer-events`: Loan transfer lifecycle events
- `ownership-events`: Immutable record of loan ownership changes
- `payment-routing-events`: Payment routing configurations and events
- `ai-events`: Events from the AI/ML services
- `securitization-events`: Events related to securitization pools

## 3. How to Use

### API Endpoints

The module exposes a full set of RESTful API endpoints under `/api/v1/investors`. You can interact with these endpoints to:

- Create and manage investors
- Initiate and approve loan transfers
- Get AI-powered investor matching and pricing recommendations
- Query investor portfolios

See the `investor_api.py` file for the complete OpenAPI documentation.

### MCP Tools

The module provides a comprehensive set of MCP tools for AI agents. These tools allow agents to perform all major operations, such as creating investors, initiating transfers, and getting AI-powered insights.

See the `investor_tools.py` file for the complete list of MCP tool definitions.

## 4. Deployment

The module can be deployed as a standalone service or as part of a larger UltraCore deployment. The following components are required:

- **Investor Management Service**: The main service for this module.
- **Kafka**: For event streaming.
- **PostgreSQL**: For storing materialized views.
- **Redis**: For caching.

See the `docker-compose.yml` file in the `deployment/` directory for an example of how to run the service.

## 5. PowerShell Deployment Script

A PowerShell script is provided to automate the deployment of the Investor Management module. The script will:

1. Clone the UltraCore repository.
2. Build the Docker images for the new services.
3. Start the services using Docker Compose.

To run the script, open a PowerShell terminal and execute:

```powershell
./deploy_investor_management.ps1
```
