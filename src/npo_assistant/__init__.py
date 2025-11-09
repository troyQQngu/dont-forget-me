"""NPO assistant package."""
from .ai import generate_daily_todo, plan_meeting, reflect_on_meeting
from .data_loader import find_donor, load_donors, load_schedule
from .llm import OpenAIChatClient
from .models import Donor, Interaction, ScheduleEntry

__all__ = [
    "generate_daily_todo",
    "plan_meeting",
    "reflect_on_meeting",
    "find_donor",
    "load_donors",
    "load_schedule",
    "OpenAIChatClient",
    "Donor",
    "Interaction",
    "ScheduleEntry",
]
