# income_agent.py

from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
from typing import Dict, Any
import json


class IncomeAgent:
    def __init__(self):
        """Initialize the LLM-powered income analysis agent."""
        self.agent = Agent(
            model=Gemini(id="gemini-2.5-pro"),
            markdown=False
        )

    def analyze_income(self, income_list: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze multiple income entries and derive insights.

        Input format:
        {
            "income": [
                {"Rupees": 1000, "source": "SIP"},
                {"Rupees": 2500, "source": "Payment from Niraj"},
                ...
            ]
        }

        Output:
        {
            "majorIncomeSource": "<source>",
            "totalIncome": <sum>,
            "mostFrequentClient": "<source>"
        }
        """

        try:
            prompt = f"""
            You are an Income Pattern Analysis AI Agent.

            The user will give an object with "income" which is a list of entries.
            Each entry contains:
            - Rupees: numeric amount
            - source: income source (Salary, SIP, Client name, Gig, Freelancing, etc.)

            Your tasks:
            1. Identify which source generated the **highest total Rupees** → majorIncomeSource.
            2. Calculate **total income** combining all entries.
            3. Identify the source that appears the **most frequently** → mostFrequentClient.
            4. Strictly return a clean JSON in this format:

            {{
                "majorIncomeSource": "<source>",
                "totalIncome": <number>,
                "mostFrequentClient": "<source>"
            }}

            Do not add any explanation outside JSON.

            Income Data:
            {json.dumps(income_list)}
            """

            run_response: RunOutput = self.agent.run(prompt)
            content = run_response.content.strip()

            # Handle JSON code-block format
            if content.startswith("```json"):
                content = content[7:-3].strip()

            return json.loads(content)

        except json.JSONDecodeError:
            return {
                "error": "Failed to parse agent response",
                "raw_response": run_response.content
            }
        except Exception as e:
            return {"error": str(e)}
