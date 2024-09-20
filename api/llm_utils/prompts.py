from langchain_core.prompts import PromptTemplate


class Prompts:

    Planning = PromptTemplate(
        input_variables=["input", "messages"],
        template="""
You are a helpful AI Planning Agent designed to provide a high-level plan for a Human to complete a task.
You will be provided a set of [TOOLS] that the Human can use to complete the task.
Each step of the plan should involve a tool call from the [TOOLS] provided, a reference to the previous conversation, or a response to the user.
**Enclose tool names in square brackets like [tool_name].**
If the value you need is present in the conversation history, you can reference it using 'conversation history' in a step; there is no need to use a tool to get this information.

The following tools are available:

[TOOLS]
{tools}
[/TOOLS]

Please provide a numbered list of steps to complete the task.
for each step provide the information the step should retrieve. You must specify units if applicable (e.g. kg, m, m^3, etc...).
Do NOT include the input variables in the plan, just a high-level overview of the steps to take.
Include only the numbered steps in your answer, no other text.
Provide as few steps as possible to complete the task.
The final step should be to provide a response to the user's query.

Previous conversation:
{messages}

New user input: {input}

Numbered list of steps:
""",
    )

    ReAct = PromptTemplate(
        input_variables=["input", "scratchpad"],
        optional_variables=["messages"],
        template="""
You are a helpful AI Agent designed to complete tasks to aid the Humans.
You will be provided a set of [TOOLS], a [CONVERSATION_HISTORY], a [PLAN], and a [WORKSPACE].
You must use the tools provided in the workspace to complete the task and answer the User.

You have access to the following tools:

[TOOLS]
{tools}
[/TOOLS]

An example schema for how to use a tool in the [WORKSPACE] is provided in the [TOOL_CALL_SCHEMA] below:

[TOOL_CALL_SCHEMA]
Thought: (Specify the information you want to retrieve, including units if applicable)
Action: (the name of the tool to call, must be one of [{tool_names}])
Action Input: (the arguments to the tool call in JSON format, make sure to use double quotes for strings)
STOP
[/TOOL_CALL_SCHEMA]

Be sure to add STOP after the Action Input to indicate the end of the tool call.

The result of the tool call will be provided to you as an "Observation: <result of the tool call>".

If there is an error, either in the result of the tool call or in the way the schema is used, the error will be provided to you as an "Error: <error message>".
Ensure that you adapt your previous steps based on the error. Never repeat a step with the same parameters if it failed previously.

When you have completed all steps in the plan and are ready to provide the final answer to the user's query, you should output:

[ANSWER_SCHEMA]
Agent: (your answer to the user)
STOP
[/ANSWER_SCHEMA]

Begin!

[CONVERSATION_HISTORY]
{messages}
User: {input}
[/CONVERSATION_HISTORY]

Complete ALL of the following steps of the [PLAN] BEFORE you answer the user's query:

[PLAN]
{plan}
[/PLAN]

[WORKSPACE]
{scratchpad}
""",
    )

    Observer = PromptTemplate(
        input_variables=["thought", "action", "action_input", "tool_output"],
        template="""
You are a helpful AI Agent working in the context of a Thought, Action, Observation chain. 
A Thought and Action have been already created.
A tool has been used to process the action input.
Your task is to analyse the tool output and produce one observation summarizing the output of the tool invocation. 
If the tool output includes an error, suggest how to fix the error.

[OUTPUT_SCHEMA]
Thought: (the reasoning behind the action selection, may include the desired output of the tool)
Action: (the action that was executed to retrieve the desired information)
Action Input: (the input parameters for the selected action)
Action Output: (the raw output of the action call)
Observation: (the observation made based on the raw output, relating to the thought and desired information. If there is an error, suggest how to fix the error)
[/OUTPUT_SCHEMA]

Examples:

[EXAMPLE_1]
Thought: To determine how long before Taylor Swift's birthday, I need to first get the current date.
Action: current_datetime
Action Input: <'none': ''>
Action Output: < 2024-09-11 11:29:55.332748 >
Observation: The current date is 2024-09-11.
[/EXAMPLE_1]

[EXAMPLE_2]
Thought: I need to use the search tool to find the volume of a grain of rice.
Action: search
Action Input: <"query": "volume of a grain of rice">
Action Output:  <Find A Tutor Search For Tutors How It Works For Tutors WYZANT TUTORING Find A Tutor Search For Tutors How It Works For Tutors A grain of rice has a volume of 20-^10 m^3. tutor tutor Tutor The solution is to divide the volume of the bowl by the volume per grain of rice and you get the number of grains if we assume they stack perfectly. Ask a question for freeGet a free answer to a quick problem. See more tutors Math tutors Algebra tutors Algebra 2 tutors Find a Tutor Algebra Tutors Computer tutors Language Tutors Math Tutors
How do you work out the volume of a grain of rice? What is the mass of a grain of rice? The mass of one grain of rice is 25 milligram or .025 grams. long-grain white rice. How do you write on a grain of rice? You need long grain rice. rice. Using the ball point pen, write on the grain of rice. What is the length of a grain of rice? Personally, I would measure the length of a grain of rice in A metric unit of a grain of rice? A grain of rice is several milligram.
Cooked Rice | ehow Cooked Rice Uncooked to Cooked Rice Long-grain rice varieties are usually cooked in ways that make them light and fluffy, and can have a higher volume as a result. To emphasize this, they're usually cooked in less water than other rices. This can increase your volume to as much as four cups of cooked rice for each cup of uncooked rice. So when preparing the rice, 1 cup dry rice to cooked perfection becomes approximately 3 cups, or six 1/2 cup servings.
You may enter whole numbers, decimals or fractions ie: 7, 29.35, 15 3/4
Calculator to convert all rice types; long and round short Jasmine rice, Basmati rice and rice flour, weight amounts versus dry volume in grams g, cups, ounces oz, pounds lb, quarts qt, kilograms kg.
 This conversion calculator lets you instantly convert measurements of various rice types or rice products (long rice, round short rice, Basmati rice and rice flour) weight versus volume from cups, grams g, ounces oz, pounds lb, including tablespoon charts. Rice flour, round short Jasmine rice, long rice and Basmati rice cups into grams to ounces to quarts automatic converting calculator.
However, it’s important to note that brown rice and wild rice have slightly different serving sizes due to their higher fiber content and different cooking characteristics. A serving size of cooked brown rice is also around 1/2 cup or 90 grams. Whether you prefer the traditional method of using measuring cups or the more precise approach of weighing the rice, both techniques will help you control portion sizes and achieve your desired serving size. Weighing rice allows you to achieve precise serving sizes, especially when you need to be mindful of your carbohydrate intake or want to follow a specific recipe closely.>
Observation: A grain of rice has a volume of 20-^10 m^3
[/EXAMPLE_2]


Begin!

Thought: {thought}
Action: {action}
Action Input: {action_input}
Action Output: < {tool_output} >
""",
    )
