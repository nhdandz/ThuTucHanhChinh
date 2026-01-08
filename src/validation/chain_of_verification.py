#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chain-of-Verification (CoVe) - Layer 5 Validation
Multi-step verification process to reduce hallucinations

Steps:
1. Generate baseline answer
2. LLM plans verification questions
3. Answer verification questions independently
4. Generate final verified answer using verifications
"""

import sys
import json
import re
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class VerificationQuestion:
    """A verification question for fact-checking"""
    question: str
    answer: str
    verified_fact: str
    confidence: float


@dataclass
class CoVeResult:
    """Result of Chain-of-Verification"""
    original_question: str
    baseline_answer: str
    verification_questions: List[VerificationQuestion]
    final_answer: str
    confidence_improvement: float
    is_verified: bool


class ChainOfVerification:
    """
    Chain-of-Verification (CoVe) Pipeline

    Process:
    1. Generate baseline answer
    2. LLM generates verification questions about the answer
    3. Answer each verification question independently
    4. Use verifications to generate final corrected answer
    """

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_url: str = "http://localhost:11434",
        num_verifications: int = 5
    ):
        """
        Initialize CoVe pipeline

        Args:
            model_name: Ollama model name
            ollama_url: Ollama server URL
            num_verifications: Number of verification questions to generate
        """
        print(f"🔄 Initializing Chain-of-Verification (CoVe)")
        print(f"   Model: {model_name}")
        print(f"   Verification questions: {num_verifications}")

        self.model_name = model_name
        self.ollama_url = ollama_url
        self.generate_endpoint = f"{ollama_url}/api/generate"
        self.num_verifications = num_verifications

        print(f"✅ CoVe initialized!")

    def _call_ollama(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Call Ollama API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        if system:
            payload["system"] = system

        try:
            print("********************************************", prompt)
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=120
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            return response.json()["response"].strip()
        except Exception as e:
            print(f"⚠️ Ollama API call failed: {e}")
            return ""

    def _generate_baseline_answer(
        self,
        question: str,
        context: str
    ) -> str:
        """
        Generate initial baseline answer

        Args:
            question: User question
            context: Retrieved context

        Returns:
            Baseline answer
        """
        system_prompt = """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.
CHỈ trả lời dựa trên CONTEXT được cung cấp.
"""

        prompt = f"""Câu hỏi: {question}

Context:
{context[:2000]}

Trả lời ngắn gọn, chính xác:"""

        answer = self._call_ollama(prompt, system=system_prompt, temperature=0.1)
        return answer

    def _generate_verification_questions(
        self,
        question: str,
        answer: str
    ) -> List[str]:
        """
        Generate verification questions to fact-check the answer

        Args:
            question: Original question
            answer: Baseline answer to verify

        Returns:
            List of verification questions
        """
        system_prompt = """Bạn là chuyên gia fact-checking.

NHIỆM VỤ: Tạo các câu hỏi kiểm chứng để xác minh tính chính xác của câu trả lời.

YÊU CẦU:
- Mỗi câu hỏi kiểm tra một fact cụ thể
- Câu hỏi phải có thể trả lời YES/NO hoặc với số cụ thể
- Tập trung vào các con số, danh sách, thời gian
"""

        prompt = f"""Câu hỏi gốc: "{question}"

Câu trả lời cần kiểm chứng:
{answer}

Hãy tạo {self.num_verifications} câu hỏi kiểm chứng để xác minh các fact trong câu trả lời.

VÍ DỤ:
Nếu câu trả lời nói "cần 3 giấy tờ", tạo câu hỏi: "Có chính xác 3 loại giấy tờ không?"
Nếu nói "trong 7 ngày", tạo câu hỏi: "Thời hạn có đúng là 7 ngày không?"

Trả về JSON array:
["Câu hỏi kiểm chứng 1?", "Câu hỏi kiểm chứng 2?", ...]

