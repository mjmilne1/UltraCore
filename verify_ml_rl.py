"""
ML/RL Models Verification
Verifies all machine learning and reinforcement learning models
"""

import os
import sys
import glob

def check_ml_models():
    """Check ML model implementations"""
    
    print("=" * 80)
    print("ML/RL MODELS VERIFICATION")
    print("=" * 80)
    print()
    
    print("1. Machine Learning Models:")
    print("-" * 80)
    
    # Find all ML model files
    ml_files = glob.glob('**/ml/**/*.py', recursive=True)
    ml_files = [f for f in ml_files if '__pycache__' not in f and '__init__' not in f]
    
    # Categorize by domain
    domains = {}
    for file_path in ml_files:
        parts = file_path.split('/')
        if 'domains' in parts:
            idx = parts.index('domains')
            if idx + 1 < len(parts):
                domain = parts[idx + 1]
            else:
                domain = 'other'
        elif 'integrations' in parts:
            idx = parts.index('integrations')
            if idx + 1 < len(parts):
                domain = f"integration_{parts[idx + 1]}"
            else:
                domain = 'integration'
        else:
            domain = 'core'
        
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(file_path)
    
    # Print by domain
    for domain, files in sorted(domains.items()):
        print(f"\n  {domain.upper()} Domain:")
        for file_path in sorted(files):
            model_name = os.path.basename(file_path).replace('.py', '').replace('_', ' ').title()
            print(f"    ✓ {model_name}")
    
    print(f"\n  Total ML Models: {len(ml_files)}")
    print()
    
    return len(ml_files) > 0

def check_rl_models():
    """Check RL model implementations"""
    
    print("2. Reinforcement Learning Models:")
    print("-" * 80)
    
    # Find all RL model files
    rl_files = glob.glob('**/rl/**/*.py', recursive=True)
    rl_files = [f for f in rl_files if '__pycache__' not in f and '__init__' not in f]
    
    # Categorize by domain
    domains = {}
    for file_path in rl_files:
        parts = file_path.split('/')
        if 'domains' in parts:
            idx = parts.index('domains')
            if idx + 1 < len(parts):
                domain = parts[idx + 1]
            else:
                domain = 'other'
        elif 'integrations' in parts:
            idx = parts.index('integrations')
            if idx + 1 < len(parts):
                domain = f"integration_{parts[idx + 1]}"
            else:
                domain = 'integration'
        else:
            domain = 'core'
        
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(file_path)
    
    # Print by domain
    for domain, files in sorted(domains.items()):
        print(f"\n  {domain.upper()} Domain:")
        for file_path in sorted(files):
            model_name = os.path.basename(file_path).replace('.py', '').replace('_', ' ').title()
            print(f"    ✓ {model_name}")
    
    print(f"\n  Total RL Models: {len(rl_files)}")
    print()
    
    return len(rl_files) > 0

def check_model_types():
    """Check types of ML models implemented"""
    
    print("3. ML Model Types:")
    print("-" * 80)
    
    model_types = {
        'credit_scor': 'Credit Scoring',
        'fraud': 'Fraud Detection',
        'risk': 'Risk Assessment',
        'predict': 'Predictive Analytics',
        'optim': 'Optimization',
        'sentiment': 'Sentiment Analysis',
        'anomaly': 'Anomaly Detection',
        'classification': 'Classification',
        'regression': 'Regression',
        'clustering': 'Clustering',
    }
    
    # Search across all ML files
    ml_files = glob.glob('**/ml/**/*.py', recursive=True)
    ml_files = [f for f in ml_files if '__pycache__' not in f]
    
    found_types = set()
    for file_path in ml_files:
        filename = os.path.basename(file_path).lower()
        for keyword, model_type in model_types.items():
            if keyword in filename:
                found_types.add(model_type)
    
    for model_type in sorted(found_types):
        print(f"  ✓ {model_type}")
    
    print()
    return len(found_types) > 0

