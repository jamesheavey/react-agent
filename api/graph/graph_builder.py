import os, json
from typing import Annotated, Union
from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph
from schema.agent_outputs import Action, Finish, Observation, Error, ToolOutput
from schema.message import Message
from .reducers import add_clear, add_max_10
from llm_utils.prompts import Prompts
from llm_utils.output_parsers import react_parser, plan_parser, observation_parser
from tools.tools import get_tools
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from .utils import get_checkpointer, render_graph, send_event
from llm_utils.stop_sequences import STOP_SEQUENCES


class State(TypedDict):
    input: str
    output: str
    messages: Annotated[list[Message], add_max_10]
    steps: Annotated[list[Union[Action, ToolOutput, Observation, Finish, Error]], add_clear]
    plan: str


class GraphBuilder:

    def __init__(self, llm: Union[ChatAnthropic, ChatOpenAI], verbose=True, max_iterations=10):
        self.tools = get_tools()
        self.agent_runnable = (
            Prompts.ReAct.partial(tools=self.tools.json, tool_names=self.tools.names)
            | llm.bind(stop=STOP_SEQUENCES).with_config({"tags": ["agent"]})
            | react_parser
        )
        self.planner_runnable = (
            Prompts.Planning.partial(tools=self.tools.json)
            | llm.bind(stop=STOP_SEQUENCES).with_config({"tags": ["planner"]})
            | plan_parser
        )
        self.observer_runnable = (
            Prompts.Observer.partial() | llm.with_config({"tags": ["observer"]}) | observation_parser
        )
        self.verbose = verbose
        self.planner_node_name = "planner"
        self.agent_node_name = "agent"
        self.tools_node_name = "tools"
        self.observer_node_name = "observer"
        self.loop_count = 0
        self.max_iterations = max_iterations

    def build_graph(self):
        graph = StateGraph(State)

        graph.add_node(self.planner_node_name, self.planner_node)
        graph.add_node(self.agent_node_name, self.agent_node)
        graph.add_node(self.tools_node_name, self.tool_node)
        graph.add_node(self.observer_node_name, self.observer_node)

        graph.add_edge(START, self.planner_node_name)
        graph.add_edge(self.planner_node_name, self.agent_node_name)
        graph.add_conditional_edges(
            source=self.agent_node_name,
            path=self.router,
            path_map=[self.tools_node_name, END, self.agent_node_name],
        )
        graph.add_edge(self.tools_node_name, self.observer_node_name)
        graph.add_edge(self.observer_node_name, self.agent_node_name)

        checkpointer = get_checkpointer()
        react_graph = graph.compile(checkpointer=checkpointer)
        render_graph(react_graph)
        return react_graph

    def planner_node(self, state: dict):
        if self.loop_count > self.max_iterations:
            self.loop_count = 0

        if self.verbose:
            if self.loop_count == 0:
                print("\033[92m\n\n BEGINNING EXECUTION...\033[0m")
                print("\033[92m-------------------------------- \n\033[0m")

            messages = "\n".join([f"{message.role}: {message.content}" for message in state["messages"]]).rstrip("\n")
            if messages:
                print(f"\033[94m{messages}\033[0m")
            print(f"\033[94mUser: {state['input']}\n\033[0m")

        output = self.planner_runnable.invoke({"input": state["input"], "messages": state["messages"]})
        if self.verbose:
            print("\033[96m-------------------------------- \n\033[0m")
            print(f"\033[96mPlan:\n\033[0m {output}\n")
            print("\033[96m-------------------------------- \n\033[0m")

        return {"plan": output, "steps": None, "output": None}

    def router(self, state: dict):
        self.loop_count += 1
        if self.loop_count > self.max_iterations:
            print("\033[91mMAX ITERATIONS EXCEEDED\033[0m")
            send_event("error", "MAX AGENT ITERATIONS EXCEEDED")
            return END

        last_step = state["steps"][-1]
        if isinstance(last_step, Error):
            return self.agent_node_name
        elif isinstance(last_step, Finish):
            return END
        return self.tools_node_name

    def agent_node(self, state: dict):
        output = self.agent_runnable.invoke(self._get_inputs(state))

        if self.verbose:
            if isinstance(output, Action):
                print(f"\033[92mThought:\033[0m {output.thought}")
                print(f"\033[92mAction:\033[0m {output.action}")
                formatted_action_input = str(output.action_input).replace("\\n", "\n")
                print(f"\033[92mAction Input:\033[0m {formatted_action_input}")
            elif isinstance(output, Finish):
                print(f"\033[95mAI: {output.output}\n\033[0m")
            elif isinstance(output, Error):
                print(f"\033[91mError:\033[0m {output.error}\n")
                print(f"\033[91mLog:\033[0m {output.log}\n")

        result = {"steps": [output]}
        if isinstance(output, Finish):
            result["messages"] = [
                Message(role="User", content=state["input"]),
                Message(role="Agent", content=output.output),
            ]
            result["output"] = output.output
            self.loop_count = 0
        return result

    def _get_inputs(self, state):
        scratchpad = ""
        for step in state["steps"]:
            if isinstance(step, Action):
                scratchpad += step.scratchpad
            elif isinstance(step, Observation):
                scratchpad += f"Observation: < {step.observation} >\n\n"
            elif isinstance(step, Error):
                scratchpad += f"Error: {step.error}\n\n"

        messages = ""
        for msg in state["messages"]:
            messages += f"{msg.role}: {msg.content}\n"

        return {
            "input": state["input"],
            "messages": messages,
            "scratchpad": scratchpad,
            "plan": state["plan"],
        }

    def tool_node(self, state: dict):
        try:
            tool_str_to_func = {tool.name: tool for tool in self.tools.functions}
            last_action = state["steps"][-1]

            if last_action.action not in tool_str_to_func:
                error = f"Invalid tool name `{last_action.action}`"
                if self.verbose:
                    print(f"\033[91mError:\033[0m {error}\n")
                send_event("error", error)
                return {"steps": [Error(error=error)]}

            tool_input = last_action.action_input
            output = tool_str_to_func[last_action.action].invoke(tool_input)

            if self.verbose:
                print(f"\033[92mTool Output: \033[93m< {str(output).strip()} >\033[92m\n\033[0m")

            return {"steps": [ToolOutput(tool_output=str(output).strip())]}
        except Exception as e:
            error_message = f"Action `{last_action.action}` failed: < {str(e)} >"
            if self.verbose:
                print(f"\033[91mError:\033[0m {error_message}\n")
            send_event("tool_error", error_message)
            return {"steps": [Error(error=error_message)]}

    def observer_node(self, state: dict):
        try:
            tool_node_output = state["steps"][-1]
            if isinstance(tool_node_output, ToolOutput):
                raw_tool_output = tool_node_output.tool_output
            elif isinstance(tool_node_output, Error):
                raw_tool_output = f"Error: {tool_node_output.error}"
            else:
                raise Exception("Reviewer node called with no Observation!")

            action = state["steps"][-2]
            if not isinstance(action, Action):
                raise Exception("Reviewer node called with no Action information")

            output = self.observer_runnable.invoke(
                {
                    "thought": action.thought,
                    "action": action.action,
                    "action_input": f"< {json.dumps(action.action_input)} >",
                    "tool_output": raw_tool_output,
                }
            )

            if self.verbose:
                print(f"\033[92mObservation: \033[93m< {output.observation} >\033[92m\n\033[0m")

            return {"steps": [output]}
        except Exception as e:
            if self.verbose:
                print(f"\033[91mError in observer_node:\033[0m {e}\n")
            send_event("error", str(e))
            return {"steps": [Error(error=str(e))]}
