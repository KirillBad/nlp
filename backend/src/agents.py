from autogen import ConversableAgent, LLMConfig
from autogen.agentchat.group.patterns import AutoPattern
from tools import classify_query
from config import config

llm_config = LLMConfig(
    config_list=[
        {
            "api_type": "openai",
            "model": "google/gemini-2.5-flash-lite-preview-09-2025",
            "api_key": config.API_KEY.get_secret_value(),
            "base_url": "https://openrouter.ai/api/v1",
            "price": [0, 0],
        }
    ]
)

triage_agent = ConversableAgent(
    name="triage_agent",
    system_message="""You are a triage agent. Your role is to route the user query to the correct agent.
    Use the classify_query tool to categorize queries and route them appropriately.
    Do not provide suggestions or answers, only route the query.""",
    llm_config=llm_config,
    human_input_mode="NEVER",
    functions=[classify_query],
)

report_agent = ConversableAgent(
    name="report_agent",
    system_message="You are a summarization agent. You create concise reports and summaries from provided articles or text. Append 'TERMINATE' to your response when finished.",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

translate_agent = ConversableAgent(
    name="translate_agent",
    system_message="You are a translation agent. You translate text to English (or other requested languages). Append 'TERMINATE' to your response when finished.",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

keyword_agent = ConversableAgent(
    name="keyword_agent",
    system_message="You are a keyword extraction agent. Extract key terms and phrases from the provided text. Append 'TERMINATE' to your response when finished.",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

annotation_agent = ConversableAgent(
    name="annotation_agent",
    system_message="You are an annotation agent. Create a brief annotation of the text. Append 'TERMINATE' to your response when finished.",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

general_agent = ConversableAgent(
    name="general_agent",
    system_message="You handle general, non-natural language processing questions.",
    llm_config=llm_config,
)

pattern = AutoPattern(
    initial_agent=triage_agent,
    agents=[
        triage_agent,
        report_agent,
        translate_agent,
        keyword_agent,
        annotation_agent,
        general_agent,
    ],
    group_manager_args={
        "llm_config": llm_config,
        "is_termination_msg": lambda msg: "TERMINATE" in msg.get("content", ""),
    },
)
