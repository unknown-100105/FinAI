from pathlib import Path
import re
import time
from typing import Any, Dict

import torch

from .response_verifier import FinancialResponseVerifier
from xai.claims import build_finance_claims
from xai.claim_extractor import FinancialClaimExtractor
from xai.claim_verifier import ClaimVerifier


class SarvamResponseAdapter:

    BASE_MODEL = "sarvamai/sarvam-1"
    DEFAULT_ADAPTER_PATH = "models/finai-v3-final-smoke"

    def __init__(
        self,
        model=None,
        tokenizer=None,
        lazy_load: bool = False,
        adapter_path: str = DEFAULT_ADAPTER_PATH,
    ):
        self.model = model
        self.tokenizer = tokenizer

        self.lazy_load = bool(lazy_load)
        self.adapter_path = str(adapter_path)

        self.loaded = (
            model is not None
            and tokenizer is not None
        )

        self.load_seconds = None

        self.verifier = FinancialResponseVerifier()
        self.claim_verifier = ClaimVerifier()

    def load(self):

        if self.loaded:
            return

        if not self.lazy_load:
            raise RuntimeError(
                "SarvamResponseAdapter is not configured for "
                "automatic model loading."
            )

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is required for the production Sarvam-1 adapter."
            )

        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
        from peft import PeftModel

        start = time.perf_counter()

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.BASE_MODEL,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = (
                self.tokenizer.eos_token
            )

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.BASE_MODEL,
            quantization_config=quant_config,
            device_map="auto",
            dtype=torch.float16,
            trust_remote_code=True,
        )

        adapter_path = Path(self.adapter_path)

        if not adapter_path.exists():
            raise FileNotFoundError(
                f"FinAI adapter path does not exist: "
                f"{adapter_path}"
            )

        self.model = PeftModel.from_pretrained(
            self.model,
            str(adapter_path),
        )

        self.model.eval()

        self.load_seconds = (
            time.perf_counter() - start
        )

        self.loaded = True

    def build_prompt(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str = "English",
        persona: str = "neutral",
    ) -> str:

        # --------------------------------------------------------
        # Training-aligned RAG prompt.
        #
        # V3 training wraps the prompt in <FINAI_QA> markers.
        # Keep the inference prompt structurally close to training.
        # --------------------------------------------------------

        if source == "retrieval_evidence":

            documents = []

            if isinstance(verified_result, dict):
                documents = (
                    verified_result.get("documents")
                    or []
                )

            evidence_blocks = []

            for index, document in enumerate(
                documents,
                start=1,
            ):

                if not isinstance(document, dict):
                    continue

                title = str(
                    document.get("title", "")
                ).strip()

                evidence_text = str(
                    document.get("text", "")
                ).strip()

                if not evidence_text:
                    continue

                # Limit each evidence item so the model does not
                # receive an unnecessarily huge prompt.
                evidence_text = evidence_text[:1200]

                evidence_blocks.append(
                    f"[EVIDENCE {index}] "
                    f"{title}\n"
                    f"{evidence_text}"
                )

            evidence = "\n\n".join(
                evidence_blocks
            )

            return (
                "<FINAI_QA>\n\n"
                "You are FinAI, a financial-domain assistant.\n\n"
                "Use the reference material to answer the user.\n\n"
                "REFERENCE MATERIAL:\n"
                f"{evidence}\n\n"
                "USER:\n"
                f"{user_text}\n\n"
                "</FINAI_QA>"
            )

        # --------------------------------------------------------
        # Training-aligned deterministic finance prompt.
        # Keep the existing verification wording required by tests.
        # --------------------------------------------------------

        return (
            "<FINAI_QA>\n\n"
            "You are FinAI, a financial-domain assistant.\n\n"
            "The system has already determined the user's intent.\n\n"
            "Do not change, recalculate, invent, reinterpret, rename, "
            "or omit any supplied verified financial value.\n\n"
            "INTENT:\n"
            f"{intent}\n\n"
            "VERIFIED RESULT:\n"
            f"{verified_result}\n\n"
            "USER:\n"
            f"{user_text}\n\n"
            "</FINAI_QA>"
        )

    def deterministic_fallback(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
    ) -> str:

        if source == "deterministic_finance_engine":

            if intent == "EMI_QUERY":

                return (
                    f"Based on the supplied loan details, your monthly "
                    f"EMI is ₹{verified_result['monthly_emi']:,.2f}. "
                    f"Total payment is ₹"
                    f"{verified_result['total_payment']:,.2f}, "
                    f"including ₹"
                    f"{verified_result['total_interest']:,.2f} "
                    f"in total interest."
                )

            if intent == "INTEREST_QUERY":

                return (
                    f"Based on the supplied assumptions, the final "
                    f"amount is ₹"
                    f"{verified_result['final_amount']:,.2f}. "
                    f"Total interest is ₹"
                    f"{verified_result['total_interest']:,.2f}."
                )

        return (
            "The requested operation was completed using the "
            "verified system result."
        )

    def _extract_generated_text(
        self,
        generated_text: str,
        prompt: str,
    ) -> str:

        text = generated_text.strip()

        if text.startswith(prompt):
            text = text[len(prompt):].strip()

        text = re.split(
            r"\n\s*(?:USER|ASSISTANT|SYSTEM)\s*:",
            text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        return text

    def _verify_response(
        self,
        response: str,
        intent: str,
        verified_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        if intent == "EMI_QUERY":

            result = self.verifier.verify_emi(
                response=response,
                verified_result=verified_result,
            )

            return {
                "applicable": True,
                **result,
            }

        return {
            "applicable": False,
            "passed": True,
            "missing_values": [],
            "semantic_errors": [],
        }

    def _required_claim_fields(self, intent: str):

        if intent == "EMI_QUERY":
            return [
                "monthly_emi",
                "total_payment",
                "total_interest",
            ]

        return []

    def _verify_claims(
        self,
        response: str,
        intent: str,
        verified_result,
        source: str,
    ):

        required_fields = self._required_claim_fields(intent)

        if not required_fields:

            return {
                "applicable": False,
                "passed": True,
                "report": None,
                "claims": [],
            }

        authoritative = build_finance_claims(
            result=verified_result,
            source=source,
            operation=intent,
        )

        proposed = FinancialClaimExtractor.extract(
            response=response,
            expected_fields=required_fields,
        )

        report = self.claim_verifier.verify(
            authoritative=authoritative,
            proposed=proposed,
            required_fields=required_fields,
        )

        return {
            "applicable": True,
            "passed": report.passed,
            "report": report.to_dict(),
            "claims": proposed.to_dict(),
        }

    def _build_verified_fallback(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
    ) -> Dict[str, Any]:

        fallback = self.deterministic_fallback(
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
        )

        verification = self._verify_response(
            response=fallback,
            intent=intent,
            verified_result=verified_result,
        )

        claim_verification = self._verify_claims(
            response=fallback,
            intent=intent,
            verified_result=verified_result,
            source=source,
        )

        return {
            "response": fallback,
            "verification": verification,
            "claim_verification": claim_verification,
        }

    def generate(
        self,
        user_text: str,
        intent: str,
        verified_result: Dict[str, Any],
        source: str,
        language: str = "English",
        persona: str = "neutral",
        max_new_tokens: int = 160,
    ) -> Dict[str, Any]:

        if (
            self.model is None
            or self.tokenizer is None
        ):

            if self.lazy_load:
                self.load()

        prompt = self.build_prompt(
            user_text=user_text,
            intent=intent,
            verified_result=verified_result,
            source=source,
            language=language,
            persona=persona,
        )

        if (
            self.model is None
            or self.tokenizer is None
        ):

            fallback_result = self._build_verified_fallback(
                user_text=user_text,
                intent=intent,
                verified_result=verified_result,
                source=source,
            )

            return {
                "status": "FALLBACK",
                "source": source,
                "language": language,
                "persona": persona,
                "prompt": prompt,
                "response": fallback_result["response"],
                "verification": fallback_result["verification"],
                "claim_verification": fallback_result[
                    "claim_verification"
                ],
            }

        # --------------------------------------------------------
        # FinAI V3 uses completion-style training, not chat-template
        # formatting. Tokenize the exact training-aligned prompt.
        # --------------------------------------------------------

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.model.device)
            for key, value in inputs.items()
        }

        input_length = (
            inputs["input_ids"].shape[-1]
        )

        with torch.inference_mode():

            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.05,
                use_cache=True,
            )

        generated_tokens = (
            output[0][input_length:]
        )

        generated = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        response = self._extract_generated_text(
            generated,
            prompt,
        )

        verification = self._verify_response(
            response=response,
            intent=intent,
            verified_result=verified_result,
        )

        claim_verification = self._verify_claims(
            response=response,
            intent=intent,
            verified_result=verified_result,
            source=source,
        )

        response_failed = (
            verification["applicable"]
            and not verification["passed"]
        )

        claims_failed = (
            claim_verification["applicable"]
            and not claim_verification["passed"]
        )

        if response_failed or claims_failed:

            fallback_result = self._build_verified_fallback(
                user_text=user_text,
                intent=intent,
                verified_result=verified_result,
                source=source,
            )

            return {
                "status": "FALLBACK_VERIFIED",
                "source": source,
                "language": language,
                "persona": persona,
                "response": fallback_result["response"],
                "verification": verification,
                "claim_verification": claim_verification,
                "fallback_verification": (
                    fallback_result["verification"]
                ),
                "fallback_claim_verification": (
                    fallback_result["claim_verification"]
                ),
                "original_response": response,
            }

        return {
            "status": "GENERATED_VERIFIED",
            "source": source,
            "language": language,
            "persona": persona,
            "response": response,
            "verification": verification,
            "claim_verification": claim_verification,
            "metrics": {
                "load_seconds": self.load_seconds,
            },
        }
