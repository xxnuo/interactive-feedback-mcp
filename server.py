# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import json
import os
import subprocess
import sys
import tempfile
from typing import Dict

from fastmcp import FastMCP
from pydantic import Field

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")


def launch_feedback_ui(
    summary: str, predefinedOptions: list[str] | None = None
) -> dict[str, str]:
    # Create a temporary file for the feedback result
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")

        # Run feedback_ui.py as a separate process
        # NOTE: There appears to be a bug in uv, so we need
        # to pass a bunch of special flags to make this work
        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--prompt",
            summary,
            "--output-file",
            output_file,
            "--predefined-options",
            "|||".join(predefinedOptions) if predefinedOptions else "",
        ]
        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
        )
        if result.returncode != 0:
            raise Exception(f"Failed to launch feedback UI: {result.returncode}")

        # Read the result from the temporary file
        with open(output_file, "r") as f:
            result = json.load(f)
        os.unlink(output_file)
        return result
    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e


@mcp.tool()
def interactive_feedback(
    message: str = Field(description="The specific question for the user"),
    predefined_options: list = Field(
        default=None,
        description="Predefined options for the user to choose from (optional)",
    ),
) -> Dict[str, str]:
    """Request interactive feedback from the user"""
    predefined_options_list = (
        predefined_options if isinstance(predefined_options, list) else None
    )
    return launch_feedback_ui(message, predefined_options_list)


if __name__ == "__main__":
    mcp.run(transport="stdio")
