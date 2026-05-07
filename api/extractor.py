"""
Layer 2: LLM Extraction using Claude API.

Replaces the local Ollama/Llama 3.2 call with Anthropic's claude-haiku.
Schemas and prompt are unchanged — only the LLM call is swapped.
"""
import sys
import os
import json
from pathlib import Path
from typing import Optional

import anthropic
from pydantic import ValidationError

# Import schemas from the demo package
sys.path.insert(0, str(Path(__file__).parent.parent / "demo"))
from schemas import DWRReport

# Module-level singleton — one HTTP connection pool shared across all requests
_client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


EXTRACTION_PROMPT = """You are a construction contract administration data extraction specialist.
You will receive text from an Ontario MTO Daily Work Record (DWR) that was extracted from a PDF.
The text is NOT in table format — it flows as plain text with field names and values on separate lines.

DOCUMENT STRUCTURE:
The DWR has these sections in order:
1. HEADER: Contract No, Created Date, Contractor, Created by, Record ID, DWR Date, Status, From/To Time
2. WEATHER: Temperature, Wind Speed, Precipitation, Visibility (after "Weather" heading)
3. LABOUR: After weather data. Pattern repeats for each worker classification:
   Classification name (e.g. "Foreman", "Skilled Labourer (Grademan)", "Driver / Teamster", "Operator (Backhoe)")
   Number (count of workers)
   Reconciled Number (may or may not be present)
   Hours Each (decimal hours like 2.00, 4.00)
   Reconciled Hours (may or may not be present)
   Total Man Hours (Number x Hours Each)
   Reconciled Man Hours (may or may not be present)
   Remarks (optional text, sometimes "T&M")
   Status (optional, e.g. "T&M")
   The labour section ends at "Labour(If Operator included..."

4. EQUIPMENT: After the labour section. Pattern repeats for each piece of equipment:
   Equipment Name — MAY span multiple lines, e.g.:
     "94 INTL" + "4900" + "TANDEM" + "CRASH" = one item named "94 INTL 4900 TANDEM CRASH"
   The number prefix (10, 12, 15, 94) is the asset number and is PART of the name.
   Asset Number (usually "0")
   Owned/Rented
   Hours Worked (decimal)
   Hours Stand By (decimal, usually 0.00)
   Down Time (decimal, usually 0.00)
   Operator Include ("No" or "Yes")
   Remarks (optional text about the equipment)
   Reconciled values (may or may not be present)
   Status (optional, e.g. "T&M")

5. MATERIALS: After "Material" heading. Pattern repeats:
   Material category, Description, Units, Quantity, New or Used, Remarks
   Reconciled Quantity (may or may not be present)
   If no materials are listed, return an empty materials array.

6. COMMENTS: After "Comments" heading.
7. CHANGE ORDER: Near bottom, extract the CO number (e.g. "CO-21").

CRITICAL RULES:
- Join multi-line equipment names into one string
- Use exact numbers from the text. Do NOT calculate or estimate.
- If reconciled values are not present, set them to null.
- If a section has column headers but no data rows, return an empty array.
- The "Material Supplied by Contractor" line is NOT a material item — skip it.
- Do NOT invent data. Only extract what is explicitly in the document."""


async def extract_dwr_with_claude(content: str, source_label: str = "") -> DWRReport:
    """
    Extract structured DWR data using Claude API tool use.
    Equivalent to extract_dwr_with_llm() but uses Anthropic instead of Ollama.
    """
    schema = DWRReport.model_json_schema()

    max_retries = 3
    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            response = await _client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                system=EXTRACTION_PROMPT,
                tools=[{
                    "name": "extract_dwr_data",
                    "description": "Extract all structured data fields from a construction Daily Work Record (DWR) document.",
                    "input_schema": schema
                }],
                tool_choice={"type": "tool", "name": "extract_dwr_data"},
                messages=[{
                    "role": "user",
                    "content": f"Extract the DWR data from this document:\n\n{content}"
                }]
            )

            # Find the tool_use block in the response
            tool_block = next(
                (block for block in response.content if block.type == "tool_use"),
                None
            )
            if tool_block is None:
                raise ValueError("Claude returned no tool_use block")

            report = DWRReport(**tool_block.input)
            return report

        except ValidationError as e:
            last_error = e
            if attempt < max_retries - 1:
                continue
            raise RuntimeError(f"Pydantic validation failed after {max_retries} attempts: {e}")
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                continue
            raise RuntimeError(f"Extraction failed after {max_retries} attempts: {e}")

    raise RuntimeError(f"Extraction failed: {last_error}")