Chỉ trả về JSON array, không giải thích:"""

        response = self._call_ollama(prompt, system=system_prompt, temperature=0.3)

        if not response:
            return []

        try:
            # Extract JSON
            start = response.find("[")
            end = response.rfind("]") + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                questions = json.loads(json_str)
                return questions[:self.num_verifications]
        except:
            pass

        return []

    def _answer_verification_question(
        self,
        verification_q: str,
        context: str
    ) -> Tuple[str, float]:
        """
        Answer a verification question using context

        Args:
            verification_q: Verification question
            context: Source context

        Returns:
            Tuple of (answer, confidence)
        """
        system_prompt = """Bạn là hệ thống fact-checking.
CHỈ trả lời dựa trên CONTEXT.
Trả lời ngắn gọn, chính xác.
"""

        prompt = f"""Context:
{context[:1500]}

Câu hỏi kiểm chứng: {verification_q}

Trả lời dựa HOÀN TOÀN vào context:
Answer:
Confidence: [0.0-1.0]

Chỉ trả về format trên:"""

        response = self._call_ollama(prompt, system=system_prompt, temperature=0.1)

        if not response:
            return "Không có thông tin", 0.0

        # Parse response
        lines = response.split('\n')
        answer = "Không có thông tin"
        confidence = 0.5

        for line in lines:
            if line.startswith('Answer:'):
                answer = line.split('Answer:', 1)[1].strip()
            elif line.startswith('Confidence:'):
                try:
                    conf_str = re.search(r'(\d+\.?\d*)', line)
                    if conf_str:
                        confidence = float(conf_str.group(1))
                        if confidence > 1.0:
                            confidence /= 100.0
                except:
                    pass

        return answer, confidence

    def _generate_verified_answer(
        self,
        question: str,
        baseline_answer: str,
        verifications: List[VerificationQuestion],
        context: str
    ) -> str:
        """
        Generate final verified answer using verification results

        Args:
            question: Original question
            baseline_answer: Initial answer
            verifications: Verification results
            context: Source context

        Returns:
            Final verified answer
        """
        system_prompt = """Bạn là trợ lý AI chuyên về thủ tục hành chính Việt Nam.

NHIỆM VỤ: Tạo câu trả lời CHÍNH XÁC dựa trên:
1. Context gốc
2. Kết quả kiểm chứng các fact

CHỈ sử dụng các fact đã được kiểm chứng.
KHÔNG thêm thông tin không có trong context hoặc verifications.
"""

        # Format verifications
        verification_text = "\n".join([
            f"Q: {v.question}\nA: {v.answer} (confidence: {v.confidence:.2f})"
            for v in verifications
        ])

        prompt = f"""Câu hỏi gốc: {question}

Câu trả lời ban đầu:
{baseline_answer}

Kết quả kiểm chứng:
{verification_text}

Context gốc:
{context[:1500]}

Dựa trên kết quả kiểm chứng và context, hãy tạo câu trả lời CHÍNH XÁC nhất.
Chỉ sử dụng thông tin đã được xác minh.

