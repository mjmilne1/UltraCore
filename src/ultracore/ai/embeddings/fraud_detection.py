"""
UltraCore Embeddings Engine - Fraud Detection & Semantic Search
Advanced ML with OpenAI Embeddings
"""

import numpy as np
from openai import OpenAI
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import json
from datetime import datetime, timedelta
from decimal import Decimal

class EmbeddingsFraudDetector:
    """Detect fraud using embeddings similarity"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-large"  # 3072 dimensions
        
        # Store embeddings of known patterns
        self.fraud_patterns = []
        self.legitimate_patterns = []
        self.customer_profiles = {}
        
    async def embed_transaction(self, transaction: Dict[str, Any]) -> np.ndarray:
        """Convert transaction to embedding"""
        
        # Create rich text description
        text = f"""
        Transaction: {transaction.get('type', 'transfer')}
        Amount: ${transaction.get('amount', 0)} AUD
        Recipient: {transaction.get('recipient', 'unknown')}
        Location: {transaction.get('location', 'Australia')}
        Time: {transaction.get('timestamp', datetime.now())}
        Device: {transaction.get('device', 'unknown')}
        IP: {transaction.get('ip', 'unknown')}
        Description: {transaction.get('description', '')}
        Customer history: {transaction.get('customer_history', 'new')}
        """
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        return np.array(response.data[0].embedding)
    
    async def check_fraud_similarity(
        self,
        transaction: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Check similarity to known fraud patterns"""
        
        # Get transaction embedding
        trans_embedding = await self.embed_transaction(transaction)
        
        # Load known fraud patterns (would be from database)
        if not self.fraud_patterns:
            await self.load_fraud_patterns()
        
        # Calculate similarities
        fraud_scores = []
        for pattern in self.fraud_patterns:
            similarity = cosine_similarity(
                [trans_embedding],
                [pattern['embedding']]
            )[0][0]
            fraud_scores.append((similarity, pattern['type']))
        
        # Get highest fraud similarity
        if fraud_scores:
            max_score, fraud_type = max(fraud_scores, key=lambda x: x[0])
        else:
            max_score, fraud_type = 0.0, "none"
        
        # Check legitimate patterns
        legit_scores = []
        for pattern in self.legitimate_patterns:
            similarity = cosine_similarity(
                [trans_embedding],
                [pattern['embedding']]
            )[0][0]
            legit_scores.append(similarity)
        
        max_legit = max(legit_scores) if legit_scores else 0.0
        
        # Calculate fraud risk
        fraud_risk = max_score - max_legit
        
        # Determine risk level
        if fraud_risk > 0.7:
            risk_level = "high"
        elif fraud_risk > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return fraud_risk, risk_level
    
    async def detect_anomaly(
        self,
        customer_id: str,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect anomalous behavior for customer"""
        
        # Get customer profile embedding
        if customer_id not in self.customer_profiles:
            await self.build_customer_profile(customer_id)
        
        profile_embedding = self.customer_profiles[customer_id]['embedding']
        trans_embedding = await self.embed_transaction(transaction)
        
        # Calculate deviation from normal behavior
        similarity = cosine_similarity(
            [trans_embedding],
            [profile_embedding]
        )[0][0]
        
        anomaly_score = 1 - similarity
        
        return {
            "anomaly_score": float(anomaly_score),
            "is_anomalous": anomaly_score > 0.6,
            "deviation_level": "high" if anomaly_score > 0.7 else "medium" if anomaly_score > 0.4 else "low",
            "recommendation": self.get_recommendation(anomaly_score)
        }
    
    async def build_customer_profile(self, customer_id: str):
        """Build customer behavior profile"""
        
        # Get customer transaction history (mock)
        transactions = [
            "Regular salary deposit $5000 from employer",
            "Weekly grocery shopping $150-200 at Woolworths",
            "Monthly rent payment $2000 via BPAY",
            "Occasional PayID transfers $50-100 to friends",
            "Quarterly utilities $300-400"
        ]
        
        # Create profile text
        profile_text = f"""
        Customer {customer_id} typical behavior:
        {' '.join(transactions)}
        Location: Sydney, Australia
        Account age: 3 years
        Risk profile: low
        """
        
        # Get embedding
        response = self.client.embeddings.create(
            model=self.model,
            input=profile_text
        )
        
        self.customer_profiles[customer_id] = {
            "embedding": np.array(response.data[0].embedding),
            "created": datetime.now().isoformat()
        }
    
    async def load_fraud_patterns(self):
        """Load known fraud pattern embeddings"""
        
        # Common Australian fraud patterns
        fraud_texts = [
            "Sudden large transfer to overseas account in high-risk country",
            "Multiple small transactions just under reporting threshold $10000",
            "Rapid sequence of ATM withdrawals across different cities",
            "Purchase of gift cards in large amounts",
            "Wire transfer to cryptocurrency exchange followed by immediate withdrawal",
            "BPAY payment to unknown biller with suspicious reference",
            "Account takeover with changed phone and address same day"
        ]
        
        for text in fraud_texts:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            self.fraud_patterns.append({
                "embedding": np.array(response.data[0].embedding),
                "type": text.split()[0].lower()
            })
        
        # Legitimate patterns
        legit_texts = [
            "Regular salary payment from known employer",
            "Grocery shopping at major Australian supermarket",
            "BPAY payment to utility company",
            "Rent payment to real estate agent",
            "PayID transfer to family member"
        ]
        
        for text in legit_texts:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            self.legitimate_patterns.append({
                "embedding": np.array(response.data[0].embedding),
                "type": "legitimate"
            })
    
    def get_recommendation(self, anomaly_score: float) -> str:
        """Get action recommendation"""
        if anomaly_score > 0.8:
            return "BLOCK: Require manual verification"
        elif anomaly_score > 0.6:
            return "CHALLENGE: Request 2FA confirmation"
        elif anomaly_score > 0.4:
            return "MONITOR: Flag for review"
        else:
            return "APPROVE: Normal behavior"


class SemanticSearch:
    """Semantic search for customer queries"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.model = "text-embedding-3-small"  # Faster, cheaper
        
        # Knowledge base embeddings
        self.knowledge_base = []
        
    async def index_knowledge_base(self):
        """Index Australian banking knowledge"""
        
        # Australian banking FAQs
        knowledge = [
            {
                "question": "How do I set up PayID?",
                "answer": "You can register your mobile number or email as a PayID through your bank's app or online banking. Link it to your account and others can pay you instantly using just your PayID."
            },
            {
                "question": "What is BPAY?",
                "answer": "BPAY is an Australian bill payment service. Use the biller code and reference number from your bill to pay through your online banking."
            },
            {
                "question": "How do I find my BSB?",
                "answer": "Your BSB (Bank State Branch) is a 6-digit number that identifies your bank and branch. Find it on your bank statement or in your online banking."
            },
            {
                "question": "What are Osko payments?",
                "answer": "Osko enables fast payments between participating Australian banks, usually arriving in under a minute, available 24/7 including weekends."
            },
            {
                "question": "How much can I transfer with PayID?",
                "answer": "PayID daily limits vary by bank, typically $1,000-$20,000 for personal accounts. Check your bank's specific limits."
            }
        ]
        
        # Create embeddings
        for item in knowledge:
            response = self.client.embeddings.create(
                model=self.model,
                input=item["question"] + " " + item["answer"]
            )
            
            item["embedding"] = np.array(response.data[0].embedding)
            self.knowledge_base.append(item)
    
    async def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base semantically"""
        
        # Get query embedding
        response = self.client.embeddings.create(
            model=self.model,
            input=query
        )
        query_embedding = np.array(response.data[0].embedding)
        
        # Calculate similarities
        similarities = []
        for item in self.knowledge_base:
            sim = cosine_similarity(
                [query_embedding],
                [item["embedding"]]
            )[0][0]
            similarities.append((sim, item))
        
        # Sort and return top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        return [
            {
                "question": item["question"],
                "answer": item["answer"],
                "relevance": float(score)
            }
            for score, item in similarities[:top_k]
        ]
