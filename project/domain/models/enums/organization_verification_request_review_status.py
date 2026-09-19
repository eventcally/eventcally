from enum import IntEnum


class OrganizationVerificationRequestReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3
