"""NPO assistant package."""
from .ai import generate_daily_todo, plan_meeting
from .data_loader import find_donor, load_donors, load_schedule
from .models import Donor, Interaction, ScheduleEntry

__all__ = [
    "generate_daily_todo",
    "plan_meeting",
    "find_donor",
    "load_donors",
    "load_schedule",
    "Donor",
    "Interaction",
    "ScheduleEntry",
]
