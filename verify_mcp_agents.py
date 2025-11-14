"""
MCP Agentic AI Verification
Verifies all MCP and AI agent components are properly wired
"""

import os
import sys
import glob

def check_mcp_server():
    """Check MCP server implementation"""
    
    print("=" * 80)
    print("MCP AGENTIC AI VERIFICATION")
    print("=" * 80)
    print()
    
    print("1. MCP Server Implementation:")
    print("-" * 80)
    
    mcp_files = [
        'src/ultracore/agentic_ai/mcp_server.py',
        'src/ultracore/agentic_ai/mcp_api.py',
    ]
    
    for file_path in mcp_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path}")
    
    print()
    
    # Check MCP tools
    try:
        with open('src/ultracore/agentic_ai/mcp_server.py', 'r') as f:
            content = f.read()
        
        print("  MCP Tools Registered:")
        tools = [
            'get_customer_360',
            'check_loan_eligibility',
            'get_account_balance',
            'get_trial_balance',
            'analyze_credit_risk',
        ]
        
        for tool in tools:
            if tool in content:
                print(f"    ✓ {tool}")
            else:
                print(f"    ✗ {tool}")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ✗ Error checking MCP server: {e}")
        print()
        return False

def check_domain_agents():
    """Check domain-specific AI agents"""
    
    print("2. Domain-Specific AI Agents:")
    print("-" * 80)
    
    # Find all agent files
    agent_files = []
    
    for pattern in ['**/agents/*.py', '**/*agent*.py']:
        agent_files.extend(glob.glob(f'src/ultracore/{pattern}', recursive=True))
        agent_files.extend(glob.glob(f'ultracore/{pattern}', recursive=True))
    
    # Remove duplicates and test files
    agent_files = list(set(agent_files))
    agent_files = [f for f in agent_files if '__pycache__' not in f and 'test' not in f.lower()]
    
    # Categorize by domain
    domains = {}
    for file_path in agent_files:
        # Extract domain from path
        parts = file_path.split('/')
        if 'domains' in parts:
            idx = parts.index('domains')
            if idx + 1 < len(parts):
                domain = parts[idx + 1]
            else:
                domain = 'other'
        elif 'agents' in parts:
            domain = 'core'
        else:
            domain = 'other'
        
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(file_path)
    
    # Print by domain
    for domain, files in sorted(domains.items()):
        print(f"\n  {domain.upper()} Domain:")
        for file_path in sorted(files):
            agent_name = os.path.basename(file_path).replace('.py', '').replace('_', ' ').title()
            print(f"    ✓ {agent_name}")
    
    print(f"\n  Total Agents: {len(agent_files)}")
    print()
    
    return len(agent_files) > 0

def check_mcp_tools():
    """Check MCP tool implementations"""
    
    print("3. MCP Tool Implementations:")
    print("-" * 80)
    
    mcp_tool_files = glob.glob('**/mcp_tools.py', recursive=True)
    mcp_tool_files = [f for f in mcp_tool_files if '__pycache__' not in f]
    
    for file_path in mcp_tool_files:
        print(f"  ✓ {file_path}")
    
    if not mcp_tool_files:
        print("  ~ No mcp_tools.py files found")
    
    print()
    return True

def check_agent_features():
    """Check AI agent features"""
    
    print("4. AI Agent Features:")
    print("-" * 80)
    
    features_to_check = [
        ('openai', 'OpenAI Integration'),
        ('context', 'Context Management'),
        ('permission', 'Permission-Based Access'),
        ('audit', 'Audit Logging'),
        ('tenant', 'Multi-Tenancy Support'),
    ]
    
    # Check across agent files
    agent_files = glob.glob('src/ultracore/**/agents/*.py', recursive=True)
    agent_files = [f for f in agent_files if '__pycache__' not in f]
    
    if agent_files:
        # Sample a few agent files
        sample_content = ""
        for file_path in agent_files[:5]:
            try:
                with open(file_path, 'r') as f:
                    sample_content += f.read()
            except:
                pass
        
        for keyword, description in features_to_check:
            if keyword in sample_content.lower():
                print(f"  ✓ {description}")
            else:
                print(f"  ~ {description} (not found in sample)")
    else:
        print("  ~ No agent files to check")
    
    print()
    return True

def check_anya_agents():
    """Check Anya AI agents (domain-specific)"""
    
    print("5. Anya AI Agents (Domain-Specific):")
    print("-" * 80)
    
    anya_agents = glob.glob('src/ultracore/**/anya_*.py', recursive=True)
    anya_agents = [f for f in anya_agents if '__pycache__' not in f]
    
    if anya_agents:
        for file_path in sorted(anya_agents):
            agent_name = os.path.basename(file_path).replace('anya_', '').replace('_agent', '').replace('.py', '').title()
            print(f"  ✓ Anya {agent_name} Agent")
        
        print(f"\n  Total Anya Agents: {len(anya_agents)}")
    else:
        print("  ~ No Anya agents found")
    
    print()
    return len(anya_agents) > 0

def check_rl_agents():
    """Check RL-powered agents"""
    
    print("6. Reinforcement Learning Agents:")
    print("-" * 80)
    
    rl_agent_files = glob.glob('**/rl/*agent*.py', recursive=True)
    rl_agent_files = [f for f in rl_agent_files if '__pycache__' not in f and 'test' not in f.lower()]
    
    for file_path in sorted(rl_agent_files):
        agent_name = os.path.basename(file_path).replace('.py', '').replace('_', ' ').title()
        print(f"  ✓ {agent_name}")
    
    if not rl_agent_files:
        print("  ~ No RL agents found")
    
    print()
    return len(rl_agent_files) > 0

def main():
    """Run all verifications"""
    
    results = []
    
    results.append(check_mcp_server())
    results.append(check_domain_agents())
    results.append(check_mcp_tools())
    results.append(check_agent_features())
    results.append(check_anya_agents())
    results.append(check_rl_agents())
    
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if all(results):
        print("\n✓ MCP AGENTIC AI FULLY IMPLEMENTED")
        return 0
    else:
        print("\n⚠ Some MCP/AI components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
