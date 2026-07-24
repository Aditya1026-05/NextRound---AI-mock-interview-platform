import asyncio
import base64
import httpx
import logging
from typing import List, Optional
from app.core.config import settings
from app.shared.enums import ExecutionStatus
from app.schemas.interview.execution import ProviderExecutionResult, ProviderTestCaseResult
from app.services.interview.code_execution_provider import CodeExecutionProvider, ExecutionPayload
from app.services.interview.code_execution_provider_factory import CodeExecutionProviderFactory

logger = logging.getLogger(__name__)


class Judge0CodeExecutionProvider(CodeExecutionProvider):
    """Concrete CodeExecutionProvider communicating with Judge0 sandbox engine API."""

    def _encode_b64(self, val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        return base64.b64encode(val.encode("utf-8")).decode("utf-8")

    def _decode_b64(self, val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        try:
            return base64.b64decode(val.encode("utf-8")).decode("utf-8")
        except Exception:
            # Fallback to raw value if decoding fails
            return val

    async def execute_batch(
        self,
        payloads: List[ExecutionPayload]
    ) -> ProviderExecutionResult:
        if not payloads:
            return ProviderExecutionResult(
                status=ExecutionStatus.ACCEPTED,
                passed_tests=0,
                total_tests=0,
                peak_time_ms=0.0,
                peak_memory_kb=0,
                test_cases=[]
            )

        headers = {
            "Content-Type": "application/json"
        }
        if settings.JUDGE0_API_KEY:
            headers["X-Auth-Token"] = settings.JUDGE0_API_KEY
            headers["X-RapidAPI-Key"] = settings.JUDGE0_API_KEY

        # Construct request payloads
        submissions = []
        for payload in payloads:
            submissions.append({
                "source_code": self._encode_b64(payload.source_code),
                "language_id": payload.language_id,
                "stdin": self._encode_b64(payload.stdin),
                "expected_output": self._encode_b64(payload.expected_output),
                "cpu_time_limit": payload.cpu_time_limit,
                "memory_limit": payload.memory_limit * 1024.0  # Limit is in KB on Judge0 (from MB)
            })

        submit_url = f"{settings.JUDGE0_URL.rstrip('/')}/submissions/batch?base64_encoded=true"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(submit_url, json={"submissions": submissions}, headers=headers, timeout=10.0)
                if response.status_code != 201:
                    logger.error(f"Failed to submit batch to Judge0: Status {response.status_code}, Body: {response.text}")
                    return ProviderExecutionResult(
                        status=ExecutionStatus.INTERNAL_ERROR,
                        passed_tests=0,
                        total_tests=len(payloads),
                        peak_time_ms=0.0,
                        peak_memory_kb=0,
                        compile_output=f"Judge0 batch creation failed (HTTP {response.status_code})",
                        test_cases=[]
                    )
                
                creation_results = response.json()
                tokens = [item["token"] for item in creation_results if "token" in item]
                if not tokens:
                    return ProviderExecutionResult(
                        status=ExecutionStatus.INTERNAL_ERROR,
                        passed_tests=0,
                        total_tests=len(payloads),
                        peak_time_ms=0.0,
                        peak_memory_kb=0,
                        compile_output="Judge0 returned empty submission tokens list.",
                        test_cases=[]
                    )
            except Exception as e:
                logger.exception("Network failure during Judge0 batch creation")
                return ProviderExecutionResult(
                    status=ExecutionStatus.INTERNAL_ERROR,
                    passed_tests=0,
                    total_tests=len(payloads),
                    peak_time_ms=0.0,
                    peak_memory_kb=0,
                    compile_output=f"Connection failure to code execution provider: {e}",
                    test_cases=[]
                )

            # Polling loop
            poll_url = f"{settings.JUDGE0_URL.rstrip('/')}/submissions/batch"
            tokens_query = ",".join(tokens)
            
            completed = False
            results = []
            
            for attempt in range(settings.JUDGE0_POLL_RETRIES):
                await asyncio.sleep(settings.JUDGE0_POLL_INTERVAL_MS / 1000.0)
                try:
                    poll_response = await client.get(
                        poll_url,
                        params={
                            "tokens": tokens_query,
                            "base64_encoded": "true",
                            "fields": "token,status_id,status,stdout,stderr,compile_output,time,memory"
                        },
                        headers=headers,
                        timeout=5.0
                    )
                    if poll_response.status_code == 200:
                        results = poll_response.json().get("submissions", [])
                        
                        # Status IDs: <= 2 is queue/processing, >= 3 is completed
                        all_done = all(item.get("status_id", 1) >= 3 for item in results)
                        if all_done:
                            completed = True
                            break
                except Exception as e:
                    logger.warning(f"Polling warning: connection to Judge0 dropped or timed out ({e}). Retrying...")

            if not completed:
                logger.error(f"Polling Judge0 timed out after {settings.JUDGE0_POLL_RETRIES} attempts.")
                return ProviderExecutionResult(
                    status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                    passed_tests=0,
                    total_tests=len(payloads),
                    peak_time_ms=0.0,
                    peak_memory_kb=0,
                    compile_output="Code execution timed out during sandbox processing.",
                    test_cases=[]
                )

            # Map results to standardized ProviderExecutionResult
            test_results = []
            passed_count = 0
            overall_status = ExecutionStatus.ACCEPTED
            peak_time = 0.0
            peak_mem = 0
            compile_output = None

            # Create token to payload mapping for indexing
            for i, result in enumerate(results):
                status_id = result.get("status_id", 13)
                status_desc = result.get("status", {}).get("description", "Unknown")
                
                raw_time_str = result.get("time")
                raw_mem = result.get("memory")
                
                time_ms = float(raw_time_str) * 1000.0 if raw_time_str else 0.0
                mem_kb = int(raw_mem) if raw_mem else 0
                
                peak_time = max(peak_time, time_ms)
                peak_mem = max(peak_mem, mem_kb)
                
                # Fetch compile output if any error
                raw_compile = result.get("compile_output")
                if raw_compile:
                    compile_output = self._decode_b64(raw_compile)

                passed = (status_id == 3)  # Status ID 3 is "Accepted"
                if passed:
                    passed_count += 1

                err_msg = None
                if not passed:
                    if status_id == 4:
                        err_msg = "Wrong Answer"
                    elif status_id == 5:
                        err_msg = "Time Limit Exceeded"
                    elif status_id == 6:
                        err_msg = "Compilation Error"
                    else:
                        err_msg = f"Runtime Error ({status_desc})"

                test_results.append(ProviderTestCaseResult(
                    test_case_id=payloads[i].test_case_id,
                    is_sample=payloads[i].is_sample,
                    passed=passed,
                    stdout=self._decode_b64(result.get("stdout")),
                    stderr=self._decode_b64(result.get("stderr")),
                    execution_time_ms=time_ms,
                    memory_kb=mem_kb,
                    error_message=err_msg,
                    actual_output=self._decode_b64(result.get("stdout"))
                ))

            # Decide overall status by prioritization (CE > RE > TLE > WA > Accepted)
            status_ids = [r.get("status_id", 13) for r in results]
            if 6 in status_ids:
                overall_status = ExecutionStatus.COMPILE_ERROR
            elif any(sid in range(7, 13) for sid in status_ids):
                overall_status = ExecutionStatus.RUNTIME_ERROR
            elif 5 in status_ids:
                overall_status = ExecutionStatus.TIME_LIMIT_EXCEEDED
            elif 4 in status_ids:
                overall_status = ExecutionStatus.WRONG_ANSWER

            return ProviderExecutionResult(
                status=overall_status,
                passed_tests=passed_count,
                total_tests=len(payloads),
                peak_time_ms=peak_time,
                peak_memory_kb=peak_mem,
                compile_output=compile_output,
                test_cases=test_results,
                provider_submission_token=",".join(tokens)
            )


# Auto-register with provider factory
CodeExecutionProviderFactory.register("judge0", Judge0CodeExecutionProvider)
