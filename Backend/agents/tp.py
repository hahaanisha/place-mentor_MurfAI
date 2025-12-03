from pathlib import Path
from rich.pretty import pprint
from agno.agent import Agent, RunOutput
from agno.media import File
from agno.models.google import Gemini
from agno.utils.media import download_file

pdf_path = "C:\\Users\\tejas\\OneDrive\\Desktop\\CODE\\PlaceMentor\\Backend\\uploads\\Tejas_Gadge_Resume.pdf"


agent = Agent(
    model=Gemini(id="gemini-2.5-pro"),
    markdown=True,
    # add_history_to_messages=True,
)

run_response: RunOutput = agent.run(
    '''
    You are a resume parser. 
        Extract the following in clean structured format:
        - Full Name
        - Email
        - Skills
        - Projects
        - Education
        - Work Experience

        Return the output in clean JSON format.
    ''',
    files=[File(filepath=pdf_path)],
)
pprint(run_response.content)


