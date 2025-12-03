from flask import Flask, request, jsonify
from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
import PyPDF2
from io import BytesIO


class CoverLetterGenerator:
    def __init__(self):
        self.agent = Agent(
            model=Gemini(id="gemini-2.5-pro"),
            tools=[],
            markdown=False
        )

    def generate(self, resume_text: str, jd: str) -> str:
        """
        Generate a cover letter using the LLM based on resume and job description.
        """
        try:
            prompt = f"""
You are an expert cover letter writer. Your task is to create a professional, tailored cover letter based on the provided resume and job description.

Instructions:
- Analyze the resume to extract key skills, experiences, achievements, and qualifications.
- Analyze the job description to identify required skills, responsibilities, and company needs.
- Match the candidate's background to the job requirements.
- Structure the cover letter as follows:
  - Header: Include placeholders for date, employer's name/address, and candidate's name/address.
  - Salutation: Use "Dear Hiring Manager," if no name is provided.
  - Introduction: State the position and how you found it, briefly mention why you're a fit.
  - Body: 2-3 paragraphs highlighting relevant experiences and skills with specific examples from the resume that align with the JD.
  - Conclusion: Reiterate interest, call to action, and thank them.
  - Closing: "Sincerely," followed by placeholder for name.
- Keep it concise (300-400 words), professional, and error-free.
- Use first-person perspective as if the candidate is writing it.
- directly start from Dear Hiring Manager and include the company name from the jd and don't include any personal details anywhere in response
Resume:
{resume_text}

Job Description:
{jd}
"""

            run_response: RunOutput = self.agent.run(prompt)
            content = run_response.content.strip()
            return content

        except Exception as e:
            return f"Error generating cover letter: {str(e)}"
