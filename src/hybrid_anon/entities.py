from dataclasses import dataclass


@dataclass(frozen=True)
class EntitySpan:
    start: int
    end: int
    label: str
    score: float
    source: str

    def as_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "label": self.label,
                "score": round(self.score, 3), "source": self.source}
