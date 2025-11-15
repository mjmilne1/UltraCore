# Microsoft Agent Framework Research Findings

## Overview

**Microsoft Agent Framework** is an open-source development kit for building AI agents and multi-agent workflows for .NET and Python. It's the unified successor to both **Semantic Kernel** and **AutoGen**, created by the same Microsoft teams.

**Repository:** https://github.com/microsoft/agent-framework  
**Status:** Public Preview (October 2025)  
**Languages:** Python, .NET  
**Lineage:** Combines Semantic Kernel + AutoGen

## Core Capabilities

### 1. AI Agents
Individual agents that use LLMs to:
- Process user inputs
- Make decisions
- Call tools and MCP servers
- Generate responses

**Supported Providers:**
- Azure OpenAI
- OpenAI
- Azure AI

### 2. Workflows
Graph-based workflows that:
- Connect multiple agents and functions
- Perform complex, multi-step tasks
- Support type-based routing
- Enable nesting and composition
- Provide checkpointing for long-running processes
- Support request/response patterns for human-in-the-loop

### 3. Foundational Building Blocks
- **Model Clients:** Chat completions and responses
- **Agent Thread:** State management
- **Context Providers:** Agent memory
- **Middleware:** Intercept agent actions
- **MCP Clients:** Tool integration

## Why Agent Framework vs Semantic Kernel/AutoGen?

The Agent Framework is the **direct successor** to both:

**From AutoGen:**
- Simple abstractions for single- and multi-agent patterns
- Multi-agent conversation capabilities
- Agent coordination patterns

**From Semantic Kernel:**
- Enterprise-grade features
- Thread-based state management
- Type safety
- Filters and middleware
- Telemetry
- Extensive model and embedding support

**New in Agent Framework:**
- **Workflows:** Explicit control over multi-agent execution paths
- **Robust State Management:** For long-running and human-in-the-loop scenarios
- **Unified Foundation:** One framework instead of two

## Workflows: Key Features

### Modularity
Workflows can be broken down into smaller, reusable components, making it easier to manage and update individual parts.

### Agent Integration
Workflows can incorporate multiple AI agents alongside non-agentic components, allowing for sophisticated orchestration.

### Type Safety
Strong typing ensures messages flow correctly between components, with comprehensive validation that prevents runtime errors.

### Flexible Flow
Graph-based architecture allows for:
- Intuitive modeling of complex workflows
- Conditional routing
- Parallel processing
- Dynamic execution paths

### External Integration
Built-in request/response patterns enable:
- Seamless integration with external APIs
- Human-in-the-loop scenarios

### Checkpointing
Save workflow states via checkpoints, enabling:
- Recovery from failures
- Resumption of long-running processes on the server side

### Multi-Agent Orchestration
Built-in patterns for coordinating multiple AI agents:
- Sequential execution
- Concurrent execution
- Hand-off patterns
- Magentic (magnetic) patterns

### Composability
Workflows can be nested or combined to create more complex processes, allowing for scalability and adaptability.

## When to Use AI Agents

### ✅ Good Use Cases
- **Customer Support:** Multi-modal queries, tool usage, natural language responses
- **Education and Tutoring:** Personalized tutoring with external knowledge bases
- **Code Generation and Debugging:** Assist developers with implementation and debugging
- **Research Assistance:** Search web, summarize documents, piece together information

### ❌ Not Suitable For
- Highly structured tasks with predefined rules
- Tasks where you can write a function instead
- Simple, deterministic operations
- Tasks requiring strict adherence to rules

**Key Principle:** _"If you can write a function to handle the task, do that instead of using an AI agent. You can use AI to help you write that function."_

## When to Use Workflows

### Problems Workflows Solve
- Complex processes with multiple steps
- Multiple decision points
- Interactions with various systems or agents
- Tasks requiring more than one AI agent
- Long-running processes that need checkpointing
- Human-in-the-loop scenarios

## Applicability to UltraCore

### ✅ Strengths for UltraCore

**1. Workflow Orchestration**
- Graph-based workflows could model complex financial processes
- Checkpointing for long-running loan applications
- Type safety prevents runtime errors in financial operations

