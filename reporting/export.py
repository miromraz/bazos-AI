import os
import pandas as pd
from jinja2 import Template
from typing import List, Dict, Any
from .visuals import generate_price_scatter

def export_html_report(listings: List[Dict[str, Any]], query: str, output_path: str = "report.html"):
    """Generate an HTML report."""
    
    # Flatten data for DataFrame
    flattened = []
    for l in listings:
        ai_eval = l.get("ai_eval", {})
        flattened.append({
            "id": l.get("id"),
            "title": l.get("title"),
            "price": l.get("price_formatted", l.get("price", "-")),
            "ai_score": ai_eval.get("score", "-"),
            "ai_reason": ai_eval.get("description", ""),
            "meets_criteria": ai_eval.get("meets_criteria", False),
            "url": l.get("url", f"https://www.bazos.cz/search.php?hledat={l.get('id')}")
        })
        
    df = pd.DataFrame(flattened)
    scatter_div = generate_price_scatter(df)
    
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bazos AI Report: {{ query }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr.best-match { background-color: #e6ffe6; }
            .charts { margin: 40px 0; }
        </style>
    </head>
    <body>
        <h1>Bazos Search Report for "{{ query }}"</h1>
        
        <div class="charts">
            {{ scatter_plot }}
        </div>
        
        <h2>Listings</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Price</th>
                <th>AI Score</th>
                <th>Reason</th>
                <th>Meets Criteria?</th>
                <th>Link</th>
            </tr>
            {% for item in items %}
            <tr class="{{ 'best-match' if item.meets_criteria else '' }}">
                <td>{{ item.id }}</td>
                <td>{{ item.title }}</td>
                <td>{{ item.price }}</td>
                <td>{{ item.ai_score }}</td>
                <td>{{ item.ai_reason }}</td>
                <td>{{ item.meets_criteria }}</td>
                <td><a href="{{ item.url }}" target="_blank">View</a></td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    
    template = Template(template_str)
    html = template.render(
        query=query,
        scatter_plot=scatter_div,
        items=flattened
    )
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    return output_path