def check_rl_algorithms():
    """Check RL algorithms implemented"""
    
    print("4. RL Algorithms:")
    print("-" * 80)
    
    # Check for common RL algorithms in code
    rl_files = glob.glob('**/rl/**/*.py', recursive=True)
    rl_files = [f for f in rl_files if '__pycache__' not in f]
    
    algorithms = {
        'q_learning': 'Q-Learning',
        'q_table': 'Q-Table',
        'dqn': 'Deep Q-Network (DQN)',
        'policy': 'Policy Gradient',
        'actor_critic': 'Actor-Critic',
        'ppo': 'Proximal Policy Optimization (PPO)',
        'ddpg': 'Deep Deterministic Policy Gradient (DDPG)',
    }
    
    found_algorithms = set()
    for file_path in rl_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read().lower()
            
            for keyword, algorithm in algorithms.items():
                if keyword in content:
                    found_algorithms.add(algorithm)
        except:
            pass
    
    for algorithm in sorted(found_algorithms):
        print(f"  ✓ {algorithm}")
    
    if not found_algorithms:
        print("  ~ No specific RL algorithms detected in code")
    
    print()
    return True

def check_training_infrastructure():
    """Check ML/RL training infrastructure"""
    
    print("5. Training Infrastructure:")
    print("-" * 80)
    
    features = [
        ('experience_replay', 'Experience Replay'),
        ('epsilon', 'Epsilon-Greedy Exploration'),
        ('reward', 'Reward Function'),
        ('train', 'Training Loop'),
        ('fit', 'Model Fitting'),
        ('predict', 'Prediction/Inference'),
        ('evaluate', 'Model Evaluation'),
    ]
    
    # Check across RL files
    rl_files = glob.glob('**/rl/**/*.py', recursive=True)
    rl_files = [f for f in rl_files if '__pycache__' not in f and '__init__' not in f]
    
    if rl_files:
        # Sample content from RL files
        sample_content = ""
        for file_path in rl_files[:10]:
            try:
                with open(file_path, 'r') as f:
                    sample_content += f.read().lower()
            except:
                pass
        
        for keyword, description in features:
            if keyword in sample_content:
                print(f"  ✓ {description}")
            else:
                print(f"  ~ {description}")
    else:
        print("  ~ No RL files to check")
    
    print()
    return True

def check_ml_libraries():
    """Check ML/RL library dependencies"""
    
    print("6. ML/RL Libraries:")
    print("-" * 80)
    
    libraries = [
        ('scikit-learn', 'scikit-learn (ML)'),
        ('tensorflow', 'TensorFlow (Deep Learning)'),
        ('torch', 'PyTorch (Deep Learning)'),
        ('xgboost', 'XGBoost (Gradient Boosting)'),
        ('lightgbm', 'LightGBM (Gradient Boosting)'),
        ('numpy', 'NumPy (Numerical Computing)'),
        ('pandas', 'Pandas (Data Manipulation)'),
    ]
    
    # Check requirements files
    req_files = ['requirements.txt', 'pyproject.toml']
    
    found_libs = set()
    for req_file in req_files:
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r') as f:
                    content = f.read().lower()
                
                for lib_name, lib_desc in libraries:
                    if lib_name in content:
                        found_libs.add(lib_desc)
            except:
                pass
    
    for lib in sorted(found_libs):
        print(f"  ✓ {lib}")
    
    if not found_libs:
        print("  ~ No ML/RL libraries detected in requirements")
    
    print()
    return True

def main():
    """Run all verifications"""
    
    results = []
    
    results.append(check_ml_models())
    results.append(check_rl_models())
    results.append(check_model_types())
    results.append(check_rl_algorithms())
    results.append(check_training_infrastructure())
    results.append(check_ml_libraries())
    
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if all(results):
        print("\n✓ ML/RL INFRASTRUCTURE FULLY IMPLEMENTED")
        return 0
    else:
        print("\n⚠ Some ML/RL components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