**2. Human-in-the-Loop**
- Perfect for compliance approval workflows
- Loan application reviews
- Large transaction confirmations

**3. MCP Integration**
- Native MCP client support
- Could consume UltraCore's existing MCP server

**4. Enterprise Features**
- Thread-based state management
- Telemetry and monitoring
- Middleware for auditing
- Type safety for financial data

**5. Multi-Agent Orchestration**
- Built-in patterns for coordinating agents
- Could orchestrate Anya + specialist agents

### ❌ Limitations for UltraCore

**1. LLM-Focused**
- Designed for LLM agents, not RL agents
- UltraCore's Alpha/Beta/Gamma/Delta/Epsilon/Zeta are RL-based

**2. Different State Model**
- Uses thread-based state management
- UltraCore uses Kafka event sourcing
- Checkpointing is not the same as event replay

**3. Microsoft Ecosystem**
- Optimized for Azure OpenAI and Azure AI
- UltraCore is cloud-agnostic

**4. Heavyweight Framework**
- Brings in Semantic Kernel + AutoGen concepts
- More complexity than needed for UltraCore

**5. Workflow Paradigm**
- Graph-based workflows are different from event-driven microservices
- Kafka provides better scalability for high-throughput operations

### 🎯 Potential Use Cases in UltraCore

**1. Compliance Workflows**
- Multi-step approval processes
- Human-in-the-loop for regulatory reviews
- Checkpointing for long-running audits

**2. Anya AI Assistant**
- Similar to OpenAI Agents SDK use case
- Multi-agent coordination (general + specialists)
- MCP client to access UltraCore services

**3. Document Processing**
- Multi-agent workflows for analyzing financial documents
- Extract data → Validate → Store → Notify

**4. Customer Onboarding**
- Complex, multi-step onboarding workflows
- Human approval at key checkpoints
- Type-safe data flow

### 🚫 NOT Recommended For

**1. Portfolio Optimization**
- RL agents are faster and more deterministic
- Workflows add unnecessary latency

**2. Credit Decisioning**
- Zeta Agent (RL) is superior to LLM-based decisioning
- Kafka event sourcing provides better audit trails

**3. Real-Time Trading**
- Workflow overhead too high
- Event-driven microservices are more appropriate

**4. High-Throughput Operations**
- Kafka can handle millions of events per second
- Workflows are designed for complex, not high-volume tasks

## Comparison: Agent Framework vs OpenAI Agents SDK

| Feature | Microsoft Agent Framework | OpenAI Agents SDK |
|---|---|---|
| **Languages** | Python, .NET | Python, TypeScript |
| **Workflows** | Graph-based, explicit control | Python-native orchestration |
| **State Management** | Thread-based + checkpointing | Sessions (SQLAlchemy, encrypted) |
| **Type Safety** | Strong typing, validation | Pydantic validation |
| **MCP Support** | Native | Native |
| **Telemetry** | Built-in | Built-in tracing |
| **Human-in-the-Loop** | Request/response patterns | Manual implementation |
| **Multi-Agent** | Built-in orchestration patterns | Handoffs |
| **Voice/Realtime** | Not mentioned | Full support |
| **Ecosystem** | Microsoft/Azure-centric | OpenAI-centric |
| **Lineage** | Semantic Kernel + AutoGen | Swarm |

## Conclusion

**Microsoft Agent Framework is a powerful, enterprise-grade framework for building complex multi-agent workflows, but it's designed for LLM agents, not RL agents. It's best suited for compliance workflows and Anya AI Assistant, not for core financial operations.**

### Recommendation for UltraCore

**Use Microsoft Agent Framework for:**
1. Compliance approval workflows (human-in-the-loop)
2. Document processing pipelines
3. Customer onboarding workflows
4. Possibly Anya AI Assistant (alternative to OpenAI Agents SDK)

**Keep existing architecture for:**
1. Portfolio optimization (RL agents)
2. Credit decisioning (Zeta Agent + Kafka)
3. Real-time trading (event-driven microservices)
4. High-throughput operations (Kafka event sourcing)

**Bottom Line:** Agent Framework excels at complex, multi-step workflows with human oversight, but UltraCore's event-driven, RL-based architecture is superior for core financial operations.
