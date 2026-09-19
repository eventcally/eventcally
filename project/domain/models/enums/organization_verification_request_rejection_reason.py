from enum import IntEnum


class OrganizationVerificationRequestRejectionReason(IntEnum):
    notresponsible = 1
    missinginformation = 2
    unknown = 3
    untrustworthy = 4
    illegal = 5
    irrelevant = 6
