from neighborly.ai import behavior_utils
from neighborly.core.social_practice import (
    SocialPracticeConfig,
    register_social_practice,
)

register_social_practice(
    SocialPracticeConfig(
        name="child",
        description="This character is a child",
        preconditions=[
            lambda world, roles, metadata: behavior_utils.is_child(
                world, roles["subject"][0]
            )
        ],
        behaviors={},
        update_fn=lambda roles, metadata: True,
    )
)

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

register_social_practice(
    SocialPracticeConfig(
        name="default",
        description="Default social practice given to all characters.",
        preconditions=[
            lambda world, roles, metadata: behavior_utils.is_senior(
                world, roles["subject"][0]
            )
        ],
        behaviors={"all": ["die", "socialize"]},
        update_fn=lambda roles, metadata: True,
    )
)
