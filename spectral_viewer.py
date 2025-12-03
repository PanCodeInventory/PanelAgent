import json
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm

def load_spectral_data(filepath="spectral_data.json"):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading spectral data: {e}")
        return {}

def get_gaussian_curve(peak, sigma, x_range):
    """
    Generates a Gaussian curve for the given peak and sigma over x_range.
    Normalized to max height 100 (arbitrary intensity units).
    """
    y = norm.pdf(x_range, loc=peak, scale=sigma)
    # Normalize peak to 100%
    if y.max() > 0:
        y = y / y.max() * 100
    return y

def plot_panel_spectra(panel_dict, spectral_data_path="spectral_data.json"):
    """
    Generates a Plotly figure showing the emission spectra of all fluorochromes in the panel.
    """
    db = load_spectral_data(spectral_data_path)
    
    # Create X axis (Wavelength nm)
    x_nm = np.linspace(350, 900, 550) # 350nm to 900nm
    
    fig = go.Figure()
    
    found_count = 0
    
    # Iterate through panel markers
    for marker, info in panel_dict.items():
        fluor_name = info.get("fluorochrome", "Unknown")
        
        # Strategy: Try exact name match, then case-insensitive, then try to map via some heuristics if needed
        # For now, direct match + case-insensitive
        data = None
        
        # 1. Direct match
        if fluor_name in db:
            data = db[fluor_name]
        else:
            # 2. Case-insensitive match
            for k, v in db.items():
                if k.lower() == fluor_name.lower():
                    data = v
                    break
        
        if data:
            peak = data.get("peak")
            sigma = data.get("sigma", 20) # Default sigma if missing
            color = data.get("color", "#888888")
            
            y_intensity = get_gaussian_curve(peak, sigma, x_nm)
            
            # Add trace
            fig.add_trace(go.Scatter(
                x=x_nm,
                y=y_intensity,
                mode='lines',
                name=f"{marker} ({fluor_name})",
                line=dict(color=color, width=2),
                fill='tozeroy', # Fill area under curve
                opacity=0.6
            ))
            
            # Add peak annotation
            fig.add_annotation(
                x=peak,
                y=105,
                text=fluor_name,
                showarrow=False,
                font=dict(size=10, color=color)
            )
            
            found_count += 1
        else:
            # Handle missing data?
            # Maybe print a warning or add a dummy trace?
            pass

    fig.update_layout(
        title="Panel Emission Spectra (Simulated)",
        xaxis_title="Wavelength (nm)",
        yaxis_title="Normalized Intensity (%)",
        template="plotly_white",
        height=400,
        showlegend=True,
        hovermode="x unified"
    )
    
    if found_count == 0:
        fig.add_annotation(
            x=600, y=50,
            text="No spectral data found for these fluorochromes.<br>Please update spectral_data.json.",
            showarrow=False,
            font=dict(size=16, color="red")
        )

    return fig
