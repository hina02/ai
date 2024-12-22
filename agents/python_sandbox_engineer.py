from pydantic_ai import Agent, Tool

from tools.python_sandbox import (
    execute_script_and_output_stdout,
    get_file_paths,
    read_file,
    write_file,
)

tools = [
    Tool(read_file),
    Tool(write_file),
    Tool(execute_script_and_output_stdout),
    Tool(get_file_paths),
]

python_sandbox_engineer = Agent(
    "openai:gpt-4o",
    tools=tools,
    system_prompt="""You are the Python engineer.
    you can get the file paths in the allowed workspace directory.
    If you want to read file, you can read the file with the file path.
    If you want to write file, you can write the file with the file name, extension and text.
    You can also execute the python script file and output the stdout.

    You should answer the instruction using the workspace and functions.
    """,
)


async def run_python_engineer_sample() -> str:
    return await python_sandbox_engineer.run(
        """id, name, price, materials, factory_idをもつproductテーブルと、
        id, name, locationをもつfactoryテーブルがあります。materialはproductテーブルを使います。
        サンプルデータを用意して、polarsでprice順に並び替えて出力するコードを書いてください。
        """
    )
