from dataclasses import dataclass
from typing import Optional, List, Dict, Union


@dataclass
class ScheduledActivity:
    """
    Activity scheduled to take place at a specific place and time
    Attribute Fields
    ----------------
    time : int
        hour during the day that this activity takes place
    duration : int
        hours to spent doing this activity
    location : str
        where the activity is taking place
    activity : str
        what is the character going to do at this place
    """
    time: int
    duration: int
    location: Union[str, int]
    activity: str


class ScheduleConflictError(Exception):
    """
    Exception thrown when someone tries to schedule two
    activities that temporally conflict with one another
    """

    def __init__(self, existing_activity: 'ScheduledActivity', new_activity: 'ScheduledActivity') -> None:
        super().__init__()
        self.existing_activity = existing_activity
        self.new_activity = new_activity
        self.message = f'Scheduling conflict between {existing_activity} and {new_activity}'

    def __str__(self) -> str:
        """Return string representation"""
        return self.message


class DailyRoutine:
    """
    A character's daily routine on a 24-hour schedule
    Attributes
    ----------
    _activities : List[Activity]
        activities that this character has scheduled in their routine
    _schedule : List[Optional[Activity]]
        schedule represented as a list of length 24 (for 24 hrs/day)
        None entries represent free time
    """

    __slots__ = "_activities", "_schedule"

    def __init__(self) -> None:
        self._activities: List['ScheduledActivity'] = []
        self._schedule: List[Optional['ScheduledActivity']] = [None] * 24

    def get_activity(self, hour: int) -> Optional['ScheduledActivity']:
        """
        Return the activity a character is supposed to be doing given the time
        If there is nothing scheduled, assume free time for one hour
        """
        if not isinstance(hour, int):
            raise TypeError(
                f'expected hour to be \'int\', but was \'{type(hour).__name__}\'')
        if hour < 0 or hour > 23:
            raise ValueError(
                f'given value for hour ({hour}) need to be on the interval [0,23] inclusive')

        return self._schedule[hour]

    def add_activity(self, new_activity: 'ScheduledActivity') -> None:
        """
        Add a Activity and update the schedule
        """
        if not isinstance(new_activity, ScheduledActivity):
            raise TypeError(
                f'Expected \'Activity\' object, but received {type(new_activity).__name__}')

        for hour in range(new_activity.time, min(new_activity.time + new_activity.duration, 24)):
            existing_activity = self._schedule[hour]
            if existing_activity is not None:
                raise ScheduleConflictError(existing_activity, new_activity)
            self._schedule[hour] = new_activity
        self._activities.append(new_activity)

    def remove_activity(self, activity: 'ScheduledActivity') -> None:
        """
        Remove an activity from the daily routine
        """
        if not isinstance(activity, ScheduledActivity):
            raise TypeError(
                f'Expected \'Activity\' object, but received {type(activity).__name__}')

        self._activities.remove(activity)
        for i in range(len(self._schedule)):
            if self._schedule[i] == activity:
                self._schedule[i] = None

    def pretty_print(self) -> None:
        """Print this routine"""
        activity_str_list: List[str] = []

        for i, activity in enumerate(self._schedule):
            if activity:
                activity_str_list.append(
                    f'({i:02}:00) => {activity.activity} @ {activity.location}\n')
            else:
                activity_str_list.append(f'({i:02}:00) => Free\n')

        print(f'=== Routine ===\n{"".join(activity_str_list)}')

    def __repr__(self) -> str:
        """Return printable representation"""
        activity_str_list: List[str] = []

        for i, activity in enumerate(self._schedule):
            if activity:
                activity_str_list.append(
                    f'({i:02}:00) => {activity.activity} @ {activity.location}')
            else:
                activity_str_list.append(f'({i:02}:00) => Free')

        return f'Routine({", ".join(activity_str_list)})'


class DailyRoutineFactory:
    """
    Constructs DailyRoutine objects
    This factory does not maintain any references to the objects after creation
    """

    @staticmethod
    def get_student_routine() -> 'DailyRoutine':
        """Construct routine for someone who goes to school during the day"""
        routine = DailyRoutine()
        routine.add_activity(ScheduledActivity(0, 6, '@home', 'resting'))
        routine.add_activity(ScheduledActivity(7, 8, '@school', 'learning'))
        routine.add_activity(ScheduledActivity(21, 3, '@home', 'resting'))
        return routine

    @staticmethod
    def get_day_shift_routine() -> 'DailyRoutine':
        """Construct routine for someone who works the day shift"""
        routine = DailyRoutine()
        routine.add_activity(ScheduledActivity(0, 6, '@home', 'resting'))
        routine.add_activity(ScheduledActivity(7, 8, '@work', 'working'))
        routine.add_activity(ScheduledActivity(21, 3, '@home', 'resting'))
        return routine

    @staticmethod
    def get_night_shift_routine() -> 'DailyRoutine':
        """Construct routine for someone who works the night shift"""
        routine = DailyRoutine()
        routine.add_activity(ScheduledActivity(22, 2, '@work', 'working'))
        routine.add_activity(ScheduledActivity(0, 6, '@work', 'working'))
        routine.add_activity(ScheduledActivity(8, 8, '@home', 'resting'))
        return routine

    @staticmethod
    def get_weekend_routine(run_errands: bool = True) -> 'DailyRoutine':
        """Construct routine for someone's weekend"""
        routine = DailyRoutine()
        routine.add_activity(ScheduledActivity(0, 8, '@home', 'resting'))
        if run_errands:
            routine.add_activity(ScheduledActivity(11, 3, '@any', 'errands'))
        return routine


class Routine:
    """
    Manage a character's routine for the week
    """

    __slots__ = "_daily_routines"

    def __init__(
            self,
            sunday: Optional[DailyRoutine] = None,
            monday: Optional[DailyRoutine] = None,
            tuesday: Optional[DailyRoutine] = None,
            wednesday: Optional[DailyRoutine] = None,
            thursday: Optional[DailyRoutine] = None,
            friday: Optional[DailyRoutine] = None,
            saturday: Optional[DailyRoutine] = None,
    ) -> None:
        self._daily_routines: Dict[str, 'DailyRoutine'] = {
            'sunday': sunday if sunday else DailyRoutineFactory.get_weekend_routine(),
            'monday': monday if monday else DailyRoutine(),
            'tuesday': tuesday if tuesday else DailyRoutine(),
            'wednesday': wednesday if wednesday else DailyRoutine(),
            'thursday': thursday if thursday else DailyRoutine(),
            'friday': friday if friday else DailyRoutine(),
            'saturday': saturday if saturday else DailyRoutineFactory.get_weekend_routine(),
        }

    def add_activity_to_days(self, days: List[str], activity: 'ScheduledActivity') -> None:
        for day in days:
            self._daily_routines[day].add_activity(activity)

    def get_activity(self, day: str, hour: int) -> Optional['ScheduledActivity']:
        """Get the scheduled activity for a given day and time"""
        daily_routine = self._daily_routines.get(day.lower())

        if daily_routine is None:
            raise ValueError(
                f'Expected day of the week, but received \'{day}\'')

        return daily_routine.get_activity(hour)
