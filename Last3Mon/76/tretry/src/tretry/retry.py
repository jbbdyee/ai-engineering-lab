"""The retry engine (R1 · R2 · R6 · R13). Knows nothing about commands or HTTP: it calls attempt() and reads its Outcome.

sleep, clock and rand are arguments so tests never wait and always get the same numbers."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Outcome:
    """What one attempt gave. retryable=False means trying again cannot help (e.g. HTTP 400)."""
    ok: bool
    retryable: bool = True
    error: str = ""
    output: str = ""
    status: int | None = None
    retry_after: float | None = None  # seconds the server asked us to wait (HTTP 429 / 503 Retry-After)


@dataclass
class Policy:
    tries: int = 3
    backoff: float = 0.5      # wait before try 2; doubles each time
    max_wait: float = 8.0     # one wait is never longer than this
    jitter: float = 0.0       # 0.2 = each wait is randomly 0..20% shorter, so many clients do not retry at the same moment
    deadline: float | None = None  # seconds for all tries together; no new try that could not finish in time

    def wait(self, attempt: int, rand: Callable[[], float] = random.random) -> float:
        """Wait after attempt number `attempt` (1-based) and before the next one."""
        base = min(self.backoff * 2 ** (attempt - 1), self.max_wait)
        return round(base * (1 - self.jitter * rand()), 3)


@dataclass
class Attempt:
    attempt: int
    started: float   # seconds since the first try started
    seconds: float
    ok: bool
    error: str = ""
    status: int | None = None
    waited: float = 0.0   # wait before this attempt
    fallback: bool = False


@dataclass
class Result:
    ok: bool
    output: str = ""
    attempts: list[Attempt] = field(default_factory=list)
    stopped: str = ""      # why it stopped: success · tries · not-retryable · deadline · breaker
    used_fallback: bool = False
    seconds: float = 0.0


def run_with_retry(attempt: Callable[[float | None], Outcome], policy: Policy, *,
                   fallback: Callable[[float | None], Outcome] | None = None,
                   per_try_timeout: float | None = None,
                   sleep: Callable[[float], None] = time.sleep,
                   clock: Callable[[], float] = time.monotonic,
                   rand: Callable[[], float] = random.random,
                   skip_tries: bool = False) -> Result:
    """Call attempt(timeout) until it works, up to policy.tries. Then fallback once, if given.

    skip_tries=True goes straight to the fallback (the circuit breaker is open)."""
    start = clock()
    result = Result(ok=False)
    waited = 0.0
    number = 0
    while not skip_tries and number < policy.tries:
        number += 1
        timeout = per_try_timeout
        if policy.deadline is not None:
            left = policy.deadline - (clock() - start)
            if left <= 0:
                result.stopped = "deadline"
                break
            timeout = min(timeout, left) if timeout else left
        began = clock()
        outcome = attempt(timeout)
        result.attempts.append(Attempt(number, round(began - start, 3), round(clock() - began, 3), outcome.ok,
                                       outcome.error, outcome.status, waited))
        if outcome.ok:
            result.ok, result.output, result.stopped = True, outcome.output, "success"
            break
        if not outcome.retryable:
            result.output, result.stopped = outcome.output, "not-retryable"
            break
        if number == policy.tries:
            result.stopped = "tries"
            break
        waited = policy.wait(number, rand)
        if outcome.retry_after is not None:
            waited = min(max(waited, outcome.retry_after), policy.max_wait)
        if policy.deadline is not None and clock() - start + waited >= policy.deadline:
            result.stopped = "deadline"
            break
        sleep(waited)
    if skip_tries:
        result.stopped = "breaker"
    # a request that cannot be right (4xx) gets no fallback: the fallback would hide the caller's mistake
    if not result.ok and fallback is not None and result.stopped != "not-retryable":
        began = clock()
        outcome = fallback(per_try_timeout)
        result.attempts.append(Attempt(len(result.attempts) + 1, round(began - start, 3), round(clock() - began, 3),
                                       outcome.ok, outcome.error, outcome.status, 0.0, fallback=True))
        result.used_fallback = True
        if outcome.ok:
            result.ok, result.output = True, outcome.output
    result.seconds = round(clock() - start, 3)
    return result
