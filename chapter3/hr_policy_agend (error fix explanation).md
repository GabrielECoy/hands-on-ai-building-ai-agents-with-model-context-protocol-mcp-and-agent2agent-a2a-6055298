I'm going to create a short TODO list to track debugging steps for this error (what I'll check and next actions). Expected outcome: a clear plan we can follow while you paste the traceback or let me run the file.

Created 4 todos

Progress update — I created a small todo list to track debugging steps. Next I need the exact Python traceback (or permission to run the script here) so I can pinpoint the error.

Likely causes and quick checks you can do now

Missing module or symbol ImportError:
If you see "ModuleNotFoundError: No module named 'langgraph'" then the package isn't installed in your environment.
If you see "ImportError: cannot import name 'create_react_agent' from 'langgraph.prebuilt'" then the API changed (the function was removed/renamed) or you have an older/newer version.
Stray token in file:
I noticed your selection shows a single line containing "create_react_agent" (line 67). A lone name is a valid Python expression only if the name exists at import time; if the import failed earlier, that bare name will raise NameError when executing the file. If that line is accidental it should be removed.
NameError at runtime:
If import failed earlier, later code referencing create_react_agent(...) would raise NameError.
Version/API mismatch:
The langgraph.prebuilt module may not expose create_react_agent (it might be named differently). Check its docs or inspect the module interactively.
What I recommend (pick one)

Paste the full traceback here (best). I’ll tell you exactly what to change and can edit the file for you.
Or run this in your workspace and paste the output:
Quick manual checks you can run now:
Open hr_policy_agent.py and remove the stray line that only contains create_react_agent (line 67) if it isn't needed.
Verify packages:
In your environment run:
If a package is missing, install it (e.g., pip install langgraph).
If you want, I can:

Remove the stray line safely and run the script to see the new error (if any).
Or just tell you how to fix the import if you paste the traceback.
Which would you like me to do next?

----------------------------

pasting full trace

Exception Group Traceback (most recent call last):
| File "/workspaces/hands-on-ai-building-ai-agents-with-model-context-protocol-mcp-and-agent2agent-a2a-6055298/chapter3/hr_policy_agent.py", line 80, in <module>
| response = asyncio.run(
| run_hr_policy_agent("What is the policy on remote work?"))
| File "/usr/local/lib/python3.13/asyncio/runners.py", line 195, in run
| return runner.run(main)
| ~~~~~~~~~~^^^^^^
| File "/usr/local/lib/python3.13/asyncio/runners.py", line 118, in run
| return self._loop.run_until_complete(task)
| ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
| File "/usr/local/lib/python3.13/asyncio/base_events.py", line 725, in run_until_complete
| return future.result()
| ~~~~~~~~~~~~~^^
| File "/workspaces/hands-on-ai-building-ai-agents-with-model-context-protocol-mcp-and-agent2agent-a2a-6055298/chapter3/hr_policy_agent.py", line 52, in run_hr_policy_agent
| async with stdio_client(server_params) as (read, write):
| ~~~~~~~~~~~~^^^^^^^^^^^^^^^
| File "/usr/local/lib/python3.13/contextlib.py", line 235, in aexit
| await self.gen.athrow(value)
| File "/home/vscode/.local/lib/python3.13/site-packages/mcp/client/stdio/init.py", line 183, in stdio_client
| anyio.create_task_group() as tg,
| ~~~~~~~~~~~~~~~~~~~~~~~^^
| File "/home/vscode/.local/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 781, in aexit
| raise BaseExceptionGroup(
| "unhandled errors in a TaskGroup", self._exceptions
| ) from None
| ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
+-+---------------- 1 ----------------
| Exception Group Traceback (most recent call last):
| File "/home/vscode/.local/lib/python3.13/site-packages/mcp/client/stdio/init.py", line 189, in stdio_client
| yield read_stream, write_stream
| File "/workspaces/hands-on-ai-building-ai-agents-with-model-context-protocol-mcp-and-agent2agent-a2a-6055298/chapter3/hr_policy_agent.py", line 53, in run_hr_policy_agent
| async with ClientSession(read, write) as session:
| ~~~~~~~~~~~~~^^^^^^^^^^^^^
| File "/home/vscode/.local/lib/python3.13/site-packages/mcp/shared/session.py", line 218, in aexit
| return await self._task_group.aexit(exc_type, exc_val, exc_tb)
| ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| File "/home/vscode/.local/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 781, in aexit
| raise BaseExceptionGroup(
| "unhandled errors in a TaskGroup", self._exceptions
| ) from None
| ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
+-+---------------- 1 ----------------
| Traceback (most recent call last):
| File "/workspaces/hands-on-ai-building-ai-agents-with-model-context-protocol-mcp-and-agent2agent-a2a-6055298/chapter3/hr_policy_agent.py", line 67, in run_hr_policy_agent
| agent = create_react_agent(model, hr_policy_tools)
| File "/home/vscode/.local/lib/python3.13/site-packages/langgraph/prebuilt/chat_agent_executor.py", line 663, in create_react_agent
| workflow.add_node(
| ~~~~~~~~~~~~~~~~~^
| "agent",
| ^^^^^^^^
| RunnableCallable(call_model, acall_model),
| ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
| input_schema=input_schema,
| ^^^^^^^^^^^^^^^^^^^^^^^^^^
| )
| ^
| TypeError: StateGraph.add_node() got an unexpected keyword argument 'input_schema'

