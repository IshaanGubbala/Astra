"""Design specialist — wireframes, mockups, color palettes, design specs, logo briefs."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.design_tools import (
    generate_wireframe,
    generate_color_palette,
    generate_design_spec,
    generate_logo_brief,
)
from backend.tools.web_search import web_search


def build_design_agent(**kwargs) -> Agent:
    return Agent(
        name="design",
        role=(
            "You are a design specialist. Create wireframes, design systems, and visual specs. "
            "generate_design_spec produces a full design system. generate_color_palette creates brand colors. "
            "generate_wireframe creates page wireframes — call once per key page. "
            "generate_logo_brief produces a logo direction brief. "
            "web_search finds competitor designs or inspiration as needed. "
            "Call obsidian_log then done with concrete design artifacts."
        ),
        tools={
            "generate_wireframe": generate_wireframe,
            "generate_color_palette": generate_color_palette,
            "generate_design_spec": generate_design_spec,
            "generate_logo_brief": generate_logo_brief,
            "web_search": web_search,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
