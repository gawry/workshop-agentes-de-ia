"""
DeepEval evaluation script for RAG agent.
"""
import pandas as pd
from typing import List, Dict, Any
from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    HallucinationMetric,
    ToxicityMetric
)
from deepeval.test_case import LLMTestCase
from deepeval.dataset import EvaluationDataset
from rag_agent import PetrobrasRAGAgent
from config import GOLDEN_SET_CSV, EVALUATION_METRICS, validate_config

def load_golden_set() -> pd.DataFrame:
    """Load golden set from CSV file."""
    print(f"📊 Loading golden set from {GOLDEN_SET_CSV}")
    df = pd.read_csv(GOLDEN_SET_CSV)
    print(f"✅ Loaded {len(df)} examples")
    return df

def create_test_cases(df: pd.DataFrame, split: str = "dev", max_cases: int = 10) -> List[LLMTestCase]:
    """Create DeepEval test cases from golden set."""
    # Filter by split
    split_df = df[df['Split'] == split].copy()
    
    # Limit number of cases for demo
    if len(split_df) > max_cases:
        split_df = split_df.head(max_cases)
        print(f"⚠️ Limited to {max_cases} cases for demo")
    
    print(f"📋 Creating {len(split_df)} test cases for split '{split}'")
    
    # Initialize RAG agent
    agent = PetrobrasRAGAgent()
    
    test_cases = []
    
    for _, row in split_df.iterrows():
        try:
            # Get answer from RAG agent
            result = agent.query(row["Pergunta"])
            actual_output = result["answer"]
            
            # Get retrieval context (simplified)
            retrieval_context = []
            if "retrieved_docs" in result and result["retrieved_docs"] > 0:
                # For DeepEval, we'll use a simplified context
                retrieval_context = [f"Document from {source}" for source in result.get("sources", [])]
            
            # Create test case
            test_case = LLMTestCase(
                input=row["Pergunta"],
                actual_output=actual_output,
                expected_output=row["Resposta_Esperada"],
                retrieval_context=retrieval_context,
                metadata={
                    "id": row["ID"],
                    "categoria": row["Categoria"],
                    "fontes_obrigatorias": row["Fontes_Obrigatorias"]
                }
            )
            
            test_cases.append(test_case)
            print(f"✅ Created test case {row['ID']}: {row['Pergunta'][:50]}...")
            
        except Exception as e:
            print(f"⚠️ Error creating test case {row['ID']}: {e}")
            continue
    
    print(f"✅ Created {len(test_cases)} test cases")
    return test_cases

def create_metrics() -> List:
    """Create DeepEval metrics for evaluation."""
    metrics = [
        FaithfulnessMetric(
            threshold=EVALUATION_METRICS["faithfulness_threshold"],
            model="gpt-3.5-turbo"
        ),
        AnswerRelevancyMetric(
            threshold=EVALUATION_METRICS["relevancy_threshold"],
            model="gpt-3.5-turbo"
        ),
        HallucinationMetric(
            threshold=EVALUATION_METRICS["hallucination_threshold"],
            model="gpt-3.5-turbo"
        ),
        ToxicityMetric(
            threshold=0.5,
            model="gpt-3.5-turbo"
        )
    ]
    
    print(f"📊 Created {len(metrics)} evaluation metrics")
    return metrics

def run_evaluation(test_cases: List[LLMTestCase], metrics: List, split: str = "dev"):
    """Run DeepEval evaluation."""
    print(f"🚀 Starting DeepEval evaluation for split '{split}'...")
    print(f"📊 Evaluating {len(test_cases)} test cases with {len(metrics)} metrics")
    
    try:
        # Run evaluation
        results = evaluate(
            test_cases=test_cases,
            metrics=metrics
        )
        
        print("✅ Evaluation completed successfully!")
        return results
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        raise

def print_evaluation_summary(test_cases: List[LLMTestCase], metrics: List):
    """Print detailed evaluation summary."""
    print("\n📊 DEEP EVAL EVALUATION SUMMARY")
    print("=" * 60)
    
    # Calculate overall pass rates
    total_cases = len(test_cases)
    
    print(f"\n📋 Test Cases: {total_cases}")
    print(f"📊 Metrics: {len(metrics)}")
    
    # Print metric details
    for metric in metrics:
        metric_name = metric.__class__.__name__
        threshold = getattr(metric, 'threshold', 'N/A')
        
        # Calculate pass rate for this metric
        passed = 0
        for test_case in test_cases:
            if hasattr(test_case, 'metrics') and metric_name in test_case.metrics:
                score = test_case.metrics[metric_name].score
                if score >= threshold:
                    passed += 1
        
        pass_rate = (passed / total_cases) * 100 if total_cases > 0 else 0
        
        print(f"\n{metric_name}:")
        print(f"  Threshold: {threshold}")
        print(f"  Passed: {passed}/{total_cases} ({pass_rate:.1f}%)")
    
    # Print individual test case results
    print(f"\n📝 INDIVIDUAL TEST CASE RESULTS")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. ID: {test_case.metadata.get('id', 'N/A')}")
        print(f"   Question: {test_case.input[:80]}...")
        print(f"   Category: {test_case.metadata.get('categoria', 'N/A')}")
        
        # Print metric scores
        if hasattr(test_case, 'metrics'):
            for metric_name, metric_result in test_case.metrics.items():
                score = getattr(metric_result, 'score', 'N/A')
                print(f"   {metric_name}: {score}")
        else:
            print("   No metrics available")

def save_evaluation_report(test_cases: List[LLMTestCase], output_file: str = "deepeval_report.html"):
    """Save evaluation report to HTML file."""
    try:
        from deepeval.utils import save_html_report
        
        save_html_report(
            test_cases=test_cases,
            file_path=output_file
        )
        print(f"📄 HTML report saved to: {output_file}")
        
    except Exception as e:
        print(f"⚠️ Could not save HTML report: {e}")

def main():
    """Main evaluation function."""
    print("🔍 DeepEval RAG Evaluation")
    print("=" * 40)
    
    try:
        # Validate configuration
        validate_config()
        
        # Load golden set
        df = load_golden_set()
        
        # Create test cases
        test_cases = create_test_cases(df, split="dev", max_cases=5)  # Limit for demo
        
        if not test_cases:
            print("❌ No test cases created. Exiting.")
            return
        
        # Create metrics
        metrics = create_metrics()
        
        # Run evaluation
        results = run_evaluation(test_cases, metrics, split="dev")
        
        # Print summary
        print_evaluation_summary(test_cases, metrics)
        
        # Save HTML report
        save_evaluation_report(test_cases)
        
        print("\n🎉 DeepEval evaluation completed successfully!")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()
