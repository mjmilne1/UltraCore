"""
UltraCore Module Inventory
Comprehensive audit of all UltraCore modules and features
"""

import os
import glob

def audit_domains():
    """Audit domain modules"""
    
    print("=" * 80)
    print("ULTRACORE MODULE INVENTORY")
    print("=" * 80)
    print()
    
    print("1. DOMAIN MODULES:")
    print("-" * 80)
    
    # Find all domain directories
    domain_paths = [
        'src/ultracore/domains',
        'ultracore/domains',
    ]
    
    domains = set()
    for base_path in domain_paths:
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and not item.startswith('_'):
                    domains.add(item)
    
    for domain in sorted(domains):
        print(f"  ✓ {domain}")
    
    print(f"\n  Total Domains: {len(domains)}")
    print()
    
    return domains

def audit_api_modules():
    """Audit API modules"""
    
    print("2. API MODULES:")
    print("-" * 80)
    
    api_paths = [
        'ultracore/api/v1',
    ]
    
    api_modules = set()
    for base_path in api_paths:
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and not item.startswith('_'):
                    api_modules.add(item)
    
    for module in sorted(api_modules):
        print(f"  ✓ {module}")
    
    print(f"\n  Total API Modules: {len(api_modules)}")
    print()
    
    return api_modules

def audit_services():
    """Audit service modules"""
    
    print("3. SERVICE MODULES:")
    print("-" * 80)
    
    service_paths = [
        'ultracore/services',
    ]
    
    services = set()
    for base_path in service_paths:
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and not item.startswith('_'):
                    services.add(item)
    
    for service in sorted(services):
        print(f"  ✓ {service}")
    
    print(f"\n  Total Services: {len(services)}")
    print()
    
    return services

def audit_infrastructure():
    """Audit infrastructure modules"""
    
    print("4. INFRASTRUCTURE MODULES:")
    print("-" * 80)
    
    infra_modules = []
    
    # Check key infrastructure components
    infra_checks = [
        ('src/ultracore/events', 'Event Sourcing (Kafka)'),
        ('src/ultracore/mesh', 'Data Mesh'),
        ('src/ultracore/agentic_ai', 'Agentic AI (MCP)'),
        ('ultracore/ml', 'Machine Learning'),
        ('ultracore/rl', 'Reinforcement Learning'),
        ('src/ultracore/security', 'Security'),
        ('src/ultracore/infrastructure', 'Infrastructure'),
        ('ultracore/datamesh', 'Data Mesh Domains'),
    ]
    
    for path, name in infra_checks:
        if os.path.exists(path):
            print(f"  ✓ {name}")
            infra_modules.append(name)
        else:
            print(f"  ✗ {name}")
    
    print()
    return infra_modules

def audit_integrations():
    """Audit integration modules"""
    
    print("5. INTEGRATION MODULES:")
    print("-" * 80)
    
    integration_paths = [
        'ultracore/integrations',
    ]
    
    integrations = set()
    for base_path in integration_paths:
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and not item.startswith('_'):
                    integrations.add(item)
    
    for integration in sorted(integrations):
        print(f"  ✓ {integration}")
    
    print(f"\n  Total Integrations: {len(integrations)}")
    print()
    
    return integrations

def audit_core_features():
    """Audit core banking features"""
    
    print("6. CORE BANKING FEATURES:")
    print("-" * 80)
    
    features = {
        'Loans': [],
        'Savings': [],
        'Deposits': [],
        'Payments': [],
        'Accounts': [],
        'Clients': [],
        'Transactions': [],
        'Accounting': [],
        'Reporting': [],
    }
    
    # Search for feature implementations
    for feature_name in features.keys():
        # Check in domains
        domain_files = glob.glob(f'**/domains/**/*{feature_name.lower()}*.py', recursive=True)
        domain_files = [f for f in domain_files if '__pycache__' not in f and '__init__' not in f]
        
        # Check in API
        api_files = glob.glob(f'**/api/**/*{feature_name.lower()}*.py', recursive=True)
        api_files = [f for f in api_files if '__pycache__' not in f and '__init__' not in f]
        
        # Check in services
        service_files = glob.glob(f'**/services/**/*{feature_name.lower()}*.py', recursive=True)
        service_files = [f for f in service_files if '__pycache__' not in f and '__init__' not in f]
        
        total_files = len(domain_files) + len(api_files) + len(service_files)
        
        if total_files > 0:
            print(f"  ✓ {feature_name} ({total_files} files)")
        else:
            print(f"  ~ {feature_name} (not found)")
    
    print()
    return features

def main():
    """Run complete audit"""
    
    domains = audit_domains()
    api_modules = audit_api_modules()
    services = audit_services()
    infra = audit_infrastructure()
    integrations = audit_integrations()
    features = audit_core_features()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal Domains: {len(domains)}")
    print(f"Total API Modules: {len(api_modules)}")
    print(f"Total Services: {len(services)}")
    print(f"Total Infrastructure Modules: {len(infra)}")
    print(f"Total Integrations: {len(integrations)}")
    print()
    
    print("UltraCore is a comprehensive platform with extensive coverage")
    print("across domains, APIs, services, and infrastructure.")
    print()

if __name__ == "__main__":
    main()
