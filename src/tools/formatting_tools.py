"""
Formatting tools for dynamic report generation.
These tools allow the ReportAgent to convert analysis findings into various formats.
"""

import json
from typing import List, Dict, Any, Optional
from agents import function_tool


@function_tool
async def convert_json_to_markdown_table(
    json_data: str,
    columns: Optional[str] = None
) -> str:
    """
    Convert JSON data to a markdown table format.
    
    Args:
        json_data: JSON string containing list of dictionaries
        columns: Optional comma-separated list of columns to include (e.g., "API Endpoint,File Name")
                If None, includes all columns found in the data
    
    Returns:
        Markdown table as string
    """
    try:
        # Parse JSON data
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        if not isinstance(data, list) or not data:
            return "❌ Error: No valid data to convert to table"
        
        # Determine columns to include
        if columns:
            requested_columns = [col.strip() for col in columns.split(',')]
        else:
            # Extract all unique columns from the data
            all_columns = set()
            for item in data:
                if isinstance(item, dict):
                    all_columns.update(item.keys())
            requested_columns = sorted(list(all_columns))
        
        if not requested_columns:
            return "❌ Error: No columns found in data"
        
        # Generate markdown table
        table = "| " + " | ".join(requested_columns) + " |\n"
        table += "|" + "|".join(["-" * (len(col) + 2) for col in requested_columns]) + "|\n"
        
        for item in data:
            if isinstance(item, dict):
                row_values = []
                for col in requested_columns:
                    value = str(item.get(col, 'N/A'))
                    # Escape markdown characters
                    value = value.replace('|', '\\|')
                    row_values.append(value)
                table += "| " + " | ".join(row_values) + " |\n"
        
        return f"""# 📊 Generated Table

{table}

**Total rows**: {len(data)}
**Columns**: {', '.join(requested_columns)}
"""
        
    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON data - {str(e)}"
    except Exception as e:
        return f"❌ Error converting to table: {str(e)}"


@function_tool
async def format_findings_as_list(
    json_data: str,
    grouping_field: Optional[str] = None,
    display_fields: Optional[str] = None
) -> str:
    """
    Format JSON findings as a structured list.
    
    Args:
        json_data: JSON string containing analysis findings
        grouping_field: Optional field name to group items by (e.g., "File Name")
        display_fields: Optional comma-separated fields to display (e.g., "API Endpoint,Method Name")
    
    Returns:
        Formatted markdown list
    """
    try:
        # Parse JSON data
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        if not isinstance(data, list) or not data:
            return "❌ Error: No valid data to format as list"
        
        # Determine display fields
        if display_fields:
            fields_to_show = [field.strip() for field in display_fields.split(',')]
        else:
            # Show all fields from first item
            fields_to_show = list(data[0].keys()) if data else []
        
        result = "# 📋 Analysis Results\n\n"
        
        if grouping_field and grouping_field in data[0]:
            # Group by specified field
            groups = {}
            for item in data:
                group_key = item.get(grouping_field, 'Unknown')
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(item)
            
            for group_name, items in groups.items():
                result += f"## {grouping_field}: {group_name}\n\n"
                for item in items:
                    result += f"- **{item.get(fields_to_show[0], 'Item')}**\n"
                    for field in fields_to_show[1:]:
                        value = item.get(field, 'N/A')
                        result += f"  - {field}: {value}\n"
                    result += "\n"
        else:
            # Simple list format
            for i, item in enumerate(data, 1):
                result += f"### {i}. {item.get(fields_to_show[0], 'Item')}\n"
                for field in fields_to_show[1:]:
                    value = item.get(field, 'N/A')
                    result += f"- **{field}**: {value}\n"
                result += "\n"
        
        return result
        
    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON data - {str(e)}"
    except Exception as e:
        return f"❌ Error formatting as list: {str(e)}"


@function_tool
async def extract_unique_fields(json_data: str) -> str:
    """
    Extract all unique field names from JSON data.
    
    Args:
        json_data: JSON string containing analysis findings
    
    Returns:
        List of available fields as formatted string
    """
    try:
        # Parse JSON data
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        if not isinstance(data, list) or not data:
            return "❌ Error: No valid data to analyze"
        
        # Extract all unique fields
        all_fields = set()
        for item in data:
            if isinstance(item, dict):
                all_fields.update(item.keys())
        
        fields_list = sorted(list(all_fields))
        
        result = f"# 📋 Available Fields\n\n"
        result += f"**Total unique fields found**: {len(fields_list)}\n\n"
        
        for field in fields_list:
            # Show sample values for each field
            sample_values = []
            for item in data:
                if isinstance(item, dict) and field in item:
                    value = str(item[field])
                    if value not in sample_values and len(sample_values) < 3:
                        sample_values.append(value)
            
            result += f"- **{field}**: {', '.join(sample_values[:2])}"
            if len(sample_values) > 2:
                result += f", ..."
            result += "\n"
        
        return result
        
    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON data - {str(e)}"
    except Exception as e:
        return f"❌ Error extracting fields: {str(e)}"


@function_tool
async def generate_summary_stats(json_data: str) -> str:
    """
    Generate summary statistics from JSON findings data.
    
    Args:
        json_data: JSON string containing analysis findings
    
    Returns:
        Summary statistics as formatted string
    """
    try:
        # Parse JSON data
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        if not isinstance(data, list) or not data:
            return "❌ Error: No valid data to analyze"
        
        result = "# 📊 Summary Statistics\n\n"
        result += f"**Total Items**: {len(data)}\n\n"
        
        # Count unique values for each field
        field_stats = {}
        for item in data:
            if isinstance(item, dict):
                for field, value in item.items():
                    if field not in field_stats:
                        field_stats[field] = set()
                    field_stats[field].add(str(value))
        
        result += "## Field Statistics\n\n"
        for field, unique_values in field_stats.items():
            result += f"- **{field}**: {len(unique_values)} unique values\n"
        
        return result
        
    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON data - {str(e)}"
    except Exception as e:
        return f"❌ Error generating stats: {str(e)}"