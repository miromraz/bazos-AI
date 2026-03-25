import pandas as pd
import plotly.express as px
from typing import List, Dict, Any

def generate_price_scatter(df: pd.DataFrame) -> str:
    """Returns a Plotly Div string for a scatter plot of AI Score vs Price."""
    if df.empty or 'price' not in df.columns or 'ai_score' not in df.columns:
        return "<p>Not enough data for scatter plot.</p>"
        
    # Clean price column
    df['clean_price'] = df['price'].astype(str).str.replace(r'[^\d]', '', regex=True)
    df['clean_price'] = pd.to_numeric(df['clean_price'], errors='coerce')
    
    df['clean_score'] = pd.to_numeric(df['ai_score'], errors='coerce')
    
    clean_df = df.dropna(subset=['clean_price', 'clean_score'])
    if clean_df.empty:
        return "<p>Could not parse prices or scores.</p>"
        
    fig = px.scatter(clean_df, x='clean_price', y='clean_score', hover_data=['title', 'id'],
                     title='Price vs AI Score', labels={'clean_price': 'Price (CZK)', 'clean_score': 'AI Score'})
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
