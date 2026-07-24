import abc
import uuid
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.interview.execution import ProviderExecutionResult


class ExecutionPayload(BaseModel):
    test_case_id: uuid.UUID
    is_sample: bool
    source_code: str
    language_id: int
    stdin: Optional[str] = None
    expected_output: Optional[str] = None
    cpu_time_limit: float
    memory_limit: float


class CodeExecutionProvider(abc.ABC):
    """Abstract interface defining the code execution engine contract."""

    @abc.abstractmethod
    async def execute_batch(
        self,
        payloads: List[ExecutionPayload]
    ) -> ProviderExecutionResult:
        """Executes a batch of compiler/execution runs concurrently."""
        pass
