from dataclasses import dataclass


MB = 1024 * 1024


@dataclass(frozen=True)
class PlanLimits:
    max_files: int
    max_file_size: int
    max_total_size: int
    allow_premium_tools: bool = False


PLAN_LIMITS = {
    "GUEST": PlanLimits(
        max_files=5,
        max_file_size=25 * MB,
        max_total_size=100 * MB,
        allow_premium_tools=False,
    ),
    "FREE": PlanLimits(
        max_files=10,
        max_file_size=50 * MB,
        max_total_size=200 * MB,
        allow_premium_tools=False,
    ),
    "PRO": PlanLimits(
        max_files=50,
        max_file_size=200 * MB,
        max_total_size=1024 * MB,
        allow_premium_tools=True,
    ),
    "BUSINESS": PlanLimits(
        max_files=100,
        max_file_size=500 * MB,
        max_total_size=5 * 1024 * MB,
        allow_premium_tools=True,
    ),
}


def get_plan_limits(user=None) -> PlanLimits:
    if user is None or not getattr(user, "is_authenticated", False):
        return PLAN_LIMITS["GUEST"]

    plan = getattr(user, "plan", "FREE") or "FREE"

    return PLAN_LIMITS.get(plan, PLAN_LIMITS["FREE"])