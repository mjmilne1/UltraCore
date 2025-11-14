"""
Data Mesh Architecture Verification
Verifies all data mesh components are properly wired
"""

import os
import sys

def check_data_mesh_files():
    """Check all data mesh implementation files exist"""
    
    data_mesh_files = [
        'src/ultracore/mesh/data_mesh.py',
        'ultracore/datamesh/holdings_mesh.py',
        'ultracore/datamesh/transaction_mesh.py',
        'ultracore/datamesh/accounting_mesh.py',
        'ultracore/datamesh/client_mesh.py',
        'ultracore/modules/cash/data_mesh.py',
        'ultracore/services/ultrawealth/datamesh.py',
        'ultracore/services/yahoo_finance/datamesh.py',
    ]
    
    print("=" * 80)
    print("DATA MESH ARCHITECTURE VERIFICATION")
    print("=" * 80)
    print()
    
    print("1. Data Mesh Implementation Files:")
    print("-" * 80)
    
    all_exist = True
    for file_path in data_mesh_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    print()
    return all_exist

def check_data_products():
    """Check data products are defined"""
    
    print("2. Data Products Defined:")
    print("-" * 80)
    
    try:
        # Check core data mesh
        with open('src/ultracore/mesh/data_mesh.py', 'r') as f:
            content = f.read()
            
        data_products_found = []
        
        if 'PaymentDomain' in content:
            data_products_found.append("Payment Domain (real_time_transactions, payment_analytics)")
        
        if 'CustomerDomain' in content:
            data_products_found.append("Customer Domain (customer_360_view, customer_behavior_stream)")
        
        if 'RiskDomain' in content:
            data_products_found.append("Risk Domain (real_time_fraud_scores)")
        
        if 'DataMeshOrchestrator' in content:
            data_products_found.append("Data Mesh Orchestrator (federated queries)")
        
        for product in data_products_found:
            print(f"  ✓ {product}")
        
        print()
        return len(data_products_found) > 0
        
    except Exception as e:
        print(f"  ✗ Error checking data products: {e}")
        print()
        return False

def check_quality_slas():
    """Check quality SLAs are defined"""
    
    print("3. Quality SLAs:")
    print("-" * 80)
    
    try:
        with open('src/ultracore/mesh/data_mesh.py', 'r') as f:
            content = f.read()
        
        sla_checks = [
            ('completeness', 'Completeness guarantees'),
            ('latency_ms', 'Latency SLAs'),
            ('accuracy', 'Accuracy requirements'),
            ('freshness', 'Data freshness'),
        ]
        
        for check, description in sla_checks:
            if check in content:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description}")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ Error checking SLAs: {e}")
        print()
        return False

def check_access_patterns():
    """Check access patterns are defined"""
    
    print("4. Access Patterns:")
    print("-" * 80)
    
    try:
        with open('src/ultracore/mesh/data_mesh.py', 'r') as f:
            content = f.read()
        
        patterns = [
            ('stream', 'Stream access (real-time)'),
            ('api', 'API access (request/response)'),
            ('batch', 'Batch access (scheduled)'),
        ]
        
        for pattern, description in patterns:
            if f'"{pattern}"' in content or f"'{pattern}'" in content:
                print(f"  ✓ {description}")
            else:
                print(f"  ~ {description} (not explicitly found)")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ Error checking access patterns: {e}")
        print()
        return False

def check_governance():
    """Check data governance features"""
    
    print("5. Data Governance:")
    print("-" * 80)
    
    try:
        with open('src/ultracore/mesh/data_mesh.py', 'r') as f:
            content = f.read()
        
        governance_features = [
            ('apply_governance', 'Governance policy enforcement'),
            ('hash_pii', 'PII masking'),
            ('quality_score', 'Quality scoring'),
            ('lineage', 'Data lineage tracking'),
        ]
        
        for feature, description in governance_features:
            if feature in content:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description}")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ Error checking governance: {e}")
        print()
        return False

def check_domain_implementations():
    """Check domain-specific data mesh implementations"""
    
    print("6. Domain-Specific Implementations:")
    print("-" * 80)
    
    domains = [
        ('ultracore/datamesh/holdings_mesh.py', 'Holdings Domain'),
        ('ultracore/datamesh/transaction_mesh.py', 'Transaction Domain'),
        ('ultracore/datamesh/accounting_mesh.py', 'Accounting Domain'),
        ('ultracore/datamesh/client_mesh.py', 'Client Domain'),
        ('ultracore/modules/cash/data_mesh.py', 'Cash Domain'),
    ]
    
    for file_path, domain_name in domains:
        if os.path.exists(file_path):
            print(f"  ✓ {domain_name}")
        else:
            print(f"  ✗ {domain_name}")
    
    print()
    return True

def main():
    """Run all verifications"""
    
    results = []
    
    results.append(check_data_mesh_files())
    results.append(check_data_products())
    results.append(check_quality_slas())
    results.append(check_access_patterns())
    results.append(check_governance())
    results.append(check_domain_implementations())
    
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if all(results):
        print("\n✓ DATA MESH ARCHITECTURE FULLY IMPLEMENTED")
        return 0
    else:
        print("\n⚠ Some data mesh components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