----------------------------

I'll update the todo list status, then run a short Python snippet to print the installed langgraph version and the signature of StateGraph.add_node, and read requirements.txt to see pinned versions. Expected outcome: identify the version mismatch causing the unexpected keyword argument.

Starting (2/4) Check for stray line


python3 - <<'PY'
import inspect
import importlib
import sys
print('python', sys.version)
try:
    import langgraph
    print('langgraph package:', getattr(langgraph, '__version__', 'no __version__'))
except Exception as e:
    print('failed to import langgraph:', e)

# Try to find StateGraph class and its add_node signature
found = False
for mod_name in ['langgraph', 'langgraph.graph', 'langgraph.state_graph', 'langgraph.core', 'langgraph.workflow', 'langgraph.state']:
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        continue
    for attr in dir(mod):
        if attr.lower().startswith('stategraph') or attr == 'StateGraph':
            cls = getattr(mod, attr)
            try:
                sig = inspect.signature(cls.add_node)
            except Exception as e:
                sig = f'could not get signature: {e}'
            print('found StateGraph in', mod_name)
            print('StateGraph.add_node signature:', sig)
            found = True
            break
    if found:
        break

# fallback: search modules in langgraph package for 'add_node' function
if not found:
    try:
        import pkgutil
        import langgraph
        for finder, name, ispkg in pkgutil.iter_modules(langgraph.__path__):
            full = f'langgraph.{name}'
            try:
                m = importlib.import_module(full)
            except Exception:
                continue
            for attr in dir(m):
                obj = getattr(m, attr)
                if hasattr(obj, '__qualname__') and 'StateGraph' in str(obj):
                    try:
                        sig = inspect.signature(obj.add_node)
                    except Exception:
                        sig = 'unknown'
                    print('possible StateGraph at', full, attr, 'signature', sig)
    except Exception as e:
        print('search fallback failed:', e)
PY

I'll read hr_policy_agent.py to locate where to add a small monkeypatch that maps input_schema to input on StateGraph.add_node, and to remove the stray create_react_agent token. Expected outcome: modify hr_policy_agent.py safely so create_react_agent works with the installed langgraph.
----------------------------

Thanks — I reproduced the error and fixed it locally.

What went wrong (brief)

The traceback showed:
TypeError: StateGraph.add_node() got an unexpected keyword argument 'input_schema'
That means the installed langgraph's StateGraph.add_node(...) expects a different keyword name (it uses input), while create_react_agent (from the prebuilt code) calls add_node(..., input_schema=...).
This is an API mismatch between versions of langgraph (create_react_agent expects an older/newer signature).
What I changed

I added a small, safe monkeypatch to hr_policy_agent.py that maps input_schema -> input on StateGraph.add_node before the agent is created.
File edited: hr_policy_agent.py
Adds a try/except block that wraps StateGraph.add_node and maps kwargs['input_schema'] to kwargs['input'] when present.
The script now runs and returns a valid response from the HR MCP agent.
How I verified

I ran the script in the workspace:
Output shows the patch message ("Patched StateGraph.add_node to accept input_schema -> input"), the MCP server starting, and the agent returned a remote-work policy answer.
So the immediate TypeError is resolved.
Why this approach

It's the least-invasive fix for a local environment mismatch: no changes to site-packages, no reinstall required, and it keeps the prebuilt create_react_agent call working.
It’s a safe compatibility shim and printed a message so you can spot it at runtime.
Suggested long-term fixes (pick one)

Pin a compatible langgraph version in requirements.txt that matches create_react_agent expectations (preferred for reproducible builds). If you want, I can find the exact version and update requirements.txt.
Update the prebuilt call code (in your app or in a custom fork of langgraph) to use the installed API (input), if you maintain that code.
Keep the monkeypatch as a short-term compatibility layer until packages are aligned.
Notes and next steps

If you want me to, I can:
Search for which langgraph release added/removed input_schema and recommend a concrete version to pin.
Update requirements.txt with the pinned version and re-run tests.
Replace the monkeypatch with a more robust shim module (e.g., central compatibility helper) and add a comment/link to a ticket.
If you'd prefer to change package versions instead, tell me to check available versions and I’ll pick the one that has create_react_agent working without the patch.
If you'd like I can now:

Find the matching langgraph release and update requirements.txt (I can run the checks and update the file), or
Remove the monkeypatch and demonstrate how changing the package resolves the issue.
Which would you like next?