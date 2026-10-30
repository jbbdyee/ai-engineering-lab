"""R1 · R2 · R3 · R6: the engine with fake attempts and a fake clock (no waiting)."""
from tretry.retry import Outcome, Policy, run_with_retry


def failing(times, retryable=True):
    calls = []

    def attempt(timeout):
        calls.append(timeout)
        if len(calls) <= times:
            return Outcome(False, retryable, f"boom {len(calls)}")
        return Outcome(True, output="done")
    return attempt, calls


def test_success_after_two_failures_waits_with_backoff(clock):
    attempt, calls = failing(2)
    result = run_with_retry(attempt, Policy(tries=4, backoff=0.5), sleep=clock.sleep, clock=clock)
    assert result.ok and result.output == "done" and len(calls) == 3
    assert clock.slept == [0.5, 1.0]                          # R1: 0.5 → 1.0 (doubles)


def test_wait_has_a_cap_and_jitter_only_shortens():
    policy = Policy(tries=10, backoff=1, max_wait=4, jitter=0.5)
    assert [policy.wait(n, rand=lambda: 0.0) for n in range(1, 6)] == [1, 2, 4, 4, 4]   # R1: cap
    assert policy.wait(3, rand=lambda: 1.0) == 2.0                                     # R2: up to 50% shorter


def test_all_fail_then_fallback(clock):
    attempt, _ = failing(9)
    result = run_with_retry(attempt, Policy(tries=3), fallback=lambda t: Outcome(True, output="cached"),
                            sleep=clock.sleep, clock=clock)
    assert result.ok and result.used_fallback and result.output == "cached"   # R3
    assert [a.fallback for a in result.attempts] == [False, False, False, True]


def test_not_retryable_stops_at_once_and_skips_fallback(clock):
    attempt, calls = failing(9, retryable=False)
    result = run_with_retry(attempt, Policy(tries=5), fallback=lambda t: Outcome(True, output="cached"),
                            sleep=clock.sleep, clock=clock)
    assert not result.ok and len(calls) == 1 and result.stopped == "not-retryable" and not result.used_fallback


def test_deadline_stops_before_a_wait_that_cannot_fit(clock):
    def slow(timeout):
        clock.now += 3                                           # every try takes 3 s
        return Outcome(False, True, "timeout")
    result = run_with_retry(slow, Policy(tries=5, backoff=1, deadline=7), sleep=clock.sleep, clock=clock)
    assert result.stopped == "deadline" and len(result.attempts) == 2    # R6: 3 + 1 + 3 = 7 → no third try
    assert result.seconds <= 7


def test_deadline_shortens_the_last_timeout(clock):
    seen = []

    def attempt(timeout):
        seen.append(timeout)
        clock.now += timeout
        return Outcome(False, True, "timeout")
    run_with_retry(attempt, Policy(tries=3, backoff=0.5, deadline=5), per_try_timeout=3, sleep=clock.sleep, clock=clock)
    assert seen == [3, 1.5]                                    # 3 + 0.5 wait → 1.5 s left for try 2


def test_retry_after_is_respected_up_to_the_cap(clock):
    answers = [Outcome(False, True, "HTTP 429", status=429, retry_after=3), Outcome(True, output="ok")]
    result = run_with_retry(lambda t: answers.pop(0), Policy(tries=3, backoff=0.5, max_wait=8), sleep=clock.sleep, clock=clock)
    assert result.ok and clock.slept == [3]                    # R4: the server's 3 s, not our 0.5 s
