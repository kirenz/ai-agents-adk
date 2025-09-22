"""Three-stage coding workflow example for the Google Agent Development Kit (ADK).

The pipeline chains specialised sub-agents: a writer produces code, a reviewer critiques
it, and a refactorer applies the feedback. ADK launchers will run the agent exposed as
`root_agent` below.
"""

from google.adk.agents import LlmAgent
from google.adk.agents import SequentialAgent

GEMINI_MODEL = "gemini-2.5-flash"

# --- 1. Code writing stage ---------------------------------------------------
# Generates initial Python code based solely on the user's request.
code_writer_agent = LlmAgent(
    name="CodeWriterAgent",
    model=GEMINI_MODEL,
    instruction=(
        "You are a Python code generator. Only use the user's prompt to create "
        "working Python code. Return the complete program wrapped in ```python "
        "code fences and provide no additional commentary."
    ),
    description="Writes initial Python code based on a specification.",
    output_key="generated_code",  # Persist output in state['generated_code'].
)

# --- 2. Code review stage ----------------------------------------------------
# Reads the previously generated code and produces improvement suggestions.
code_reviewer_agent = LlmAgent(
    name="CodeReviewerAgent",
    model=GEMINI_MODEL,
    instruction="""You are an expert Python code reviewer. Analyse the code below:

```python
{generated_code}
```

Assess correctness, readability, efficiency, edge cases, and adherence to Python
best practices. Respond with a concise bulleted list of findings. If the code looks
excellent, reply with: No major issues found.
""",
    description="Reviews code and provides feedback.",
    output_key="review_comments",  # Persist output in state['review_comments'].
)

# --- 3. Code refactoring stage ----------------------------------------------
# Applies the review feedback to improve the original code.
code_refactorer_agent = LlmAgent(
    name="CodeRefactorerAgent",
    model=GEMINI_MODEL,
    instruction="""You are a Python refactoring assistant. Improve the code below using the
provided review comments.

Original code:
```python
{generated_code}
```

Review comments:
{review_comments}

Implement every relevant suggestion. If reviewers found no major issues, return the
original code unchanged. Output only the final Python code enclosed in ```python ... ``` fences.
""",
    description="Refactors code based on review comments.",
    output_key="refactored_code",  # Persist output in state['refactored_code'].
)

# --- 4. Orchestration --------------------------------------------------------
# SequentialAgent runs each sub-agent in order and shares their state automatically.
code_pipeline_agent = SequentialAgent(
    name="CodePipelineAgent",
    sub_agents=[code_writer_agent, code_reviewer_agent, code_refactorer_agent],
    description="Executes code writing, reviewing, and refactoring in sequence.",
)

# ADK integrations expect the top-level agent to be called `root_agent`.
root_agent = code_pipeline_agent
