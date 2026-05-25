#!/usr/bin/env python3
"""Extract design tokens from beautiful-html-templates for material library.

Usage: python3 extract_tokens.py [template_dir] [output_dir]
"""
import json, os, re, sys, html
from pathlib import Path
from html.parser import HTMLParser

class TokenExtractor(HTMLParser):
    """Extract CSS custom properties, color values, and font families from HTML/CSS."""
    def __init__(self):
        super().__init__()
        self.css_vars = {}
        self.colors = set()
        self.fonts = set()
        self.in_style = False
        self.style_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            self.in_style = True
        attrs_d = dict(attrs)
        style_attr = attrs_d.get('style', '')
        if style_attr:
            self._parse_inline_style(style_attr)

    def handle_endtag(self, tag):
        if tag == 'style' and self.in_style:
            self.in_style = False
            self._parse_css_block(self.style_text)
            self.style_text = ""

    def handle_data(self, data):
        if self.in_style:
            self.style_text += data

    def _parse_css_block(self, css):
        # Extract CSS custom properties
        for match in re.finditer(r'(--[\w-]+)\s*:\s*([^;]+)', css):
            self.css_vars[match.group(1)] = match.group(2).strip()
        # Extract hex colors
        for match in re.finditer(r'(#[0-9a-fA-F]{3,8})\b', css):
            self.colors.add(match.group(1).upper())
        # Extract rgb/rgba colors
        for match in re.finditer(r'rgba?\s*\([^)]+\)', css):
            self.colors.add(match.group(0))
        # Extract font families
        for match in re.finditer(r"font-family\s*:\s*([^;]+)", css):
            fonts = [f.strip().strip("'\"") for f in match.group(1).split(',')]
            self.fonts.update(fonts)

    def _parse_inline_style(self, style):
        self._parse_css_block(style)


def extract_from_file(filepath: str) -> dict:
    """Extract tokens from an HTML file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    extractor = TokenExtractor()
    extractor.feed(content)
    
    return {
        "file": filepath,
        "css_variables": extractor.css_vars,
        "colors": sorted(extractor.colors),
        "fonts": sorted(extractor.fonts),
        "css_var_count": len(extractor.css_vars),
        "color_count": len(extractor.colors),
        "font_count": len(extractor.fonts),
    }


def main():
    template_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/beautiful-html-templates"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "presentation-materials/design-tokens"
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    for root, dirs, files in os.walk(template_dir):
        for f in files:
            if f.endswith('.html') or f.endswith('.css'):
                path = os.path.join(root, f)
                try:
                    token = extract_from_file(path)
                    results.append(token)
                    print(f"  {token['css_var_count']} vars | {token['color_count']} colors | {token['font_count']} fonts — {os.path.relpath(path, template_dir)}")
                except Exception as e:
                    print(f"  ERROR: {f} — {e}")
    
    # Aggregate
    all_vars = {}
    all_colors = set()
    all_fonts = set()
    for r in results:
        all_vars.update(r['css_variables'])
        all_colors.update(r['colors'])
        all_fonts.update(r['fonts'])
    
    # Save
    summary = {
        "source": "beautiful-html-templates",
        "total_files": len(results),
        "unique_css_variables": len(all_vars),
        "unique_colors": len(all_colors),
        "unique_fonts": len(all_fonts),
        "css_variables": dict(sorted(all_vars.items())),
        "colors": sorted(all_colors),
        "fonts": sorted(all_fonts),
        "per_file": results,
    }
    
    out = os.path.join(output_dir, "beautiful-html-templates-tokens.json")
    with open(out, 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved to {out}")
    print(f"   {len(all_vars)} CSS vars, {len(all_colors)} colors, {len(all_fonts)} fonts")

if __name__ == "__main__":
    main()