from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from orders.models import Order, Product
from .agents import run_manager_agent
from .models import AgentLog, Conversation


class ManagerRiskAssessmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="risk-test")
        product = Product.objects.create(
            name="Wooden desk",
            price="100.00",
            category="Furniture",
        )
        order = Order.objects.create(
            user=self.user,
            product=product,
            product_name=product.name,
            amount="100.00",
        )
        self.conversation = Conversation.objects.create(user=self.user, order=order)

    @patch("supports.agents.client.models.generate_content")
    def test_escalate_to_risk_decision_runs_agent(self, generate_content):
        generate_content.side_effect = [
            SimpleNamespace(
                function_calls=None,
                text=(
                    "Decision: ESCALATE_TO_RISK\n"
                    "Reason: The account looks suspicious.\n"
                    "Next step: Route the case to risk."
                ),
            ),
            SimpleNamespace(function_calls=None, text="Risk level: HIGH"),
        ]

        run_manager_agent("Refund case", self.user.id, self.conversation.id)

        self.assertTrue(self.conversation.risk_assessed)
        self.assertEqual(
            AgentLog.objects.filter(
                conversation=self.conversation,
                event_type="risk",
            ).count(),
            2,
        )

    @patch("supports.agents.client.models.generate_content")
    def test_tool_based_risk_escalation_is_not_run_twice(self, generate_content):
        tool_call = SimpleNamespace(
            id="risk-call",
            name="access_fraud_risk",
            args={"user_id": self.user.id},
        )
        generate_content.side_effect = [
            SimpleNamespace(
                function_calls=[tool_call],
                candidates=[SimpleNamespace(content="risk tool request")],
            ),
            SimpleNamespace(function_calls=None, text="Risk level: HIGH"),
            SimpleNamespace(function_calls=None, text="Decision: DENY"),
        ]

        run_manager_agent("Refund case", self.user.id, self.conversation.id)

        self.assertTrue(self.conversation.risk_assessed)
        self.assertEqual(
            AgentLog.objects.filter(
                conversation=self.conversation,
                event_type="risk",
            ).count(),
            2,
        )