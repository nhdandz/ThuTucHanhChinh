#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NLI-based Hallucination Detector - Layer 1 Validation
Uses Natural Language Inference to detect contradictions between context and answer
"""

import sys
import re
import requests
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class NLILabel(Enum):
    """NLI prediction labels"""
    ENTAILMENT = "entailment"
    NEUTRAL = "neutral"
    CONTRADICTION = "contradiction"


@dataclass
class SentenceValidation:
    """Validation result for a single sentence"""
    sentence: str
    label: NLILabel
    entailment_score: float
    neutral_score: float
    contradiction_score: float
    is_hallucination: bool
    confidence: float


@dataclass
class ValidationResult:
    """Complete validation result for an answer"""
    original_answer: str
    sentences: List[str]
    validations: List[SentenceValidation]
    hallucination_count: int
    total_sentences: int
    hallucination_rate: float
    overall_confidence: float
    is_valid: bool


class OllamaNLIValidator:
    """
    NLI-based hallucination detector using Ollama LLM

    Alternative to transformer models (xlm-roberta-large-xnli)
    Uses LLM prompting for NLI classification
    """

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434",
        contradiction_threshold: float = 0.5
    ):
        """
        Initialize NLI validator

        Args:
            model_name: Ollama model name
            ollama_url: Ollama server URL
            contradiction_threshold: Threshold for flagging contradictions
        """
        print(f"🔄 Initializing NLI Validator (Ollama-based)")
        print(f"   Model: {model_name}")
        print(f"   Contradiction threshold: {contradiction_threshold}")

        self.model_name = model_name
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"
        self.contradiction_threshold = contradiction_threshold

        print(f"✅ NLI Validator initialized!")

    def _call_ollama(self, prompt: str, system: Optional[str] = None) -> str:
        """Call Ollama API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1  # Low temperature for consistent classification
            }
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            return response.json()["response"].strip()
        except Exception as e:
            print(f"⚠️ Ollama API call failed: {e}")
            return ""

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Remove thinking tags if present
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        # Simple sentence splitting for Vietnamese
        # Split on period, exclamation, question mark followed by space or newline
        sentences = re.split(r'[.!?]\s+', text)

        # Filter out empty sentences and clean up
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        return sentences

    def _classify_nli(
        self,
        premise: str,
        hypothesis: str
    ) -> Tuple[NLILabel, Dict[str, float]]:
        """
        Classify NLI relationship between premise and hypothesis

        Args:
            premise: Context (source of truth)
            hypothesis: Sentence to validate

        Returns:
            Tuple of (label, scores_dict)
        """
        system_prompt = """Bạn là hệ thống phân loại NLI (Natural Language Inference).

NHIỆM VỤ: Xác định mối quan hệ giữa Premise (tiền đề) và Hypothesis (giả thuyết).

CÁC NHÃN:
1. ENTAILMENT: Hypothesis được suy ra từ Premise (thông tin đúng)
2. NEUTRAL: Hypothesis không liên quan hoặc không đủ thông tin
3. CONTRADICTION: Hypothesis mâu thuẫn với Premise (thông tin sai)

QUAN TRỌNG:
- Chỉ trả về nhãn và điểm số
- Không giải thích
"""

        prompt = f"""Premise (Ngữ cảnh từ tài liệu):
{premise[:1000]}

Hypothesis (Câu cần kiểm tra):
{hypothesis}

Phân loại mối quan hệ NLI.

Trả về theo format:
Label: [ENTAILMENT/NEUTRAL/CONTRADICTION]
Entailment: [0.0-1.0]
Neutral: [0.0-1.0]
Contradiction: [0.0-1.0]

Chỉ trả về format trên, không giải thích:"""

        response = self._call_ollama(prompt, system=system_prompt)

        if not response:
            # Default to NEUTRAL on failure
            return NLILabel.NEUTRAL, {
                "entailment": 0.33,
                "neutral": 0.34,
                "contradiction": 0.33
            }

        # Parse response
        try:
            lines = response.strip().split('\n')
            label_line = next((l for l in lines if 'Label:' in l), None)
            ent_line = next((l for l in lines if 'Entailment:' in l), None)
            neu_line = next((l for l in lines if 'Neutral:' in l), None)
            con_line = next((l for l in lines if 'Contradiction:' in l), None)

            # Extract label
            label_str = "NEUTRAL"
            if label_line:
                if "ENTAILMENT" in label_line.upper():
                    label_str = "ENTAILMENT"
                elif "CONTRADICTION" in label_line.upper():
                    label_str = "CONTRADICTION"

            label = NLILabel(label_str.lower())

            # Extract scores (with fallback)
            def extract_score(line):
                if not line:
                    return 0.33
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    score = float(match.group(1))
                    # Normalize if > 1
                    return score if score <= 1.0 else score / 100.0
                return 0.33

            scores = {
                "entailment": extract_score(ent_line),
                "neutral": extract_score(neu_line),
                "contradiction": extract_score(con_line)
            }

            # Normalize scores to sum to 1.0
            total = sum(scores.values())
            if total > 0:
                scores = {k: v/total for k, v in scores.items()}

            return label, scores

        except Exception as e:
            print(f"⚠️ Failed to parse NLI response: {e}")
            return NLILabel.NEUTRAL, {
                "entailment": 0.33,
                "neutral": 0.34,
                "contradiction": 0.33
            }

    def validate_sentence(
        self,
        sentence: str,
        context: str
    ) -> SentenceValidation:
        """
        Validate a single sentence against context

        Args:
            sentence: Sentence to validate
            context: Source context

        Returns:
            SentenceValidation object
        """
        label, scores = self._classify_nli(premise=context, hypothesis=sentence)

        is_hallucination = (
            label == NLILabel.CONTRADICTION or
            scores["contradiction"] > self.contradiction_threshold
        )

        # Confidence is the score of the predicted label
        confidence = scores[label.value]

        return SentenceValidation(
            sentence=sentence,
            label=label,
            entailment_score=scores["entailment"],
            neutral_score=scores["neutral"],
            contradiction_score=scores["contradiction"],
            is_hallucination=is_hallucination,
            confidence=confidence
        )

    def validate_answer(
        self,
        answer: str,
        context: str,
        max_sentences: int = 20
    ) -> ValidationResult:
        """
        Validate complete answer against context

        Args:
            answer: Generated answer to validate
            context: Source context
            max_sentences: Maximum sentences to validate

        Returns:
            ValidationResult object
        """
        print(f"\n🔍 Validating answer against context...")

        # Split answer into sentences
        sentences = self._split_into_sentences(answer)
        sentences = sentences[:max_sentences]  # Limit for performance

        print(f"   Analyzing {len(sentences)} sentences...")

        # Validate each sentence
        validations = []
        hallucination_count = 0

        for i, sentence in enumerate(sentences, 1):
            print(f"   [{i}/{len(sentences)}] Checking: {sentence[:60]}...")

            validation = self.validate_sentence(sentence, context)
            validations.append(validation)

            if validation.is_hallucination:
                hallucination_count += 1
                print(f"      ⚠️ HALLUCINATION DETECTED!")
                print(f"         Label: {validation.label.value}")
                print(f"         Contradiction score: {validation.contradiction_score:.2f}")

        # Calculate metrics
        total_sentences = len(sentences)
        hallucination_rate = hallucination_count / total_sentences if total_sentences > 0 else 0.0

        # Overall confidence (average of non-hallucination sentences)
        valid_confidences = [
            v.confidence for v in validations
            if not v.is_hallucination
        ]
        overall_confidence = (
            sum(valid_confidences) / len(valid_confidences)
            if valid_confidences else 0.0
        )

        # Answer is valid if hallucination rate < threshold (e.g., 10%)
        is_valid = hallucination_rate < 0.1

        result = ValidationResult(
            original_answer=answer,
            sentences=sentences,
            validations=validations,
            hallucination_count=hallucination_count,
            total_sentences=total_sentences,
            hallucination_rate=hallucination_rate,
            overall_confidence=overall_confidence,
            is_valid=is_valid
        )

        print(f"\n   📊 Validation Summary:")
        print(f"      Total sentences: {total_sentences}")
        print(f"      Hallucinations: {hallucination_count}")
        print(f"      Hallucination rate: {hallucination_rate:.1%}")
        print(f"      Overall confidence: {overall_confidence:.2f}")
        print(f"      Is valid: {'✅' if is_valid else '❌'}")

        return result

    def format_validation_report(self, result: ValidationResult) -> str:
        """
        Format validation result as human-readable report

        Args:
            result: ValidationResult object

        Returns:
            Formatted report string
        """
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📋 NLI VALIDATION REPORT")
        lines.append("=" * 80)

        lines.append(f"\n✅ Valid Answer: {'YES' if result.is_valid else 'NO'}")
        lines.append(f"📊 Hallucination Rate: {result.hallucination_rate:.1%}")
        lines.append(f"🎯 Confidence: {result.overall_confidence:.2f}")
        lines.append(f"📝 Sentences Analyzed: {result.total_sentences}")
        lines.append(f"⚠️  Hallucinations Detected: {result.hallucination_count}")

        if result.hallucination_count > 0:
            lines.append("\n" + "-" * 80)
            lines.append("⚠️  HALLUCINATED SENTENCES:")
            lines.append("-" * 80)

            for i, validation in enumerate(result.validations, 1):
                if validation.is_hallucination:
                    lines.append(f"\n[{i}] {validation.sentence}")
                    lines.append(f"    Label: {validation.label.value}")
                    lines.append(f"    Contradiction: {validation.contradiction_score:.2%}")
                    lines.append(f"    Entailment: {validation.entailment_score:.2%}")
                    lines.append(f"    Neutral: {validation.neutral_score:.2%}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


def test_nli_validator():
    """Test NLI validator with sample data"""
    print("=" * 80)
    print("TEST NLI VALIDATOR")
    print("=" * 80)

    validator = OllamaNLIValidator(
        model_name="qwen3:8b",
        contradiction_threshold=0.5
    )

    # Test case 1: Valid answer (from context)
    context1 = """
Hồ sơ đăng ký kết hôn bao gồm:
1. Giấy tờ tùy thân (CMND/CCCD) - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân - 01 bản chính
3. Giấy khám sức khỏe tiền hôn nhân - 01 bản chính

Thời gian giải quyết: Trong ngày làm việc.
"""

    answer1 = """
Để đăng ký kết hôn, bạn cần chuẩn bị CMND hoặc CCCD (02 bản sao).
Bạn cũng cần có giấy xác nhận tình trạng hôn nhân (01 bản chính).
Ngoài ra, cần có giấy khám sức khỏe tiền hôn nhân (01 bản chính).
Thủ tục được giải quyết trong ngày làm việc.
"""

    print("\n" + "🔵" * 40)
    print("TEST CASE 1: Valid Answer (Should Pass)")
    print("🔵" * 40)

    result1 = validator.validate_answer(answer1, context1)
    print(validator.format_validation_report(result1))

    # Test case 2: Answer with hallucinations
    answer2 = """
Để đăng ký kết hôn, bạn cần chuẩn bị CMND hoặc CCCD (02 bản sao).
Bạn cũng cần nộp 500.000 VNĐ lệ phí đăng ký kết hôn.
Thủ tục được giải quyết trong vòng 30 ngày làm việc.
Bạn phải từ 25 tuổi trở lên mới được đăng ký kết hôn.
"""

    print("\n\n" + "🔴" * 40)
    print("TEST CASE 2: Answer with Hallucinations (Should Fail)")
    print("🔴" * 40)

    result2 = validator.validate_answer(answer2, context1)
    print(validator.format_validation_report(result2))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_nli_validator()
