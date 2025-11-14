"""MCP Tools for Template Management"""
from typing import Dict, List
from datetime import datetime

async def create_custom_template(name: str, template_type: str,
                                configuration: Dict,
                                description: str) -> Dict:
    """Create a custom template
    
    Args:
        name: Template name
        template_type: Type (portfolio, rebalancing, alert, report)
        configuration: Template configuration
        description: Template description
    
    Returns:
        Created template details
    """
    template_id = f"template_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "template_id": template_id,
        "name": name,
        "type": template_type,
        "configuration": configuration,
        "description": description,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "user_123",
        "version": "1.0",
        "is_public": False,
        "usage_count": 0
    }

async def apply_template(template_id: str, target_id: str,
                        customizations: Dict = None) -> Dict:
    """Apply template to target entity
    
    Args:
        template_id: Template ID
        target_id: Target entity ID (portfolio, user, etc.)
        customizations: Optional customizations
    
    Returns:
        Application result
    """
    return {
        "template_id": template_id,
        "target_id": target_id,
        "status": "applied",
        "customizations_applied": customizations or {},
        "applied_at": datetime.utcnow().isoformat(),
        "changes_made": [
            "Updated asset allocation",
            "Set rebalancing thresholds",
            "Configured alert rules"
        ],
        "rollback_available": True,
        "rollback_expires_at": "2024-11-21T00:00:00Z"
    }

async def get_template_recommendations(user_id: str,
                                      context: Dict) -> List[Dict]:
    """Get personalized template recommendations
    
    Args:
        user_id: User ID
        context: User context (profile, preferences, goals)
    
    Returns:
        List of recommended templates
    """
    age = context.get('age', 40)
    risk_tolerance = context.get('risk_tolerance', 'moderate')
    country = context.get('country', 'AU')
    
    recommendations = []
    
    # Portfolio templates
    if age < 40 and risk_tolerance == 'high':
        recommendations.append({
            "template_id": "template_aggressive_growth",
            "name": "Aggressive Growth",
            "type": "portfolio",
            "match_score": 0.95,
            "reason": "High risk tolerance and long investment horizon"
        })
    
    if country == 'AU' and age > 60:
        recommendations.append({
            "template_id": "template_au_retirement",
            "name": "Australian Retirement Income",
            "type": "portfolio",
            "match_score": 0.92,
            "reason": "Age-appropriate with franking credit optimization"
        })
    
    # Rebalancing templates
    recommendations.append({
        "template_id": "template_threshold_rebalance",
        "name": "Threshold Rebalancing",
        "type": "rebalancing",
        "match_score": 0.88,
        "reason": "Suitable for active portfolio management"
    })
    
    return recommendations

async def customize_template(template_id: str,
                            customizations: Dict) -> Dict:
    """Customize a template
    
    Args:
        template_id: Template ID
        customizations: Customization parameters
    
    Returns:
        Customized template
    """
    return {
        "template_id": template_id,
        "customized_template_id": f"{template_id}_custom_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "base_template": template_id,
        "customizations": customizations,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "changes": [
            f"Modified {key}: {value}"
            for key, value in customizations.items()
        ]
    }

async def get_template_marketplace(category: str = None,
                                  sort_by: str = "popularity") -> List[Dict]:
    """Browse template marketplace
    
    Args:
        category: Filter by category (portfolio, rebalancing, alert, report)
        sort_by: Sort by (popularity, rating, recent)
    
    Returns:
        List of marketplace templates
    """
    templates = [
        {
            "template_id": "template_aggressive_growth",
            "name": "Aggressive Growth",
            "category": "portfolio",
            "description": "80% equities, 20% alternatives for long-term growth",
            "rating": 4.8,
            "usage_count": 1250,
            "created_by": "UltraCore",
            "price_aud": 0.00,  # Free
            "is_verified": True
        },
        {
            "template_id": "template_au_retirement",
            "name": "Australian Retirement Income",
            "category": "portfolio",
            "description": "Franking credit optimized income portfolio",
            "rating": 4.9,
            "usage_count": 890,
            "created_by": "UltraCore",
            "price_aud": 0.00,
            "is_verified": True
        },
        {
            "template_id": "template_threshold_rebalance",
            "name": "Threshold Rebalancing",
            "category": "rebalancing",
            "description": "Rebalance when allocation drifts >5%",
            "rating": 4.7,
            "usage_count": 2100,
            "created_by": "UltraCore",
            "price_aud": 0.00,
            "is_verified": True
        }
    ]
    
    # Filter by category
    if category:
        templates = [t for t in templates if t['category'] == category]
    
    # Sort
    if sort_by == "popularity":
        templates.sort(key=lambda x: x['usage_count'], reverse=True)
    elif sort_by == "rating":
        templates.sort(key=lambda x: x['rating'], reverse=True)
    
    return templates
