#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integrated Multi-Layer Validation Pipeline
Combines all 5 validation layers for comprehensive answer quality assurance
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from nli_validator import OllamaNLIValidator, ValidationResult as NLIResult
from completeness_checker import CompletenessChecker, CompletenessResult
from cross_reference_validator import CrossReferenceValidator, CrossReferenceResult
from self_consistency import SelfConsistencyValidator, ConsistencyResult
from chain_of_verification import ChainOfVerification, CoVeResult

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class ValidationScore:
    """Validation scores from all layers"""
    layer_1_nli: float
    layer_2_completeness: float
    layer_3_cross_reference: float
    layer_4_self_consistency: float
    layer_5_cove: float
    overall_score: float
    is_valid: bool


@dataclass
class IntegratedValidationResult:
    """Complete validation result from all layers"""
    question: str
    answer: str
    context: str
    retrieved_chunks: List[Dict]

    # Layer results
    nli_result: Optional[NLIResult]
    completeness_result: Optional[CompletenessResult]
    cross_ref_result: Optional[CrossReferenceResult]
    consistency_result: Optional[ConsistencyResult]
    cove_result: Optional[CoVeResult]

    # Summary
    validation_score: ValidationScore
    timestamp: str
    enabled_layers: List[str]


class MultiLayerValidator:
    """
    Integrated Multi-Layer Validation Pipeline

    Layers:
    1. NLI Hallucination Detection
    2. Completeness Check
    3. Cross-Reference Validation
    4. Self-Consistency (optional - expensive)
    5. Chain-of-Verification (optional - expensive)
    """

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434",
        enable_self_consistency: bool = False,
        enable_cove: bool = False
    ):
        """
        Initialize multi-layer validator

        Args:
            model_name: Ollama model name
            ollama_url: Ollama server URL
            enable_self_consistency: Enable Layer 4 (expensive)
            enable_cove: Enable Layer 5 (expensive)
        """
        print("\n" + "=" * 80)
        print("🚀 INITIALIZING MULTI-LAYER VALIDATION PIPELINE")
        print("=" * 80)
        print(f"\nConfiguration:")
        print(f"  Model: {model_name}")
        print(f"  Ollama URL: {ollama_url}")
        print(f"  Layer 4 (Self-Consistency): {'✅ ENABLED' if enable_self_consistency else '❌ DISABLED'}")
        print(f"  Layer 5 (CoVe): {'✅ ENABLED' if enable_cove else '❌ DISABLED'}")
        print()

        self.enable_self_consistency = enable_self_consistency
        self.enable_cove = enable_cove

        # Initialize validators
        print("📦 Loading validation layers...")
        print()

        self.nli_validator = OllamaNLIValidator(
            model_name=model_name,
            ollama_url=ollama_url
        )

        self.completeness_checker = CompletenessChecker(
            model_name=model_name,
            ollama_url=ollama_url
        )

        self.cross_ref_validator = CrossReferenceValidator(
            min_support=1
        )

        if enable_self_consistency:
            self.consistency_validator = SelfConsistencyValidator(
                model_name=model_name,
                ollama_url=ollama_url,
                num_generations=3  # Reduced for performance
            )

        if enable_cove:
            self.cove = ChainOfVerification(
                model_name=model_name,
                ollama_url=ollama_url,
                num_verifications=3  # Reduced for performance
            )

        print()
        print("=" * 80)
        print("✅ VALIDATION PIPELINE READY!")
        print("=" * 80)

    def validate_answer(
        self,
        question: str,
        answer: str,
        context: str,
        retrieved_chunks: List[Dict]
    ) -> IntegratedValidationResult:
        """
        Run complete multi-layer validation

        Args:
            question: User question
            answer: Generated answer
            context: Retrieved context
            retrieved_chunks: List of source chunks

        Returns:
            IntegratedValidationResult
        """
        print("\n\n" + "🔍" * 40)
        print("MULTI-LAYER VALIDATION PIPELINE")
        print("🔍" * 40)
        print(f"\nQuestion: {question}")
        print(f"Answer length: {len(answer)} chars")
        print(f"Context length: {len(context)} chars")
        print(f"Source chunks: {len(retrieved_chunks)}")

        enabled_layers = []

        # Layer 1: NLI Hallucination Detection
        print("\n" + "─" * 80)
        print("LAYER 1: NLI Hallucination Detection")
        print("─" * 80)
        nli_result = self.nli_validator.validate_answer(answer, context)
        enabled_layers.append("Layer 1: NLI")

        # Layer 2: Completeness Check
        print("\n" + "─" * 80)
        print("LAYER 2: Completeness Check")
        print("─" * 80)
        completeness_result = self.completeness_checker.check_completeness(question, answer)
        enabled_layers.append("Layer 2: Completeness")

        # Layer 3: Cross-Reference Validation
        print("\n" + "─" * 80)
        print("LAYER 3: Cross-Reference Validation")
        print("─" * 80)
        cross_ref_result = self.cross_ref_validator.validate_facts(answer, retrieved_chunks)
        enabled_layers.append("Layer 3: Cross-Reference")

        # Layer 4: Self-Consistency (optional)
        consistency_result = None
        if self.enable_self_consistency:
            print("\n" + "─" * 80)
            print("LAYER 4: Self-Consistency")
            print("─" * 80)
            consistency_result = self.consistency_validator.validate_with_self_consistency(
                question, context
            )
            enabled_layers.append("Layer 4: Self-Consistency")

        # Layer 5: Chain-of-Verification (optional)
        cove_result = None
        if self.enable_cove:
            print("\n" + "─" * 80)
            print("LAYER 5: Chain-of-Verification")
            print("─" * 80)
            cove_result = self.cove.verify_answer(question, context)
            enabled_layers.append("Layer 5: CoVe")

        # Calculate overall validation score
        validation_score = self._calculate_validation_score(
            nli_result,
            completeness_result,
            cross_ref_result,
            consistency_result,
            cove_result
        )

        result = IntegratedValidationResult(
            question=question,
            answer=answer,
            context=context,
            retrieved_chunks=retrieved_chunks,
            nli_result=nli_result,
            completeness_result=completeness_result,
            cross_ref_result=cross_ref_result,
            consistency_result=consistency_result,
            cove_result=cove_result,
            validation_score=validation_score,
            timestamp=datetime.now().isoformat(),
            enabled_layers=enabled_layers
        )

        print("\n" + "🔍" * 40)
        print("VALIDATION COMPLETE")
        print("🔍" * 40)
        print(f"\nOverall Validation Score: {validation_score.overall_score:.0%}")
        print(f"Is Valid: {'✅ YES' if validation_score.is_valid else '❌ NO'}")

        return result

    def _calculate_validation_score(
        self,
        nli_result: NLIResult,
        completeness_result: CompletenessResult,
        cross_ref_result: CrossReferenceResult,
        consistency_result: Optional[ConsistencyResult],
        cove_result: Optional[CoVeResult]
    ) -> ValidationScore:
        """Calculate overall validation score"""

        # Layer 1: NLI (1.0 - hallucination_rate)
        layer_1_score = 1.0 - nli_result.hallucination_rate

        # Layer 2: Completeness
        layer_2_score = completeness_result.completeness_score

        # Layer 3: Cross-Reference (reliable_facts / total_facts)
        layer_3_score = (
            cross_ref_result.reliable_facts / cross_ref_result.total_facts
            if cross_ref_result.total_facts > 0 else 0.5
        )

        # Layer 4: Self-Consistency (if enabled)
        layer_4_score = (
            consistency_result.average_agreement
            if consistency_result else 0.0
        )

        # Layer 5: CoVe (if enabled)
        layer_5_score = (
            cove_result.confidence_improvement
            if cove_result else 0.0
        )

        # Weighted average (prioritize always-on layers)
        weights = {
            "layer_1": 0.30,  # NLI - critical
            "layer_2": 0.30,  # Completeness - critical
            "layer_3": 0.25,  # Cross-ref - important
            "layer_4": 0.10 if consistency_result else 0.0,  # Self-consistency - optional
            "layer_5": 0.05 if cove_result else 0.0   # CoVe - optional
        }

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}

        overall_score = (
            layer_1_score * weights["layer_1"] +
            layer_2_score * weights["layer_2"] +
            layer_3_score * weights["layer_3"] +
            layer_4_score * weights["layer_4"] +
            layer_5_score * weights["layer_5"]
        )

        # Valid if overall score >= 0.75 (75%)
        is_valid = overall_score >= 0.75

        return ValidationScore(
            layer_1_nli=layer_1_score,
            layer_2_completeness=layer_2_score,
            layer_3_cross_reference=layer_3_score,
            layer_4_self_consistency=layer_4_score,
            layer_5_cove=layer_5_score,
            overall_score=overall_score,
            is_valid=is_valid
        )

    def format_validation_report(self, result: IntegratedValidationResult) -> str:
        """Format complete validation report"""
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📋 INTEGRATED MULTI-LAYER VALIDATION REPORT")
        lines.append("=" * 80)

        lines.append(f"\n❓ Question: {result.question}")
        lines.append(f"🕒 Timestamp: {result.timestamp}")
        lines.append(f"📊 Enabled Layers: {len(result.enabled_layers)}")
        for layer in result.enabled_layers:
            lines.append(f"   ✓ {layer}")

        lines.append("\n" + "=" * 80)
        lines.append("VALIDATION SCORES")
        lines.append("=" * 80)

        lines.append(f"\nLayer 1 (NLI):              {result.validation_score.layer_1_nli:.0%}")
        lines.append(f"Layer 2 (Completeness):     {result.validation_score.layer_2_completeness:.0%}")
        lines.append(f"Layer 3 (Cross-Reference):  {result.validation_score.layer_3_cross_reference:.0%}")

        if result.consistency_result:
            lines.append(f"Layer 4 (Self-Consistency): {result.validation_score.layer_4_self_consistency:.0%}")

        if result.cove_result:
            lines.append(f"Layer 5 (CoVe):             {result.validation_score.layer_5_cove:.0%}")

        lines.append(f"\n{'─' * 80}")
        lines.append(f"OVERALL SCORE:              {result.validation_score.overall_score:.0%}")
        lines.append(f"IS VALID:                   {'✅ YES' if result.validation_score.is_valid else '❌ NO'}")

        # Layer details
        lines.append("\n" + "=" * 80)
        lines.append("LAYER DETAILS")
        lines.append("=" * 80)

        # Layer 1
        lines.append("\n[Layer 1] NLI Hallucination Detection:")
        lines.append(f"  Hallucination rate: {result.nli_result.hallucination_rate:.0%}")
        lines.append(f"  Confidence: {result.nli_result.overall_confidence:.2f}")
        lines.append(f"  Valid: {'✅' if result.nli_result.is_valid else '❌'}")

        # Layer 2
        lines.append("\n[Layer 2] Completeness Check:")
        lines.append(f"  Completeness: {result.completeness_result.completeness_score:.0%}")
        lines.append(f"  Addressed aspects: {result.completeness_result.addressed_aspects}/{result.completeness_result.total_aspects}")
        lines.append(f"  Complete: {'✅' if result.completeness_result.is_complete else '❌'}")

        # Layer 3
        lines.append("\n[Layer 3] Cross-Reference Validation:")
        lines.append(f"  Reliable facts: {result.cross_ref_result.reliable_facts}/{result.cross_ref_result.total_facts}")
        lines.append(f"  Average support: {result.cross_ref_result.average_support:.1f} chunks")
        lines.append(f"  Valid: {'✅' if result.cross_ref_result.is_valid else '❌'}")

        # Layer 4
        if result.consistency_result:
            lines.append("\n[Layer 4] Self-Consistency:")
            lines.append(f"  Generations: {result.consistency_result.num_generations}")
            lines.append(f"  Consensus facts: {len(result.consistency_result.consensus_facts)}")
            lines.append(f"  Agreement: {result.consistency_result.average_agreement:.0%}")
            lines.append(f"  Consistent: {'✅' if result.consistency_result.is_consistent else '❌'}")

        # Layer 5
        if result.cove_result:
            lines.append("\n[Layer 5] Chain-of-Verification:")
            lines.append(f"  Verifications: {len(result.cove_result.verification_questions)}")
            lines.append(f"  Confidence: {result.cove_result.confidence_improvement:.0%}")
            lines.append(f"  Verified: {'✅' if result.cove_result.is_verified else '❌'}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def export_validation_result(self, result: IntegratedValidationResult, filepath: str):
        """Export validation result to JSON"""
        # Convert to dict (simplified - exclude complex objects)
        export_data = {
            "question": result.question,
            "answer": result.answer[:500],  # Truncate for file size
            "validation_score": asdict(result.validation_score),
            "timestamp": result.timestamp,
            "enabled_layers": result.enabled_layers,
            "layer_summaries": {
                "nli": {
                    "hallucination_rate": result.nli_result.hallucination_rate,
                    "confidence": result.nli_result.overall_confidence,
                    "is_valid": result.nli_result.is_valid
                },
                "completeness": {
                    "score": result.completeness_result.completeness_score,
                    "is_complete": result.completeness_result.is_complete
                },
                "cross_reference": {
                    "reliable_facts": result.cross_ref_result.reliable_facts,
                    "total_facts": result.cross_ref_result.total_facts,
                    "is_valid": result.cross_ref_result.is_valid
                }
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Validation result exported to: {filepath}")


def test_validation_pipeline():
    """Test integrated validation pipeline"""
    print("\n\n")
    print("*" * 80)
    print("TESTING INTEGRATED MULTI-LAYER VALIDATION PIPELINE")
    print("*" * 80)

    # Initialize pipeline (without expensive layers for testing)
    validator = MultiLayerValidator(
        model_name="qwen3:8b",
        enable_self_consistency=False,  # Disable for faster testing
        enable_cove=False  # Disable for faster testing
    )

    # Test data
    question = "Đăng ký kết hôn cần giấy tờ gì?"

    answer = """
Để đăng ký kết hôn, bạn cần chuẩn bị các giấy tờ sau:
1. Giấy tờ tùy thân (CMND/CCCD) - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính
3. Giấy khám sức khỏe tiền hôn nhân - 01 bản chính

Thời gian xử lý: Trong ngày làm việc.
"""

    context = """
Hồ sơ đăng ký kết hôn bao gồm:
1. Giấy tờ tùy thân (CMND/CCCD/Hộ chiếu) - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính
3. Giấy khám sức khỏe tiền hôn nhân - 01 bản chính

Thời gian giải quyết: Trong ngày làm việc, tối đa 3 ngày.
"""

    chunks = [
        {
            "chunk_id": "chunk_001",
            "content": "Giấy tờ tùy thân CMND CCCD 02 bản sao giấy xác nhận tình trạng hôn nhân 01 bản chính"
        },
        {
            "chunk_id": "chunk_002",
            "content": "Giấy khám sức khỏe tiền hôn nhân 01 bản chính cơ sở y tế thẩm quyền"
        },
        {
            "chunk_id": "chunk_003",
            "content": "Thời gian giải quyết trong ngày làm việc tối đa 3 ngày"
        }
    ]

    # Run validation
    result = validator.validate_answer(question, answer, context, chunks)

    # Display report
    print(validator.format_validation_report(result))

    # Export
    validator.export_validation_result(result, "validation_test_result.json")

    print("\n" + "*" * 80)
    print("TEST COMPLETE")
    print("*" * 80)


if __name__ == "__main__":
    test_validation_pipeline()
