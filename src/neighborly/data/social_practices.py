from neighborly.core.social_practice import (
    SocialPracticeConfig,
    register_social_practice,
)
from neighborly.core import behavior_utils

register_social_practice(
    SocialPracticeConfig(
        name="adult",
        description="This character is a legal adult",
        preconditions=[
            lambda world, roles, metadata: behavior_utils.is_adult(
                world, roles["subject"][0]
            )
        ],
        behaviors={"all": ["look for job"]},
        update_fn=lambda roles, metadata: True,
    )
)

register_social_practice(
    SocialPracticeConfig(
        name="senior",
        description="This character is a senior citizen",
        preconditions=[
            lambda world, roles, metadata: behavior_utils.is_senior(
                world, roles["subject"][0]
            )
        ],
        behaviors={"all": ["look for job"]},
        update_fn=lambda roles, metadata: True,
    )
)
