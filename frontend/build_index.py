#!/usr/bin/env python3
"""Build script for TERRATWIN redesigned frontend (index.html).

Injects the verified Phase 2 & 3 data into a premier geospatial exploration platform
featuring Leaflet with CartoDB Dark Matter / Satellite tiles, dynamic glowing markers,
continuous similarity heatmaps, radar comparison charts, and comprehensive filters.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = Path(__file__).resolve().parent

DATA_FILE = FRONTEND_DIR / "terratwin_data.json"
if not DATA_FILE.exists():
    raise FileNotFoundError(f"Missing {DATA_FILE}")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

json_data_str = json.dumps(raw_data)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TerraTwin — Planetary Analogue Explorer</title>
  
  <!-- Leaflet Map CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  
  <style>
    :root {{
      --bg-space: #070b14;
      --bg-panel: rgba(11, 17, 32, 0.88);
      --bg-panel-border: rgba(0, 240, 255, 0.22);
      --bg-card: rgba(16, 26, 48, 0.75);
      --bg-card-hover: rgba(24, 40, 72, 0.9);
      --accent-cyan: #00f0ff;
      --accent-blue: #0072ff;
      --accent-purple: #9d4edd;
      --accent-orange: #ff8800;
      --accent-gold: #ffcc00;
      --accent-emerald: #00ff88;
      --accent-ruby: #ff3366;
      --accent-grey: #718096;
      --text-main: #f0f4fc;
      --text-muted: #8ba2c7;
      --text-dim: #5a7199;
      --font-mono: 'SF Mono', 'Roboto Mono', 'Courier New', monospace;
      --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-space);
      color: var(--text-main);
      font-family: var(--font-sans);
      overflow: hidden;
      height: 100vh;
      width: 100vw;
      user-select: none;
    }}

    /* Fullscreen Application Container */
    #app-container {{
      position: relative;
      width: 100vw;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* Top HUD Header */
    header.hud-header {{
      position: absolute;
      top: 14px;
      left: 16px;
      right: 16px;
      height: 60px;
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--bg-panel-border);
      border-radius: 10px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65);
    }}

    .brand-group {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .brand-logo {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      box-shadow: 0 0 16px rgba(0, 240, 255, 0.45);
    }}

    .brand-text h1 {{
      font-size: 17px;
      font-weight: 800;
      letter-spacing: 1.5px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .brand-text h1 span.tagline {{
      font-size: 10.5px;
      font-weight: 500;
      letter-spacing: 0.5px;
      color: var(--accent-cyan);
      background: rgba(0, 240, 255, 0.1);
      padding: 2px 7px;
      border-radius: 4px;
      border: 1px solid rgba(0, 240, 255, 0.25);
    }}

    /* Target Selector Dropdown / Segmented Pills */
    .target-nav-group {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .target-selector {{
      display: flex;
      background: rgba(7, 11, 20, 0.75);
      border: 1px solid rgba(0, 240, 255, 0.25);
      border-radius: 8px;
      padding: 3px;
      gap: 3px;
    }}

    .target-btn {{
      padding: 6px 12px;
      font-size: 11.5px;
      font-weight: 600;
      color: var(--text-muted);
      background: transparent;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .target-btn:hover {{
      color: #fff;
    }}

    .target-btn.active {{
      color: #fff;
      background: linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(157, 78, 221, 0.35));
      border: 1px solid var(--accent-cyan);
      box-shadow: 0 0 12px rgba(0, 240, 255, 0.3);
    }}

    /* Mission Preset Pills */
    .preset-selector {{
      display: flex;
      gap: 5px;
    }}

    .preset-btn {{
      padding: 6px 10px;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      background: rgba(16, 26, 48, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .preset-btn:hover {{
      color: #fff;
      border-color: rgba(255, 255, 255, 0.25);
    }}

    .preset-btn.active {{
      color: var(--accent-cyan);
      border-color: var(--accent-cyan);
      background: rgba(0, 240, 255, 0.12);
      box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }}

    .top-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .action-btn {{
      padding: 6px 10px;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      background: rgba(16, 26, 48, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }}

    .action-btn:hover {{
      color: #fff;
      border-color: var(--accent-cyan);
    }}

    /* Main Area Layout: Map (70%) + Comparison Dashboard (30%) */
    #main-content {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      display: flex;
      z-index: 1;
    }}

    /* Interactive Map Container */
    #map-viewport {{
      flex: 1;
      height: 100%;
      position: relative;
      background: #070b14;
    }}

    #map {{
      width: 100%;
      height: 100%;
      background: #070b14;
    }}

    /* Custom Leaflet Styling for Dark Matter */
    .leaflet-container {{
      background: #070b14 !important;
      font-family: var(--font-sans) !important;
    }}

    /* Invert and style standard free OpenStreetMap tiles into a NASA Dark Control Map (100% Free, NO CartoDB, NO API Key) */
    .osm-dark-tiles .leaflet-tile {{
      filter: invert(100%) hue-rotate(180deg) brightness(80%) contrast(95%) saturate(0.25) !important;
    }}

    .leaflet-bar a {{
      background-color: var(--bg-panel) !important;
      color: var(--accent-cyan) !important;
      border-color: var(--bg-panel-border) !important;
    }}
    .leaflet-bar a:hover {{
      background-color: var(--bg-card-hover) !important;
      color: #fff !important;
    }}

    /* Floating Left Sidebar (Filters, Search, Ranked List) */
    aside.sidebar-left {{
      position: absolute;
      top: 86px;
      left: 16px;
      bottom: 56px;
      width: 340px;
      z-index: 1000;
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--bg-panel-border);
      border-radius: 10px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65);
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    aside.sidebar-left.collapsed {{
      transform: translateX(-360px);
    }}

    .sidebar-toggle-btn {{
      position: absolute;
      top: 12px;
      right: -32px;
      width: 32px;
      height: 36px;
      background: var(--bg-panel);
      border: 1px solid var(--bg-panel-border);
      border-left: none;
      border-radius: 0 8px 8px 0;
      color: var(--accent-cyan);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 13px;
      box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4);
    }}

    .panel-header {{
      padding: 14px 16px 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .panel-title {{
      font-size: 12.5px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: var(--accent-cyan);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .search-row {{
      margin-top: 10px;
      position: relative;
    }}

    .search-row input {{
      width: 100%;
      padding: 7px 10px 7px 28px;
      background: rgba(7, 11, 20, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 6px;
      font-size: 11px;
      color: #fff;
      outline: none;
      transition: border-color 0.2s;
    }}

    .search-row input:focus {{
      border-color: var(--accent-cyan);
    }}

    .search-row span.search-icon {{
      position: absolute;
      left: 9px;
      top: 7px;
      font-size: 11px;
      color: var(--text-dim);
    }}

    /* Filter Controls */
    .filter-section {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: 8px;
    }}

    .filter-pills {{
      display: flex;
      gap: 4px;
    }}

    .filter-pill {{
      flex: 1;
      padding: 4px 0;
      font-size: 9.5px;
      font-weight: 600;
      text-transform: uppercase;
      text-align: center;
      background: rgba(16, 26, 48, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 4px;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;
    }}

    .filter-pill.active {{
      background: rgba(0, 240, 255, 0.15);
      border-color: var(--accent-cyan);
      color: #fff;
    }}

    .filter-dropdowns {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }}

    .filter-select {{
      width: 100%;
      padding: 4px 6px;
      background: rgba(7, 11, 20, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      color: var(--text-muted);
      font-size: 10px;
      outline: none;
    }}

    .filter-select:focus {{
      border-color: var(--accent-cyan);
    }}

    .discovery-toggle-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 4px;
      padding: 4px 6px;
      background: rgba(157, 78, 221, 0.1);
      border: 1px solid rgba(157, 78, 221, 0.25);
      border-radius: 4px;
      font-size: 10px;
    }}

    .discovery-toggle-row span {{
      color: var(--accent-purple);
      font-weight: 600;
    }}

    /* Candidate Cards List */
    .cards-list {{
      flex: 1;
      overflow-y: auto;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .cards-list::-webkit-scrollbar {{
      width: 4px;
    }}

    .cards-list::-webkit-scrollbar-thumb {{
      background: rgba(0, 240, 255, 0.25);
      border-radius: 4px;
    }}

    .site-card {{
      background: var(--bg-card);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 8px;
      padding: 10px;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }}

    .site-card:hover {{
      background: var(--bg-card-hover);
      border-color: rgba(0, 240, 255, 0.35);
      transform: translateY(-1px);
    }}

    .site-card.selected {{
      border-color: var(--accent-cyan);
      background: rgba(22, 38, 70, 0.9);
      box-shadow: 0 0 14px rgba(0, 240, 255, 0.3);
    }}

    .card-top-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }}

    .rank-pill {{
      font-size: 10px;
      font-weight: 700;
      font-family: var(--font-mono);
      color: var(--accent-cyan);
      background: rgba(0, 240, 255, 0.1);
      padding: 1px 5px;
      border-radius: 3px;
      border: 1px solid rgba(0, 240, 255, 0.2);
    }}

    .score-indicator {{
      font-size: 12px;
      font-weight: 800;
      font-family: var(--font-mono);
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .score-indicator.high {{ color: var(--accent-emerald); }}
    .score-indicator.medium {{ color: var(--accent-gold); }}
    .score-indicator.low {{ color: var(--accent-ruby); }}
    .score-indicator.missing {{ color: var(--accent-grey); }}

    .site-card h3 {{
      font-size: 12px;
      font-weight: 700;
      color: #fff;
      line-height: 1.3;
      margin-bottom: 2px;
    }}

    .site-card-meta {{
      font-size: 9.5px;
      color: var(--text-muted);
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
    }}

    .site-card-tags {{
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
    }}

    .micro-tag {{
      font-size: 8.5px;
      padding: 2px 4px;
      border-radius: 2px;
      white-space: nowrap;
    }}

    .micro-tag.match {{
      background: rgba(0, 255, 136, 0.1);
      border: 1px solid rgba(0, 255, 136, 0.25);
      color: var(--accent-emerald);
    }}

    .micro-tag.dev {{
      background: rgba(255, 51, 102, 0.1);
      border: 1px solid rgba(255, 51, 102, 0.25);
      color: var(--accent-ruby);
    }}

    .micro-tag.status-val {{
      background: rgba(0, 240, 255, 0.1);
      color: var(--accent-cyan);
    }}

    .micro-tag.status-cand {{
      background: rgba(255, 136, 0, 0.1);
      color: var(--accent-orange);
    }}

    /* Floating Right Sidebar (Scientific Comparison & Analysis Dashboard) */
    aside.sidebar-right {{
      width: 440px;
      height: 100%;
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-left: 1px solid var(--bg-panel-border);
      z-index: 1000;
      display: flex;
      flex-direction: column;
      box-shadow: -8px 0 32px rgba(0, 0, 0, 0.65);
      transition: width 0.3s ease, transform 0.3s ease;
      overflow: hidden;
    }}

    aside.sidebar-right.collapsed {{
      transform: translateX(450px);
      width: 0;
    }}

    .right-toggle-btn {{
      position: absolute;
      top: 86px;
      right: 440px;
      width: 32px;
      height: 36px;
      background: var(--bg-panel);
      border: 1px solid var(--bg-panel-border);
      border-right: none;
      border-radius: 8px 0 0 8px;
      color: var(--accent-cyan);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 13px;
      z-index: 1001;
      box-shadow: -4px 4px 12px rgba(0, 0, 0, 0.4);
      transition: right 0.3s ease;
    }}

    aside.sidebar-right.collapsed ~ .right-toggle-btn {{
      right: 0;
    }}

    /* Right Sidebar Tabs */
    .tab-bar {{
      display: flex;
      background: rgba(7, 11, 20, 0.7);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 6px 8px;
      gap: 4px;
      margin-top: 68px; /* Below header */
    }}

    .tab-btn {{
      flex: 1;
      padding: 8px 4px;
      font-size: 11px;
      font-weight: 600;
      text-align: center;
      background: transparent;
      border: none;
      color: var(--text-muted);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }}

    .tab-btn:hover {{
      color: #fff;
    }}

    .tab-btn.active {{
      background: rgba(0, 240, 255, 0.15);
      color: var(--accent-cyan);
      border: 1px solid rgba(0, 240, 255, 0.3);
    }}

    .tab-content {{
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: none;
    }}

    .tab-content.active {{
      display: block;
    }}

    .tab-content::-webkit-scrollbar {{
      width: 4px;
    }}

    .tab-content::-webkit-scrollbar-thumb {{
      background: rgba(0, 240, 255, 0.25);
      border-radius: 4px;
    }}

    /* Comparison Tab Elements */
    .site-hero-card {{
      background: var(--bg-card);
      border: 1px solid rgba(0, 240, 255, 0.3);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
    }}

    .hero-title {{
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 4px;
    }}

    .hero-meta {{
      font-size: 10.5px;
      color: var(--text-muted);
      line-height: 1.4;
      margin-bottom: 8px;
    }}

    .score-hero-badge {{
      display: inline-flex;
      align-items: baseline;
      gap: 6px;
      background: rgba(7, 11, 20, 0.6);
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .score-hero-val {{
      font-size: 22px;
      font-weight: 800;
      font-family: var(--font-mono);
    }}

    .score-hero-lbl {{
      font-size: 9.5px;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .radar-container {{
      width: 100%;
      height: 220px;
      position: relative;
      margin: 10px 0 14px;
      background: rgba(7, 11, 20, 0.4);
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }}

    canvas#radar-canvas {{
      width: 100%;
      height: 100%;
      display: block;
    }}

    .matrix-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 10.5px;
      margin-top: 6px;
    }}

    .matrix-table th {{
      text-align: left;
      padding: 6px 8px;
      color: var(--text-dim);
      font-size: 9.5px;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .matrix-table td {{
      padding: 6px 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      font-family: var(--font-mono);
    }}

    /* "Where the Analogy Breaks Down" Panel */
    .breakdown-banner {{
      background: linear-gradient(135deg, rgba(255, 136, 0, 0.15), rgba(255, 51, 102, 0.15));
      border: 1px solid rgba(255, 136, 0, 0.4);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 14px;
    }}

    .breakdown-banner h3 {{
      font-size: 11.5px;
      font-weight: 800;
      color: var(--accent-orange);
      letter-spacing: 1px;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
    }}

    .breakdown-banner p {{
      font-size: 10px;
      color: var(--text-muted);
      line-height: 1.4;
    }}

    .breakdown-card {{
      background: var(--bg-card);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 10px;
    }}

    .breakdown-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}

    .breakdown-card-title {{
      font-size: 11.5px;
      font-weight: 700;
      color: #fff;
    }}

    .badge-limit {{
      font-size: 8.5px;
      padding: 2px 5px;
      border-radius: 3px;
      font-weight: 600;
      text-transform: uppercase;
      background: rgba(255, 136, 0, 0.15);
      border: 1px solid rgba(255, 136, 0, 0.3);
      color: var(--accent-orange);
    }}

    .badge-mismatch {{
      font-size: 8.5px;
      padding: 2px 5px;
      border-radius: 3px;
      font-weight: 600;
      text-transform: uppercase;
      background: rgba(255, 51, 102, 0.15);
      border: 1px solid rgba(255, 51, 102, 0.3);
      color: var(--accent-ruby);
    }}

    .breakdown-diff-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      background: rgba(7, 11, 20, 0.5);
      padding: 6px 8px;
      border-radius: 4px;
      font-size: 9.5px;
      margin-top: 4px;
    }}

    .breakdown-diff-grid span.lbl {{
      color: var(--text-dim);
      font-weight: 600;
      display: block;
      margin-bottom: 2px;
    }}

    .breakdown-impact {{
      font-size: 9.5px;
      color: var(--text-muted);
      margin-top: 6px;
      line-height: 1.35;
    }}

    /* Weight Sliders Tab */
    .slider-item {{
      margin-bottom: 12px;
    }}

    .slider-header {{
      display: flex;
      justify-content: space-between;
      font-size: 10.5px;
      margin-bottom: 4px;
    }}

    .slider-header span.name {{
      color: var(--text-main);
      font-weight: 500;
    }}

    .slider-header span.val {{
      font-family: var(--font-mono);
      color: var(--accent-cyan);
    }}

    input[type=range] {{
      width: 100%;
      height: 4px;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 2px;
      outline: none;
      -webkit-appearance: none;
    }}

    input[type=range]::-webkit-slider-thumb {{
      -webkit-appearance: none;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--accent-cyan);
      box-shadow: 0 0 6px var(--accent-cyan);
      cursor: pointer;
    }}

    /* Bottom HUD Scale & Legend Bar */
    footer.hud-footer {{
      position: absolute;
      bottom: 12px;
      left: 16px;
      right: 460px; /* Leave space for right sidebar */
      height: 38px;
      z-index: 1000;
      background: var(--bg-panel);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--bg-panel-border);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      font-size: 10.5px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
      transition: right 0.3s ease;
    }}

    aside.sidebar-right.collapsed ~ footer.hud-footer {{
      right: 16px;
    }}

    .legend-bar-group {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .legend-gradient-bar {{
      width: 140px;
      height: 7px;
      border-radius: 3px;
      background: linear-gradient(to right, #718096 0%, #ff6600 25%, #ffcc00 60%, #00ff88 80%, #00f0ff 100%);
      border: 1px solid rgba(255, 255, 255, 0.2);
    }}

    .layer-controls {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .layer-controls label {{
      display: flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
      color: var(--text-muted);
    }}

    /* Custom Leaflet Pulsing Markers */
    .pulse-marker-container {{
      position: relative;
      cursor: pointer;
    }}

    .pulse-marker-ring {{
      position: absolute;
      top: -12px;
      left: -12px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      animation: pulseAnim 2s infinite ease-out;
      opacity: 0.7;
    }}

    .pulse-marker-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 1.5px solid #fff;
      box-shadow: 0 0 8px currentColor;
    }}

    @keyframes pulseAnim {{
      0% {{
        transform: scale(0.5);
        opacity: 0.8;
      }}
      100% {{
        transform: scale(2.2);
        opacity: 0;
      }}
    }}

    /* Custom Map Tooltip Styling */
    .leaflet-popup-content-wrapper {{
      background: rgba(11, 17, 32, 0.95) !important;
      color: var(--text-main) !important;
      border: 1px solid var(--accent-cyan) !important;
      border-radius: 8px !important;
      box-shadow: 0 6px 20px rgba(0, 240, 255, 0.25) !important;
      padding: 0 !important;
    }}

    .leaflet-popup-tip {{
      background: rgba(11, 17, 32, 0.95) !important;
      border: 1px solid var(--accent-cyan) !important;
    }}

    .custom-popup-content {{
      padding: 10px 12px;
      font-family: var(--font-sans);
    }}

    .popup-title {{
      font-size: 12px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 2px;
    }}

    .popup-subtitle {{
      font-size: 9.5px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}

    .popup-score-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(7, 11, 20, 0.6);
      padding: 4px 6px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 11px;
    }}

    /* Mini Target Context Overlay */
    .mini-target-overlay {{
      position: absolute;
      top: 86px;
      right: 460px;
      width: 190px;
      background: rgba(11, 17, 32, 0.88);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(157, 78, 221, 0.35);
      border-radius: 8px;
      padding: 10px;
      z-index: 999;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
      transition: right 0.3s ease;
    }}

    aside.sidebar-right.collapsed ~ .mini-target-overlay {{
      right: 16px;
    }}

    .mini-target-title {{
      font-size: 10.5px;
      font-weight: 700;
      color: var(--accent-purple);
      text-transform: uppercase;
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
    }}

    .mini-target-desc {{
      font-size: 9.5px;
      color: var(--text-muted);
      line-height: 1.35;
    }}
  </style>
</head>
<body>

  <div id="app-container">
    <!-- Top HUD Navigation Header -->
    <header class="hud-header">
      <div class="brand-group">
        <div class="brand-logo">🪐</div>
        <div class="brand-text">
          <h1>TerraTwin <span class="tagline">NASA Space Apps</span></h1>
        </div>
      </div>

      <!-- Planetary Target Selector -->
      <div class="target-nav-group">
        <span style="font-size: 10px; color: var(--accent-emerald); background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.25); padding: 2px 7px; border-radius: 4px; font-weight: 600;">✓ Free &bull; No API Key</span>
        <span style="font-size: 10.5px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px;">Target:</span>
        <div class="target-selector">
          <button class="target-btn active" data-target="moon_south_pole">🌕 Moon South Pole</button>
          <button class="target-btn" data-target="mars_jezero_crater">🔴 Mars Jezero</button>
          <button class="target-btn" data-target="mars_oxia_planum">🔴 Mars Oxia Planum</button>
        </div>
      </div>

      <!-- Analysis Preset Selector -->
      <div class="preset-selector">
        <button class="preset-btn active" data-preset="balanced_default">⚖️ Balanced</button>
        <button class="preset-btn" data-preset="rover_mobility">🚜 Rover Mobility</button>
        <button class="preset-btn" data-preset="cold_trap_ice">❄️ Cold Trap</button>
        <button class="preset-btn" data-preset="thermal_cycling">🌡️ Thermal</button>
      </div>

      <!-- Actions -->
      <div class="top-actions">
        <button class="action-btn" id="btn-reset-view" title="Reset to global view">🌍 Global View</button>
        <button class="action-btn" id="btn-open-weights" title="Adjust feature weights">⚙️ Weights</button>
      </div>
    </header>

    <!-- Main Viewport (Map + Sidebars) -->
    <div id="main-content">
      <!-- 70% Width Interactive Earth Map -->
      <div id="map-viewport">
        <div id="map"></div>
      </div>

      <!-- Floating Left Sidebar: Discovery & Ranked Locations -->
      <aside class="sidebar-left" id="sidebar-left">
        <div class="sidebar-toggle-btn" id="btn-toggle-left" title="Toggle Sidebar">◀</div>
        <div class="panel-header">
          <div class="panel-title">
            <span>Earth Analogue Catalogue</span>
            <span id="candidate-count-badge" style="font-size: 10.5px; color: var(--accent-cyan); font-family: var(--font-mono);">24 Sites</span>
          </div>

          <!-- Location Search -->
          <div class="search-row">
            <span class="search-icon">🔍</span>
            <input type="text" id="site-search-input" placeholder="Search name, country, region...">
          </div>

          <!-- Filter Section -->
          <div class="filter-section">
            <div class="filter-pills">
              <div class="filter-pill active" data-filter="all">All (24)</div>
              <div class="filter-pill" data-filter="famous">Famous</div>
              <div class="filter-pill" data-filter="overlooked">Overlooked</div>
            </div>

            <div class="filter-dropdowns">
              <select class="filter-select" id="filter-continent">
                <option value="all">All Continents</option>
                <option value="Antarctica">Antarctica</option>
                <option value="North America">North America</option>
                <option value="South America">South America</option>
                <option value="Asia">Asia</option>
                <option value="Europe">Europe</option>
                <option value="Africa">Africa</option>
              </select>

              <select class="filter-select" id="filter-env">
                <option value="all">All Environments</option>
                <option value="polar_desert">Polar Desert</option>
                <option value="hyper_arid_desert">Hyper-Arid</option>
                <option value="volcanic_terrain">Volcanic</option>
                <option value="crater_impact">Impact Crater</option>
                <option value="playa_evaporite">Playa / Salt</option>
                <option value="cold_desert">Cold Desert</option>
              </select>
            </div>

            <!-- Discovery Mode Toggle -->
            <div class="discovery-toggle-row">
              <span>🔭 Scientific Discovery Mode</span>
              <input type="checkbox" id="toggle-discovery" style="cursor: pointer;">
            </div>
          </div>
        </div>

        <!-- Scrollable Candidate Cards List -->
        <div class="cards-list" id="cards-container">
          <!-- Injected via JavaScript -->
        </div>
      </aside>

      <!-- Floating Right Sidebar: Scientific Comparison & Analysis Dashboard -->
      <aside class="sidebar-right" id="sidebar-right">
        <div class="right-toggle-btn" id="btn-toggle-right" title="Toggle Analysis Panel">▶</div>
        <div class="tab-bar">
          <button class="tab-btn active" data-tab="tab-comparison">Comparison</button>
          <button class="tab-btn" data-tab="tab-breakdown">Where Analogy Breaks Down</button>
          <button class="tab-btn" data-tab="tab-weights">Weights</button>
        </div>

        <!-- Tab 1: Comparison HUD -->
        <div class="tab-content active" id="tab-comparison">
          <div class="site-hero-card" id="site-hero-card">
            <div class="hero-title">
              <span id="hero-site-name">Select an Analogue</span>
              <span class="rank-pill" id="hero-rank-badge">#1</span>
            </div>
            <div class="hero-meta" id="hero-site-meta">
              📍 Click any glowing map pin or list card to view verified planetary comparison.
            </div>
            <div class="score-hero-badge">
              <span class="score-hero-val" id="hero-score-val" style="color: var(--accent-emerald);">--</span>
              <span class="score-hero-lbl">Relative Similarity Index [0-100%]</span>
            </div>
          </div>

          <!-- Multi-Axis Radar Canvas -->
          <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); margin-top: 4px;">
            Multi-Feature Radar Comparison (<span style="color:#00f0ff;">■ Earth</span> vs <span style="color:#9d4edd;">■ Target</span>)
          </div>
          <div class="radar-container">
            <canvas id="radar-canvas"></canvas>
          </div>

          <!-- Feature Matrix Table -->
          <div style="font-size: 11px; font-weight: 700; color: #fff; margin-top: 8px;">
            Feature-by-Feature Scientific Matrix
          </div>
          <table class="matrix-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Target</th>
                <th>Earth Value</th>
                <th>Relative Match</th>
              </tr>
            </thead>
            <tbody id="matrix-table-body">
              <!-- Injected via JavaScript -->
            </tbody>
          </table>
        </div>

        <!-- Tab 2: Where the Analogy Breaks Down (Evidence-Based Physical Realities) -->
        <div class="tab-content" id="tab-breakdown">
          <div class="breakdown-banner">
            <h3>⚠️ Essential Scientific Guardrails</h3>
            <p>Terrestrial analogues reproduce specific geological and mechanical parameters, but CANNOT replicate fundamental planetary physics.</p>
          </div>
          <div id="breakdown-cards-container">
            <!-- Injected dynamically -->
          </div>
        </div>

        <!-- Tab 3: Interactive Weight Calibration -->
        <div class="tab-content" id="tab-weights">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 12px; font-weight: 700; color: var(--accent-cyan);">Normalized Feature Weights (Σ = 100%)</span>
            <button class="action-btn" id="btn-reset-weights" style="font-size: 9.5px; padding: 3px 6px;">Reset</button>
          </div>
          <div id="sliders-container">
            <!-- Sliders injected dynamically -->
          </div>
        </div>
      </aside>

      <!-- Mini Planetary Target Context Overlay -->
      <div class="mini-target-overlay">
        <div class="mini-target-title">
          <span id="mini-target-name">Target Context</span>
          <span id="mini-target-body" style="color: var(--accent-cyan);">Moon</span>
        </div>
        <div class="mini-target-desc" id="mini-target-desc">
          Loading planetary target specifications...
        </div>
      </div>
    </div>

    <!-- Bottom HUD Legend & Layer Controls -->
    <footer class="hud-footer">
      <div class="legend-bar-group">
        <span>Similarity Index:</span>
        <div class="legend-gradient-bar"></div>
        <div style="display: flex; gap: 8px; font-size: 9.5px;">
          <span style="color: var(--accent-grey);">N/A</span>
          <span style="color: var(--accent-orange);">&lt;60% Low</span>
          <span style="color: var(--accent-gold);">60-75% Med</span>
          <span style="color: var(--accent-emerald);">&gt;75% High</span>
        </div>
      </div>

      <div class="layer-controls">
        <label>
          <input type="checkbox" id="toggle-heatmap" checked> Heatmap Layer
        </label>
        <span style="color: var(--text-dim);">|</span>
        <span style="font-size: 9.5px; color: var(--text-muted);">Tiles:</span>
        <select class="filter-select" id="select-tile-layer" style="width: 125px; padding: 2px 4px;">
          <option value="dark">Esri Dark Canvas</option>
          <option value="satellite">Esri Satellite</option>
          <option value="nasa">NASA Blue Marble</option>
        </select>
        <span style="color: var(--text-dim);">|</span>
        <span style="font-size: 9.5px; color: var(--text-muted);">Heat Opacity:</span>
        <input type="range" id="heat-opacity" min="0" max="100" value="65" style="width: 60px;">
      </div>
    </footer>
  </div>

  <!-- Raw Embedded JSON Payload (24 Candidates + 3 Target Profiles + 4 Presets) -->
  <script id="terratwin-payload" type="application/json">
{json_data_str}
  </script>

  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

  <!-- Application Logic -->
  <script>
    (function() {{
      const DATA = JSON.parse(document.getElementById('terratwin-payload').textContent);

      // Safe Preset Weights Extractor
      function getPresetWeights(presetName) {{
        const p = DATA.presets[presetName];
        if (!p) return {{}};
        return p.weights ? {{ ...p.weights }} : {{ ...p }};
      }}

      // Application State
      const state = {{
        currentTarget: 'moon_south_pole',
        currentPreset: 'balanced_default',
        currentFilter: 'all',
        selectedContinent: 'all',
        selectedEnv: 'all',
        discoveryMode: false,
        selectedSite: 'Puna Plateau Volcanic Barren',
        searchQuery: '',
        heatOpacity: 0.65,
        showHeatmap: true,
        tileLayerType: 'dark',
        customWeights: getPresetWeights('balanced_default'),
        rankedSites: [],
        markers: {{}},
        heatCircles: []
      }};

      // Map references
      let map = null;
      let darkTileLayer = null;
      let satTileLayer = null;
      let nasaTileLayer = null;
      let heatLayerGroup = null;
      let markerLayerGroup = null;

      // Feature Min/Max Bounds for Normalization
      const FEATURE_MIN_MAX = {{
        relief_20km_m: {{ min: 10.0, max: 7000.0 }},
        slope_20km_deg: {{ min: 0.1, max: 35.0 }},
        roughness_5km_m: {{ min: 1.0, max: 90.0 }},
        roughness_10km_m: {{ min: 2.0, max: 150.0 }},
        roughness_20km_m: {{ min: 4.0, max: 250.0 }},
        hurst_2_32km: {{ min: 0.2, max: 0.95 }},
        temp_mean_c: {{ min: -60.0, max: 35.0 }},
        temp_diurnal_range_c: {{ min: 2.0, max: 30.0 }},
        temp_min_coldest_c: {{ min: -75.0, max: 25.0 }},
        temp_annual_range_c: {{ min: 5.0, max: 70.0 }},
        precip_annual_mm: {{ min: 0.0, max: 3000.0 }},
        precip_driest_month_mm: {{ min: 0.0, max: 200.0 }},
        psr_coverage_fraction: {{ min: 0.0, max: 0.25 }}
      }};

      // 1. Initialize Leaflet Map
      function initMap() {{
        map = L.map('map', {{
          center: [20.0, 0.0],
          zoom: 2.5,
          minZoom: 1.5,
          maxZoom: 12,
          worldCopyJump: true,
          attributionControl: true
        }});

        // 1. Esri Dark Gray Canvas (100% Free, ZERO API Key, CloudFront CDN, Fully supports file://)
        darkTileLayer = L.layerGroup([
          L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
            maxZoom: 16
          }}),
          L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 16
          }})
        ]).addTo(map);

        // 2. Esri Satellite Tiles (100% Free, ZERO API Key)
        satTileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
          attribution: 'Tiles &copy; Esri &mdash; Earthstar Geographics',
          maxZoom: 18
        }});

        // 3. NASA GIBS Blue Marble (100% Free, ZERO API Key)
        nasaTileLayer = L.tileLayer('https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/default/GoogleMapsCompatible_Level8/{{z}}/{{y}}/{{x}}.jpeg', {{
          attribution: 'Tiles &copy; NASA EOSDIS GIBS &mdash; Blue Marble',
          maxZoom: 8
        }});

        heatLayerGroup = L.layerGroup().addTo(map);
        markerLayerGroup = L.layerGroup().addTo(map);

        // Map resize listener
        window.addEventListener('resize', () => {{
          map.invalidateSize();
        }});
      }}

      // 2. Scientific Similarity Scoring Engine (Strictly No Fake 50% Defaults)
      function scoreCandidate(candFeatures, targetProfile, weights) {{
        let accumDist = 0.0;
        let evaluatedWeight = 0.0;
        let totalActiveWeight = 0.0;
        const subscores = {{}};
        const missingFeatures = [];
        const targetFeatures = targetProfile.features || {{}};

        for (const [feat, w] of Object.entries(weights)) {{
          if (w <= 0.0001) continue;
          totalActiveWeight += w;

          const eVal = candFeatures[feat];
          const tObj = targetFeatures[feat];
          const tVal = (tObj && typeof tObj === 'object') ? tObj.value : tObj;

          // If either feature is missing: record honestly without fake scores
          if (eVal === undefined || eVal === null || tVal === undefined || tVal === null) {{
            missingFeatures.push(feat);
            subscores[feat] = null; // Honest missing state
            continue;
          }}

          const bounds = FEATURE_MIN_MAX[feat] || {{ min: 0.0, max: 100.0 }};
          const span = (bounds.max - bounds.min) || 1.0;
          const eNorm = Math.min(1.0, Math.max(0.0, (eVal - bounds.min) / span));
          const tNorm = Math.min(1.0, Math.max(0.0, (tVal - bounds.min) / span));

          // One-sided penalty for precipitation (dryness proxy)
          let dist = 0.0;
          if (feat.includes('precip')) {{
            dist = eNorm;
          }} else {{
            dist = Math.abs(eNorm - tNorm);
          }}

          accumDist += dist * w;
          evaluatedWeight += w;
          subscores[feat] = Math.max(0.0, Math.min(100.0, (1.0 - dist) * 100.0));
        }}

        // Data quality = fraction of active weight successfully verified
        const dataQuality = totalActiveWeight > 0 ? (evaluatedWeight / totalActiveWeight) : 0.0;

        // If less than 40% of requested weight can be evaluated, flag as uncalculated
        if (evaluatedWeight <= 0.0 || dataQuality < 0.4) {{
          return {{
            overallScore: null,
            dataQuality: dataQuality * 100.0,
            subscores,
            matches: [],
            deviations: [],
            missingFeatures,
            isCalculated: false
          }};
        }}

        const compDist = accumDist / evaluatedWeight;
        const overallScore = Math.max(0.0, Math.min(100.0, (1.0 - compDist) * 100.0));

        // Sort valid subscores for top matches and deviations
        const validSubs = Object.entries(subscores)
          .filter(([k, v]) => v !== null)
          .sort((a, b) => b[1] - a[1]);

        const matches = validSubs.slice(0, 3);
        const deviations = validSubs.slice(-2).reverse();

        return {{
          overallScore,
          dataQuality: dataQuality * 100.0,
          subscores,
          matches,
          deviations,
          missingFeatures,
          isCalculated: true
        }};
      }}

      // 3. Recalculate Rankings across all 24 candidates
      function recalculateAll() {{
        const target = DATA.profiles[state.currentTarget];
        const results = [];

        for (const cand of DATA.candidates) {{
          const res = scoreCandidate(cand.features, target, state.customWeights);
          results.push({{
            ...cand,
            overall_score: res.overallScore,
            data_quality_percent: res.dataQuality,
            subscores: res.subscores,
            top_matching_features: res.matches,
            top_deviating_features: res.deviations,
            missing_features: res.missingFeatures,
            is_calculated: res.isCalculated
          }});
        }}

        // Sort: Calculated first by score descending, then uncalculated
        results.sort((a, b) => {{
          if (a.is_calculated && !b.is_calculated) return -1;
          if (!a.is_calculated && b.is_calculated) return 1;
          if (a.is_calculated && b.is_calculated) {{
            return b.overall_score - a.overall_score;
          }}
          return a.name.localeCompare(b.name);
        }});

        state.rankedSites = results;
        renderMapMarkersAndHeat();
        renderCardList();
        renderComparisonDashboard();
        renderBreakdownPanel();
        updateMiniTargetContext();
      }}

      // Helper: Color by Score
      function getScoreColor(score, isCalculated) {{
        if (!isCalculated || score === null || score === undefined) {{
          return '#718096'; // Neutral slate grey
        }}
        if (score >= 75.0) return '#00ff88'; // High similarity (Green)
        if (score >= 60.0) return '#ffcc00'; // Medium similarity (Yellow/Gold)
        return '#ff6600'; // Low similarity (Orange)
      }}

      // 4. Render Markers and Dynamic Heatmap on Map
      function renderMapMarkersAndHeat() {{
        markerLayerGroup.clearLayers();
        heatLayerGroup.clearLayers();
        state.markers = {{}};

        state.rankedSites.forEach((site, index) => {{
          const isSelected = site.name === state.selectedSite;
          const color = getScoreColor(site.overall_score, site.is_calculated);
          const scoreLabel = site.is_calculated ? `${{site.overall_score.toFixed(1)}}%` : 'N/A';

          // Custom Glowing HTML/SVG Marker
          const iconHtml = `
            <div class=\"pulse-marker-container\" title=\"${{site.name}}\">
              <div class=\"pulse-marker-ring\" style=\"border: 1.5px solid ${{color}};\"></div>
              <div class=\"pulse-marker-dot\" style=\"background-color: ${{isSelected ? '#00f0ff' : color}}; color: ${{color}};\"></div>
            </div>
          `;

          const customIcon = L.divIcon({{
            html: iconHtml,
            className: 'custom-leaflet-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          }});

          const marker = L.marker([site.lat, site.lon], {{ icon: customIcon }});

          // Sleek NASA HUD Popup Tooltip
          const popupContent = `
            <div class=\"custom-popup-content\">
              <div class=\"popup-title\">${{site.name}}</div>
              <div class=\"popup-subtitle\">📍 ${{site.country}} (${{site.region || site.continent}}) &bull; ${{site.validation_status === 'validated_analogue' ? 'Validated' : 'Candidate'}}</div>
              <div class=\"popup-score-row\">
                <span style=\"color: var(--text-muted);\">Similarity Index:</span>
                <span style=\"color: ${{color}}; font-weight: 800;\">${{scoreLabel}}</span>
              </div>
              <div style=\"font-size: 9px; color: var(--text-dim); margin-top: 4px;\">
                Top match: ${{site.top_matching_features.length > 0 ? site.top_matching_features[0][0].replace(/_20km|_10km|_5km|_mm|_c/g, '') + ' (' + site.top_matching_features[0][1].toFixed(0) + '%)' : 'None'}}
              </div>
            </div>
          `;
          marker.bindPopup(popupContent);

          marker.on('click', () => {{
            selectSite(site.name);
          }});

          markerLayerGroup.addLayer(marker);
          state.markers[site.name] = marker;

          // Add Dynamic Spatial Heat Halo (if calculated and heatmap enabled)
          if (state.showHeatmap && site.is_calculated) {{
            const heatRadiusMeters = (site.overall_score / 100.0) * 350000; // Realistic spatial radius
            const heatCircle = L.circle([site.lat, site.lon], {{
              radius: heatRadiusMeters,
              color: color,
              weight: 0.8,
              opacity: state.heatOpacity * 0.7,
              fillColor: color,
              fillOpacity: state.heatOpacity * 0.28
            }});
            heatLayerGroup.addLayer(heatCircle);
          }}
        }});
      }}

      // 5. Render Left Sidebar Candidate Cards
      function renderCardList() {{
        const container = document.getElementById('cards-container');
        container.innerHTML = '';

        let filtered = state.rankedSites;

        // Filter: Famous vs Overlooked
        if (state.currentFilter === 'famous') {{
          filtered = filtered.filter(s => s.famous);
        }} else if (state.currentFilter === 'overlooked') {{
          filtered = filtered.filter(s => !s.famous);
        }}

        // Filter: Continent
        if (state.selectedContinent !== 'all') {{
          filtered = filtered.filter(s => s.continent === state.selectedContinent);
        }}

        // Filter: Environment Type
        if (state.selectedEnv !== 'all') {{
          filtered = filtered.filter(s => s.environment_type === state.selectedEnv);
        }}

        // Filter: Search Query
        if (state.searchQuery) {{
          const q = state.searchQuery.toLowerCase();
          filtered = filtered.filter(s => 
            s.name.toLowerCase().includes(q) || 
            s.country.toLowerCase().includes(q) ||
            (s.region && s.region.toLowerCase().includes(q))
          );
        }}

        // Filter: Discovery Mode (highlights unusual environmental profiles)
        if (state.discoveryMode) {{
          filtered = filtered.filter(s => !s.famous && s.data_quality_percent >= 80);
        }}

        document.getElementById('candidate-count-badge').textContent = `${{filtered.length}} Sites`;

        filtered.forEach((site, index) => {{
          const isSelected = site.name === state.selectedSite;
          const color = getScoreColor(site.overall_score, site.is_calculated);
          const scoreClass = !site.is_calculated ? 'missing' : (site.overall_score >= 75 ? 'high' : (site.overall_score >= 60 ? 'medium' : 'low'));
          const scoreLabel = site.is_calculated ? `${{site.overall_score.toFixed(1)}}%` : 'N/A';

          const card = document.createElement('div');
          card.className = `site-card ${{isSelected ? 'selected' : ''}}`;

          // Top matches tags
          const matchTags = site.top_matching_features.slice(0, 2).map(([k, v]) => `
            <div class=\"micro-tag match\" title=\"${{k}}\">✓ ${{k.replace(/_20km|_10km|_5km|_mm|_c/g, '')}}: ${{v.toFixed(0)}}%</div>
          `).join('');

          card.innerHTML = `
            <div class=\"card-top-row\">
              <span class=\"rank-pill\">#${{index + 1}}</span>
              <span class=\"score-indicator ${{scoreClass}}\">${{scoreLabel}}</span>
            </div>
            <h3>${{site.name}}</h3>
            <div class=\"site-card-meta\">
              <span>📍 ${{site.country}} &bull; ${{site.elevation_m ? site.elevation_m + 'm' : ''}}</span>
              <span class=\"micro-tag ${{site.validation_status === 'validated_analogue' ? 'status-val' : 'status-cand'}}\">
                ${{site.validation_status === 'validated_analogue' ? 'Validated' : 'Candidate'}}
              </span>
            </div>
            <div class=\"site-card-tags\">
              ${{matchTags}}
              ${{site.famous ? '<div class=\"micro-tag\" style=\"background:rgba(255,136,0,0.15); color:var(--accent-orange);\">Famous</div>' : '<div class=\"micro-tag\" style=\"background:rgba(0,240,255,0.15); color:var(--accent-cyan);\">Overlooked</div>'}}
            </div>
          `;

          card.addEventListener('click', () => {{
            selectSite(site.name);
            flyToSite(site.lat, site.lon);
          }});

          container.appendChild(card);
        }});
      }}

      // 6. Select a Site and Update Dashboard
      function selectSite(name) {{
        state.selectedSite = name;
        document.querySelectorAll('.site-card').forEach(c => c.classList.remove('selected'));
        renderCardList();
        renderComparisonDashboard();
        renderBreakdownPanel();

        // Highlight marker
        const marker = state.markers[name];
        if (marker) {{
          marker.openPopup();
        }}
      }}

      function flyToSite(lat, lon) {{
        if (map) {{
          map.flyTo([lat, lon], 5.5, {{
            duration: 1.2,
            easeLinearity: 0.25
          }});
        }}
      }}

      // 7. Render Comparison Dashboard & Radar Chart
      function renderComparisonDashboard() {{
        const site = state.rankedSites.find(s => s.name === state.selectedSite) || state.rankedSites[0];
        const target = DATA.profiles[state.currentTarget];
        if (!site || !target) return;

        // Hero Card
        document.getElementById('hero-site-name').textContent = site.name;
        document.getElementById('hero-rank-badge').textContent = `Rank #${{state.rankedSites.indexOf(site) + 1}}`;
        document.getElementById('hero-site-meta').innerHTML = `
          📍 ${{site.country}} (${{site.region || site.continent}}) &bull; Elev: ${{site.elevation_m || 0}} m<br>
          <span style=\"color:var(--text-dim);\">Data Source: ${{site.data_source || 'ETOPO 2022 / WorldClim 2.1'}} &bull; Quality: ${{site.data_quality_percent.toFixed(0)}}%</span>
        `;

        const scoreVal = document.getElementById('hero-score-val');
        if (site.is_calculated) {{
          scoreVal.textContent = `${{site.overall_score.toFixed(1)}}%`;
          scoreVal.style.color = getScoreColor(site.overall_score, true);
        }} else {{
          scoreVal.textContent = 'N/A';
          scoreVal.style.color = 'var(--accent-grey)';
        }}

        // Draw Radar Chart
        drawRadarChart(site, target);

        // Populate Scientific Matrix Table
        const tbody = document.getElementById('matrix-table-body');
        tbody.innerHTML = '';

        const keyFeats = [
          ['slope_20km_deg', 'Mean Slope (20km)', '°'],
          ['roughness_10km_m', 'Roughness (10km)', 'm'],
          ['relief_20km_m', 'Local Relief (20km)', 'm'],
          ['hurst_2_32km', 'Hurst Exponent', ''],
          ['temp_mean_c', 'Mean Annual Temp', '°C'],
          ['temp_diurnal_range_c', 'Diurnal Range ΔT', '°C'],
          ['temp_min_coldest_c', 'Coldest Min Temp', '°C'],
          ['precip_annual_mm', 'Annual Precip', 'mm']
        ];

        keyFeats.forEach(([key, label, unit]) => {{
          const tObj = target.features[key] || {{}};
          const tVal = (typeof tObj === 'object') ? tObj.value : tObj;
          const eVal = site.features[key];
          const sub = site.subscores[key];

          const tr = document.createElement('tr');
          const matchColor = sub === null ? 'var(--accent-grey)' : (sub >= 75 ? 'var(--accent-emerald)' : (sub >= 60 ? 'var(--accent-gold)' : 'var(--accent-ruby)'));
          const matchText = sub === null ? 'N/A' : `${{sub.toFixed(0)}}%`;

          tr.innerHTML = `
            <td style=\"color:var(--text-main); font-weight:600;\">${{label}}</td>
            <td style=\"color:var(--accent-purple);\">${{tVal !== undefined ? tVal + unit : 'N/A'}}</td>
            <td style=\"color:var(--accent-cyan);\">${{eVal !== undefined ? eVal + unit : 'N/A'}}</td>
            <td style=\"color:${{matchColor}}; font-weight:700;\">${{matchText}}</td>
          `;
          tbody.appendChild(tr);
        }});
      }}

      // 8. Canvas Radar Chart Drawer
      function drawRadarChart(site, target) {{
        const rCanvas = document.getElementById('radar-canvas');
        rCanvas.width = rCanvas.clientWidth * 2;
        rCanvas.height = rCanvas.clientHeight * 2;
        const ctx = rCanvas.getContext('2d');
        ctx.scale(2, 2);

        const w = rCanvas.clientWidth;
        const h = rCanvas.clientHeight;
        const cx = w / 2;
        const cy = h / 2;
        const radius = Math.min(cx, cy) - 22;

        ctx.clearRect(0, 0, w, h);

        const axes = [
          {{ key: 'slope_20km_deg', label: 'Slope' }},
          {{ key: 'roughness_10km_m', label: 'Roughness' }},
          {{ key: 'relief_20km_m', label: 'Relief' }},
          {{ key: 'hurst_2_32km', label: 'Hurst' }},
          {{ key: 'temp_diurnal_range_c', label: 'Diurnal ΔT' }},
          {{ key: 'temp_mean_c', label: 'Mean Temp' }}
        ];
        const numAxes = axes.length;

        // Draw concentric web rings
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;
        for (let ring = 1; ring <= 4; ring++) {{
          const r = (radius / 4) * ring;
          ctx.beginPath();
          for (let i = 0; i < numAxes; i++) {{
            const angle = (i * 2 * Math.PI / numAxes) - Math.PI / 2;
            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }}
          ctx.closePath();
          ctx.stroke();
        }}

        // Spokes & Labels
        ctx.fillStyle = '#8ba2c7';
        ctx.font = '9.5px -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        for (let i = 0; i < numAxes; i++) {{
          const angle = (i * 2 * Math.PI / numAxes) - Math.PI / 2;
          const x = cx + radius * Math.cos(angle);
          const y = cy + radius * Math.sin(angle);
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(x, y);
          ctx.stroke();

          const lx = cx + (radius + 14) * Math.cos(angle);
          const ly = cy + (radius + 14) * Math.sin(angle);
          ctx.fillText(axes[i].label, lx, ly);
        }}

        function getNorm(key, val) {{
          if (val === undefined || val === null) return 0.05;
          const b = FEATURE_MIN_MAX[key] || {{ min: 0, max: 100 }};
          return Math.min(1.0, Math.max(0.05, (val - b.min) / (b.max - b.min)));
        }}

        // Draw Target Polygon (Purple)
        ctx.beginPath();
        axes.forEach((ax, i) => {{
          const tObj = target.features[ax.key] || {{}};
          const tVal = (typeof tObj === 'object') ? tObj.value : tObj;
          const norm = getNorm(ax.key, tVal);
          const angle = (i * 2 * Math.PI / numAxes) - Math.PI / 2;
          const x = cx + radius * norm * Math.cos(angle);
          const y = cy + radius * norm * Math.sin(angle);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }});
        ctx.closePath();
        ctx.fillStyle = 'rgba(157, 78, 221, 0.25)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(157, 78, 221, 0.9)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw Earth Site Polygon (Cyan)
        ctx.beginPath();
        axes.forEach((ax, i) => {{
          const eVal = site.features[ax.key];
          const norm = getNorm(ax.key, eVal);
          const angle = (i * 2 * Math.PI / numAxes) - Math.PI / 2;
          const x = cx + radius * norm * Math.cos(angle);
          const y = cy + radius * norm * Math.sin(angle);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }});
        ctx.closePath();
        ctx.fillStyle = 'rgba(0, 240, 255, 0.3)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.95)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }}

      // 9. Render "Where the Analogy Breaks Down" Panel
      function renderBreakdownPanel() {{
        const container = document.getElementById('breakdown-cards-container');
        container.innerHTML = '';
        const target = DATA.profiles[state.currentTarget];
        const isMoon = target.body === 'Moon';

        const limits = [
          {{
            title: 'Surface Gravity Disparity',
            tag: 'Physical Limit',
            badgeClass: 'badge-limit',
            earth: '1.00 g (9.81 m/s²)',
            planet: isMoon ? '0.166 g (~1/6 Earth g)' : '0.376 g (~3/8 Earth g)',
            impact: 'Alters rover wheel tractive force, soil sinkage, slope rollover limits, and astronaut locomotion fatigue.'
          }},
          {{
            title: 'Atmospheric Pressure & Vacuum',
            tag: 'Physical Limit',
            badgeClass: 'badge-limit',
            earth: '101.3 kPa (N₂/O₂ atmosphere)',
            planet: isMoon ? '<10⁻¹⁰ Pa (Ultra-high vacuum)' : '0.61 kPa (Thin CO₂ atmosphere)',
            impact: 'Convective heat transfer is nonexistent; liquid water boils and sublimates immediately on planetary surfaces.'
          }},
          {{
            title: 'Unshielded Ionizing Radiation',
            tag: 'Physical Limit',
            badgeClass: 'badge-limit',
            earth: '~2.4 mSv/year (Geomagnetic shield)',
            planet: isMoon ? '380 mSv/year (Unshielded GCR + SPE)' : '250 mSv/year (Thin atmospheric shield)',
            impact: 'Severe electronic single-event upsets; rapid solar array degradation; DNA double-strand breaks for crew.'
          }},
          {{
            title: 'Regolith Morphology & Sharpness',
            tag: 'Measured Mismatch',
            badgeClass: 'badge-mismatch',
            earth: 'Rounded grains (wind/water weathered)',
            planet: isMoon ? 'Jagged impact glass shards with electrostatic clinging' : 'Oxidized volcanic dust with ~1% perchlorates (ClO₄⁻)',
            impact: 'Planetary regolith aggressively erodes EVA suit seals, bearings, visors, and poses severe respiratory hazards.'
          }},
          {{
            title: isMoon ? 'Cryogenic Cold Trap Temperature' : 'Sub-Zero Permafrost Brines',
            tag: 'Measured Mismatch',
            badgeClass: 'badge-mismatch',
            earth: 'Coldest recorded: -89.2 °C (Vostok)',
            planet: isMoon ? '40 K (-233.15 °C) in Shackleton PSR' : '183 K (-90.15 °C) winter night',
            impact: 'Requires specialized cryogenic lubricants, cold-welding prevention in vacuum, and radioisotope heaters.'
          }}
        ];

        limits.forEach(item => {{
          const div = document.createElement('div');
          div.className = 'breakdown-card';
          div.innerHTML = `
            <div class=\"breakdown-card-header\">
              <span class=\"breakdown-card-title\">${{item.title}}</span>
              <span class=\"${{item.badgeClass}}\">${{item.tag}}</span>
            </div>
            <div class=\"breakdown-diff-grid\">
              <div><span class=\"lbl\">Earth Analogue</span>${{item.earth}}</div>
              <div><span class=\"lbl\">${{target.target_name}}</span>${{item.planet}}</div>
            </div>
            <div class=\"breakdown-impact\">${{item.impact}}</div>
          `;
          container.appendChild(div);
        }});
      }}

      // 10. Render Sliders for Weight Calibration
      function renderSliders() {{
        const container = document.getElementById('sliders-container');
        container.innerHTML = '';

        const sliderDefs = [
          ['slope_20km_deg', 'Mean Slope Gradient (20km)'],
          ['roughness_10km_m', 'High-Pass Roughness (10km)'],
          ['relief_20km_m', 'Local Relief (20km)'],
          ['hurst_2_32km', 'Hurst Exponent (Multi-scale)'],
          ['temp_mean_c', 'Mean Annual Temperature'],
          ['temp_diurnal_range_c', 'Diurnal Temperature Swing'],
          ['temp_min_coldest_c', 'Coldest-Month Temperature'],
          ['precip_annual_mm', 'Dryness / Precipitation']
        ];

        sliderDefs.forEach(([key, label]) => {{
          const val = state.customWeights[key] !== undefined ? state.customWeights[key] : 0.15;
          const row = document.createElement('div');
          row.className = 'slider-item';
          row.innerHTML = `
            <div class=\"slider-header\">
              <span class=\"name\">${{label}}</span>
              <span class=\"val\" id=\"val-${{key}}\">${{(val * 100).toFixed(0)}}%</span>
            </div>
            <input type=\"range\" min=\"0\" max=\"100\" value=\"${{val * 100}}\" data-key=\"${{key}}\">
          `;

          const rangeInput = row.querySelector('input');
          rangeInput.addEventListener('input', (e) => {{
            const newPct = parseFloat(e.target.value);
            state.customWeights[key] = newPct / 100.0;
            row.querySelector('.val').textContent = `${{newPct.toFixed(0)}}%`;
            recalculateAll();
          }});

          container.appendChild(row);
        }});
      }}

      // 11. Update Mini Target Context Overlay
      function updateMiniTargetContext() {{
        const target = DATA.profiles[state.currentTarget];
        document.getElementById('mini-target-name').textContent = target.target_name;
        document.getElementById('mini-target-body').textContent = target.body;
        document.getElementById('mini-target-desc').innerHTML = `
          <strong>Mission:</strong> ${{target.mission_context || 'Planetary Science'}}<br>
          <strong>CRS:</strong> ${{target.aoi ? target.aoi.crs.split(' ')[0] : 'Orthographic'}}<br>
          <strong>Relief:</strong> ${{target.features.relief_20km_m ? target.features.relief_20km_m.value + 'm' : 'N/A'}} &bull; 
          <strong>Slope:</strong> ${{target.features.slope_20km_deg ? target.features.slope_20km_deg.value + '°' : 'N/A'}}
        `;
      }}

      // 12. Setup UI Event Listeners
      function setupListeners() {{
        // Target selection
        document.querySelectorAll('.target-btn').forEach(btn => {{
          btn.addEventListener('click', () => {{
            document.querySelectorAll('.target-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentTarget = btn.dataset.target;
            recalculateAll();
          }});
        }});

        // Preset selection
        document.querySelectorAll('.preset-btn[data-preset]').forEach(btn => {{
          btn.addEventListener('click', () => {{
            document.querySelectorAll('.preset-btn[data-preset]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentPreset = btn.dataset.preset;
            state.customWeights = getPresetWeights(state.currentPreset);
            renderSliders();
            recalculateAll();
          }});
        }});

        // Famous vs Overlooked filter pills
        document.querySelectorAll('.filter-pill').forEach(pill => {{
          pill.addEventListener('click', () => {{
            document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            state.currentFilter = pill.dataset.filter;
            renderCardList();
          }});
        }});

        // Continent filter
        document.getElementById('filter-continent').addEventListener('change', (e) => {{
          state.selectedContinent = e.target.value;
          renderCardList();
        }});

        // Environment filter
        document.getElementById('filter-env').addEventListener('change', (e) => {{
          state.selectedEnv = e.target.value;
          renderCardList();
        }});

        // Discovery mode toggle
        document.getElementById('toggle-discovery').addEventListener('change', (e) => {{
          state.discoveryMode = e.target.checked;
          renderCardList();
        }});

        // Search input
        document.getElementById('site-search-input').addEventListener('input', (e) => {{
          state.searchQuery = e.target.value;
          renderCardList();
        }});

        // Heatmap toggle
        document.getElementById('toggle-heatmap').addEventListener('change', (e) => {{
          state.showHeatmap = e.target.checked;
          renderMapMarkersAndHeat();
        }});

        // Heat opacity
        document.getElementById('heat-opacity').addEventListener('input', (e) => {{
          state.heatOpacity = parseFloat(e.target.value) / 100.0;
          renderMapMarkersAndHeat();
        }});

        // Tile layer switcher
        document.getElementById('select-tile-layer').addEventListener('change', (e) => {{
          const type = e.target.value;
          state.tileLayerType = type;
          map.removeLayer(darkTileLayer);
          map.removeLayer(satTileLayer);
          if (nasaTileLayer) map.removeLayer(nasaTileLayer);

          if (type === 'satellite') {{
            satTileLayer.addTo(map);
          }} else if (type === 'nasa') {{
            nasaTileLayer.addTo(map);
          }} else {{
            darkTileLayer.addTo(map);
          }}
        }});

        // Global view reset
        document.getElementById('btn-reset-view').addEventListener('click', () => {{
          if (map) {{
            map.flyTo([20.0, 0.0], 2.5, {{ duration: 1.0 }});
          }}
        }});

        // Reset weights
        document.getElementById('btn-reset-weights').addEventListener('click', () => {{
          state.customWeights = getPresetWeights(state.currentPreset);
          renderSliders();
          recalculateAll();
        }});

        // Open weights tab
        document.getElementById('btn-open-weights').addEventListener('click', () => {{
          document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
          document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
          document.querySelector('.tab-btn[data-tab=\"tab-weights\"]').classList.add('active');
          document.getElementById('tab-weights').classList.add('active');
          document.getElementById('sidebar-right').classList.remove('collapsed');
        }});

        // Sidebar Toggles
        document.getElementById('btn-toggle-left').addEventListener('click', () => {{
          const left = document.getElementById('sidebar-left');
          left.classList.toggle('collapsed');
          document.getElementById('btn-toggle-left').textContent = left.classList.contains('collapsed') ? '▶' : '◀';
        }});

        document.getElementById('btn-toggle-right').addEventListener('click', () => {{
          const right = document.getElementById('sidebar-right');
          right.classList.toggle('collapsed');
          document.getElementById('btn-toggle-right').textContent = right.classList.contains('collapsed') ? '◀' : '▶';
        }});

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {{
          btn.addEventListener('click', () => {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
          }});
        }});
      }}

      // Init Application
      initMap();
      renderSliders();
      setupListeners();
      recalculateAll();

    }})();
  </script>
</body>
</html>
"""

OUTPUT_HTML = FRONTEND_DIR / "index.html"
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Redesigned frontend built successfully at: {OUTPUT_HTML} ({len(html_template)} bytes)")
