"""Mobile responsive CSS styles for Streamlit app."""


def get_mobile_css() -> str:
    """Return CSS for mobile responsiveness.

    Returns:
        CSS string to inject into Streamlit app
    """
    return """
    <style>
    /* Mobile responsive styles */
    @media only screen and (max-width: 768px) {
        /* Reduce padding on mobile */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }

        /* Make tables scrollable horizontally */
        .dataframe-container {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }

        /* Stack columns vertically on mobile */
        .row-widget.stHorizontal {
            flex-direction: column !important;
        }

        /* Make buttons full width on mobile */
        .stButton > button {
            width: 100% !important;
        }

        /* Reduce font sizes slightly */
        h1 {
            font-size: 1.75rem !important;
        }

        h2 {
            font-size: 1.5rem !important;
        }

        h3 {
            font-size: 1.25rem !important;
        }

        /* Make form inputs full width */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            width: 100% !important;
        }

        /* Make checkboxes easier to tap */
        .stCheckbox {
            min-height: 44px !important;
        }

        /* Improve expander touch targets */
        .streamlit-expanderHeader {
            min-height: 44px !important;
            padding: 12px !important;
        }

        /* Make tabs scrollable if too many */
        .stTabs {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }

        /* Better spacing for trial cards */
        .trial-card {
            margin-bottom: 1.5rem !important;
            padding: 1rem !important;
        }

        /* Make phone links more prominent */
        a[href^="tel:"] {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            padding: 8px 12px !important;
            background-color: #0066cc !important;
            color: white !important;
            border-radius: 4px !important;
            text-decoration: none !important;
            display: inline-block !important;
            margin: 8px 0 !important;
        }

        /* Improve metric display on mobile */
        .stMetric {
            background-color: #f0f2f6 !important;
            padding: 12px !important;
            border-radius: 4px !important;
            margin-bottom: 8px !important;
        }
    }

    /* Tablet styles */
    @media only screen and (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
    }

    /* General improvements for all screen sizes */

    /* Trial card styling */
    .trial-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .trial-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: box-shadow 0.2s;
    }

    /* Highlighted trial (high match score) */
    .trial-card-highlight {
        border-left: 4px solid #0066cc;
        background-color: #f8f9ff;
    }

    /* Warning/excluded trial */
    .trial-card-warning {
        border-left: 4px solid #ff6b6b;
        background-color: #fff5f5;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }

    .status-recruiting {
        background-color: #d4edda;
        color: #155724;
    }

    .status-closed {
        background-color: #f8d7da;
        color: #721c24;
    }

    .status-active {
        background-color: #fff3cd;
        color: #856404;
    }

    /* Phase badges */
    .phase-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #e0e0e0;
        color: #333;
        margin-left: 8px;
    }

    /* Distance indicator */
    .distance-indicator {
        color: #666;
        font-size: 0.9rem;
        font-weight: 500;
    }

    .distance-near {
        color: #28a745;
    }

    .distance-medium {
        color: #ffc107;
    }

    .distance-far {
        color: #dc3545;
    }

    /* Improve form layout */
    .stForm {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }

    /* Better button styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Improve download button */
    .stDownloadButton > button {
        background-color: #28a745;
        color: white;
        border: none;
    }

    /* Loading spinner */
    .stSpinner > div {
        border-color: #0066cc !important;
    }

    /* Alerts and info boxes */
    .stAlert {
        border-radius: 6px;
        margin-bottom: 1rem;
    }

    /* Comparison table improvements */
    .comparison-table {
        font-size: 0.9rem;
    }

    .comparison-table th {
        background-color: #f0f2f6;
        font-weight: 600;
        position: sticky;
        top: 0;
        z-index: 10;
    }

    /* Sticky header for long pages */
    @media only screen and (min-width: 769px) {
        .sticky-header {
            position: sticky;
            top: 0;
            background-color: white;
            z-index: 100;
            padding: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    }

    /* Print styles */
    @media print {
        .stButton, .stDownloadButton, .stCheckbox {
            display: none !important;
        }

        .trial-card {
            page-break-inside: avoid;
            border: 1px solid #333;
        }
    }

    /* Accessibility improvements */
    a:focus, button:focus, input:focus, select:focus {
        outline: 2px solid #0066cc !important;
        outline-offset: 2px !important;
    }

    /* High contrast for better readability */
    .high-contrast {
        font-weight: 600;
        color: #000;
    }

    /* Loading skeleton */
    .loading-skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s ease-in-out infinite;
    }

    @keyframes loading {
        0% {
            background-position: 200% 0;
        }
        100% {
            background-position: -200% 0;
        }
    }
    </style>
    """