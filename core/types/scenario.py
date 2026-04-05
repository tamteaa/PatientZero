from dataclasses import dataclass, field


@dataclass
class Scenario:
    test_name: str
    results: str
    normal_range: str
    significance: str
    keywords: list[str] = field(default_factory=list)
