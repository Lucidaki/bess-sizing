"""
Template Inference Module

Maps user answers about their system constraints to the appropriate
dispatch template (T0-T6). This allows users to describe their system
in plain language rather than selecting technical templates directly.

Template Reference:
    T0: Solar + BESS Only (no DG)
    T1: Green Priority (DG as last resort, anytime)
    T2: DG Night Charge (proactive charging at night)
    T3: DG Blackout Window (custom hours when DG cannot run)
    T4: DG Emergency Only (SoC-triggered, anytime)
    T5: DG Day Charge (SoC-triggered, day only)
    T6: DG Night SoC Trigger (SoC-triggered, night only)
"""

from typing import Dict, Optional, Tuple


# Template definitions with user-friendly descriptions
TEMPLATES = {
    0: {
        'id': 0,
        'name': 'Solar + BESS Only',
        'short_name': 'Pure Green',
        'description': 'No generator - solar and battery only',
        'merit_order': 'Solar → Battery → Unserved',
        'dg_enabled': False,
    },
    1: {
        'id': 1,
        'name': 'Green Priority',
        'short_name': 'Green Priority',
        'description': 'Generator runs only when battery depleted',
        'merit_order': 'Solar → Battery → Generator → Unserved',
        'dg_enabled': True,
    },
    2: {
        'id': 2,
        'name': 'DG Night Charge',
        'short_name': 'Night Charge',
        'description': 'Generator charges battery proactively at night',
        'merit_order': 'Solar → DG → Battery',
        'dg_enabled': True,
    },
    3: {
        'id': 3,
        'name': 'DG Blackout Window',
        'short_name': 'Blackout Window',
        'description': 'Generator cannot run during specified hours',
        'merit_order': 'Solar → Battery → Generator (when allowed)',
        'dg_enabled': True,
    },
    4: {
        'id': 4,
        'name': 'DG Emergency Only',
        'short_name': 'Emergency Only',
        'description': 'Generator starts only when battery drops below threshold',
        'merit_order': 'Solar → Battery → Generator (SoC trigger)',
        'dg_enabled': True,
    },
    5: {
        'id': 5,
        'name': 'DG Day Charge',
        'short_name': 'Day Charge',
        'description': 'Generator can only run during day hours, SoC-triggered',
        'merit_order': 'Solar → Battery → Generator (day only)',
        'dg_enabled': True,
    },
    6: {
        'id': 6,
        'name': 'DG Night SoC Trigger',
        'short_name': 'Night SoC Trigger',
        'description': 'Generator runs at night when battery low',
        'merit_order': 'Solar → Battery → Generator (night, SoC trigger)',
        'dg_enabled': True,
    },
}


def infer_template(
    dg_enabled: bool,
    dg_timing: str = 'anytime',
    dg_trigger: str = 'reactive',
    blackout_start: Optional[int] = None,
    blackout_end: Optional[int] = None
) -> int:
    """
    Infer the appropriate dispatch template from user answers.

    Args:
        dg_enabled: Whether a diesel generator is included in the system
        dg_timing: When can the generator run?
            - 'anytime': No time restrictions
            - 'day_only': Only during day hours (e.g., 6:00-18:00)
            - 'night_only': Only during night hours
            - 'custom_blackout': Cannot run during specified hours
        dg_trigger: What triggers the generator to start?
            - 'reactive': When load cannot be met by solar + battery
            - 'soc_based': When battery SoC drops below threshold
            - 'proactive': At start of allowed window (pre-emptive charging)
        blackout_start: Start hour of blackout window (0-23), for custom_blackout
        blackout_end: End hour of blackout window (0-23), for custom_blackout

    Returns:
        Template ID (0-6)

    Examples:
        >>> infer_template(dg_enabled=False)
        0  # T0 - Solar + BESS Only

        >>> infer_template(dg_enabled=True, dg_timing='anytime', dg_trigger='reactive')
        1  # T1 - Green Priority

        >>> infer_template(dg_enabled=True, dg_timing='night_only', dg_trigger='proactive')
        2  # T2 - DG Night Charge
    """
    # No generator = Template 0
    if not dg_enabled:
        return 0

    # DG timing determines primary template selection
    if dg_timing == 'anytime':
        # Anytime operation: reactive (T1) or SoC-based (T4)
        if dg_trigger == 'reactive':
            return 1  # T1 - Green Priority
        else:  # soc_based
            return 4  # T4 - Emergency Only

    elif dg_timing == 'day_only':
        # Day only operation: always SoC-triggered
        return 5  # T5 - DG Day Charge

    elif dg_timing == 'night_only':
        # Night only: proactive (T2) or SoC-based (T6)
        if dg_trigger == 'proactive':
            return 2  # T2 - DG Night Charge
        else:  # soc_based
            return 6  # T6 - Night SoC Trigger

    elif dg_timing == 'custom_blackout':
        # Custom blackout window
        return 3  # T3 - DG Blackout Window

    # Default to Green Priority if somehow nothing matches
    return 1


def get_template_info(template_id: int) -> Dict:
    """
    Get detailed information about a template.

    Args:
        template_id: Template ID (0-6)

    Returns:
        Dictionary with template details
    """
    return TEMPLATES.get(template_id, TEMPLATES[1])


def get_template_display_card(template_id: int) -> Tuple[str, str, str]:
    """
    Get display information for showing template in a UI card.

    Args:
        template_id: Template ID (0-6)

    Returns:
        Tuple of (name, merit_order, description)
    """
    info = get_template_info(template_id)
    return (info['name'], info['merit_order'], info['description'])


def get_valid_triggers_for_timing(dg_timing: str) -> list:
    """
    Get valid trigger options based on timing selection.

    Args:
        dg_timing: The selected timing option

    Returns:
        List of valid trigger options with display labels
    """
    if dg_timing == 'anytime':
        return [
            ('reactive', 'When battery + solar cannot meet load'),
            ('soc_based', 'When battery charge drops below threshold'),
        ]
    elif dg_timing == 'day_only':
        return [
            ('soc_based', 'When battery charge drops below threshold'),
        ]
    elif dg_timing == 'night_only':
        return [
            ('proactive', 'At start of night (pre-emptive charging)'),
            ('soc_based', 'When battery charge drops below threshold'),
        ]
    elif dg_timing == 'custom_blackout':
        return [
            ('reactive', 'When battery + solar cannot meet load'),
        ]
    return []


def validate_template_params(
    dg_enabled: bool,
    dg_timing: str,
    dg_trigger: str,
    soc_on: float = 0.30,
    soc_off: float = 0.80,
    blackout_start: Optional[int] = None,
    blackout_end: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate template parameters and return any warnings.

    Returns:
        Tuple of (is_valid, warning_message)
    """
    if not dg_enabled:
        return True, None

    # Validate SoC thresholds for SoC-based triggers
    if dg_trigger == 'soc_based':
        if soc_on >= soc_off:
            return False, "SoC ON threshold must be less than OFF threshold"

        deadband = soc_off - soc_on
        if deadband < 0.20:
            return True, f"Warning: Small deadband ({deadband*100:.0f}%) may cause frequent cycling"

    # Validate blackout window
    if dg_timing == 'custom_blackout':
        if blackout_start is None or blackout_end is None:
            return False, "Blackout start and end hours are required"
        if blackout_start == blackout_end:
            return False, "Blackout start and end cannot be the same"

    return True, None