Câu trả lời cuối cùng:"""

        final_answer = self._call_ollama(prompt, system=system_prompt, temperature=0.1)
        return final_answer

    def verify_answer(
        self,
        question: str,
        context: str
    ) -> CoVeResult:
        """
        Run complete Chain-of-Verification pipeline

        Args:
            question: User question
            context: Retrieved context

        Returns:
            CoVeResult object
        """
        print(f"\n🔍 Chain-of-Verification (CoVe) Pipeline...")
        print(f"   Question: {question}")

        # Step 1: Generate baseline answer
        print(f"\n   [1/4] Generating baseline answer...")
        baseline_answer = self._generate_baseline_answer(question, context)
        print(f"         ✓ Baseline generated ({len(baseline_answer)} chars)")

        # Step 2: Generate verification questions
        print(f"\n   [2/4] Planning verification questions...")
        verification_questions = self._generate_verification_questions(question, baseline_answer)
        print(f"         ✓ {len(verification_questions)} questions generated")

        # Step 3: Answer verification questions
        print(f"\n   [3/4] Answering verification questions...")
        verifications = []

        for i, ver_q in enumerate(verification_questions, 1):
            print(f"         [{i}/{len(verification_questions)}] {ver_q[:60]}...")

            answer, confidence = self._answer_verification_question(ver_q, context)

            verification = VerificationQuestion(
                question=ver_q,
                answer=answer,
                verified_fact=f"{ver_q} → {answer}",
                confidence=confidence
            )

            verifications.append(verification)
            print(f"             Answer: {answer[:50]}... (conf: {confidence:.2f})")

        # Step 4: Generate final verified answer
        print(f"\n   [4/4] Generating final verified answer...")
        final_answer = self._generate_verified_answer(
            question, baseline_answer, verifications, context
        )
        print(f"         ✓ Final answer generated ({len(final_answer)} chars)")

        # Calculate confidence improvement
        baseline_length = len(baseline_answer.split())
        final_length = len(final_answer.split())
        avg_verification_conf = (
            sum(v.confidence for v in verifications) / len(verifications)
            if verifications else 0.0
        )

        # Simple heuristic: improvement based on verification confidence
        confidence_improvement = avg_verification_conf

        is_verified = avg_verification_conf >= 0.7

        result = CoVeResult(
            original_question=question,
            baseline_answer=baseline_answer,
            verification_questions=verifications,
            final_answer=final_answer,
            confidence_improvement=confidence_improvement,
            is_verified=is_verified
        )

        print(f"\n   📊 CoVe Summary:")
        print(f"      Verification questions: {len(verifications)}")
        print(f"      Avg verification confidence: {avg_verification_conf:.2f}")
        print(f"      Is verified: {'✅' if is_verified else '❌'}")

        return result

    def format_cove_report(self, result: CoVeResult) -> str:
        """Format CoVe result as report"""
        lines = []

        lines.append("\n" + "=" * 80)
        lines.append("📋 CHAIN-OF-VERIFICATION REPORT")
        lines.append("=" * 80)

        lines.append(f"\n❓ Question: {result.original_question}")
        lines.append(f"\n✅ Verified: {'YES' if result.is_verified else 'NO'}")
        lines.append(f"📈 Confidence: {result.confidence_improvement:.0%}")

        lines.append("\n" + "-" * 80)
        lines.append("BASELINE ANSWER:")
        lines.append("-" * 80)
        lines.append(result.baseline_answer)

        lines.append("\n" + "-" * 80)
        lines.append(f"VERIFICATION QUESTIONS ({len(result.verification_questions)}):")
        lines.append("-" * 80)

        for i, ver in enumerate(result.verification_questions, 1):
            lines.append(f"\n[{i}] {ver.question}")
            lines.append(f"    Answer: {ver.answer}")
            lines.append(f"    Confidence: {ver.confidence:.2f}")

        lines.append("\n" + "-" * 80)
        lines.append("FINAL VERIFIED ANSWER:")
        lines.append("-" * 80)
        lines.append(result.final_answer)

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


def test_chain_of_verification():
    """Test CoVe pipeline"""
    print("=" * 80)
    print("TEST CHAIN-OF-VERIFICATION")
    print("=" * 80)

    cove = ChainOfVerification(
        model_name="qwen3:8b",
        num_verifications=3  # Use 3 for faster testing
    )

    question = "Đăng ký kết hôn cần giấy tờ gì?"
    context = """
Hồ sơ đăng ký kết hôn bao gồm:
1. Giấy tờ tùy thân (CMND/CCCD/Hộ chiếu) của cả hai bên - 02 bản sao
2. Giấy xác nhận tình trạng hôn nhân (đối với người từ 30 tuổi trở lên) - 01 bản chính
3. Giấy khám sức khỏe tiền hôn nhân do cơ sở y tế cấp - 01 bản chính

Thời gian giải quyết: Trong ngày làm việc, trường hợp đặc biệt không quá 03 ngày.
Số lượng hồ sơ: 02 bộ
"""

    result = cove.verify_answer(question, context)
    print(cove.format_cove_report(result))

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_chain_of_verification()
