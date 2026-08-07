"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 11: Confidence Router
  TODO 12: Design 3 HITL decision points
"""
from dataclasses import dataclass
import math


# ============================================================
# TODO 11: Implement ConfidenceRouter
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
    "change_beneficiary",
    "change_recipient",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        # TODO 11: Implement routing logic
        #
        # 1. Check if action_type is in HIGH_RISK_ACTIONS
        #    -> If yes: always escalate (action="escalate", priority="high",
        #       requires_human=True, reason="High-risk action: {action_type}")
        #
        # 2. Check confidence thresholds:
        #    - confidence >= 0.9:
        #      action="auto_send", priority="low",
        #      requires_human=False, reason="High confidence"
        #
        #    - 0.7 <= confidence < 0.9:
        #      action="queue_review", priority="normal",
        #      requires_human=True, reason="Medium confidence — needs review"
        #
        #    - confidence < 0.7:
        #      action="escalate", priority="high",
        #      requires_human=True, reason="Low confidence — escalating"

        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = float("nan")

        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate", confidence=confidence_value,
                reason=f"High-risk action: {action_type}", priority="high",
                requires_human=True,
            )

        # Invalid scores are not evidence for automation, so fail closed.
        if not math.isfinite(confidence_value) or not 0.0 <= confidence_value <= 1.0:
            return RoutingDecision(
                action="escalate", confidence=confidence_value,
                reason="Invalid confidence - escalating", priority="high",
                requires_human=True,
            )
        if confidence_value >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send", confidence=confidence_value,
                reason="High confidence", priority="low", requires_human=False,
            )
        if confidence_value >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review", confidence=confidence_value,
                reason="Medium confidence - needs review", priority="normal",
                requires_human=True,
            )
        return RoutingDecision(
            action="escalate", confidence=confidence_value,
            reason="Low confidence - escalating", priority="high",
            requires_human=True,
        )


# ============================================================
# TODO 12: Design 3 HITL decision points + a review lifecycle
#
# For each decision point, define:
# - trigger: What condition activates this HITL check?
# - hitl_model: Which model? (human-in-the-loop, human-on-the-loop,
#   human-as-tiebreaker)
# - context_needed: What info does the human reviewer need?
# - example: A concrete scenario
# - approval_path: What approve/reject/timeout decision is recorded?
# - audit_fields: Which correlation ID, intent and proposed action/diff are logged?
#
# Think about real banking scenarios where human judgment is critical.
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "Transfer authorization",
        "trigger": "Any transfer_money request, regardless of model confidence or amount.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Proposed action, source and destination account (masked), amount, currency, recipient, recent transfer history, anomaly flags, and customer confirmation evidence.",
        "example": "The agent proposes a 50,000,000 VND transfer to a new recipient.",
        "approval_path": "Approve creates a recorded approval token and permits the gateway call; reject cancels the request; timeout leaves it on hold and never sends money.",
        "audit_fields": "request_id, correlation_id, intent=transfer_money, proposed amount/recipient diff, anomaly flags, reviewer_id, reviewer decision, decision timestamp, and HITL audit layer.",
    },
    {
        "id": 2,
        "name": "Beneficiary change",
        "trigger": "Any change_beneficiary or change_recipient request, especially when the recipient is new or device/location signals differ.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Old and new beneficiary details (masked where appropriate), linked account, proposed transfer amount, beneficiary age, authentication method, device/location changes, and fraud-risk signals.",
        "example": "The customer asks to replace the saved beneficiary before a high-value transfer.",
        "approval_path": "Approve records the reviewed old-to-new beneficiary diff; reject preserves the old beneficiary; timeout holds the change and blocks any dependent transfer.",
        "audit_fields": "request_id, correlation_id, intent=change_beneficiary, old/new beneficiary diff, amount, risk signals, reviewer_id, reviewer decision, timeout state, and HITL audit layer.",
    },
    {
        "id": 3,
        "name": "Account closure",
        "trigger": "Any close_account request after the agent has collected the closure intent.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Account status, identity verification result, remaining balance, linked products, pending transactions, closure reason, and the proposed closure effective date.",
        "example": "The agent proposes closing an account that still has a pending card settlement.",
        "approval_path": "Approve sends the closure to the authorized workflow; reject keeps the account active; timeout rejects the automatic workflow and leaves the account unchanged.",
        "audit_fields": "request_id, correlation_id, intent=close_account, proposed account-state diff, verification and pending-item context, reviewer_id, reviewer decision, decision timestamp, and HITL audit layer.",
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
