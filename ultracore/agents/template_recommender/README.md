# Template Recommender AI Agent

## Overview
AI agent for personalized template recommendations.

## Features
- Portfolio template recommendations
- Rebalancing strategy recommendations
- Alert rule recommendations
- Template personalization

## Usage
```python
from ultracore.agents.template_recommender.template_recommender_agent import TemplateRecommenderAgent

agent = TemplateRecommenderAgent(llm_client)

# Recommend portfolio template
result = await agent.recommend_portfolio_template(client_profile)
```
