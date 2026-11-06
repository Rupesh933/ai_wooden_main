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


class ToolDeclarationsSchemaTests(TestCase):
    def test_tool_declarations_required_properties_exist(self):
        from .agents import SUPPORT_TOOLS, MANAGER_TOOLS, RISK_TOOLS

        for tools in [SUPPORT_TOOLS, MANAGER_TOOLS, RISK_TOOLS]:
            for tool_group in tools:
                for func in tool_group.get("function_declarations", []):
                    params = func.get("parameters", {})
                    props = set(params.get("properties", {}).keys())
                    required = params.get("required", [])
                    for req in required:
                        self.assertIn(
                            req,
                            props,
                            f"Tool '{func['name']}' has required param '{req}' which is missing in properties: {props}",
                        )


class LangChainAgentOutputTests(TestCase):
    def test_extract_text_content_from_gemini_block_format(self):
        from .langchain_agents import _extract_text_content

        gemini_blocks = [
            {
                "type": "text",
                "text": "Your Timbernest folding bed order is dispatched 📦",
                "extras": {"signature": "abc123xyz"},
            }
        ]
        result = _extract_text_content(gemini_blocks)
        self.assertEqual(result, "Your Timbernest folding bed order is dispatched 📦")

    def test_extract_text_content_from_plain_string(self):
        from .langchain_agents import _extract_text_content

        self.assertEqual(_extract_text_content("Hello!"), "Hello!")

    @patch("supports.langchain_agents.support_agent.invoke")
    def test_run_support_agent_langchain_returns_clean_string(self, mock_invoke):
        from langchain_core.messages import AIMessage
        from .langchain_agents import run_support_agent_langchain

        mock_invoke.return_value = {
            "messages": [
                AIMessage(
                    content=[
                        {
                            "type": "text",
                            "text": "Your folding bed is on its way!",
                            "extras": {"signature": "sig123"},
                        }
                    ]
                )
            ]
        }

        # Test with (user_message, conversation_id, order_id, user_id)
        reply = run_support_agent_langchain("hey", 1, 10, 1)
        self.assertEqual(reply, "Your folding bed is on its way!")
        self.assertIsInstance(reply, str)

        # Test with inverted (conversation_id, user_message, order_id, user_id)
        reply_inverted = run_support_agent_langchain(1, "hey", 10, 1)
        self.assertEqual(reply_inverted, "Your folding bed is on its way!")