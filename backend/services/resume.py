from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Education(BaseModel):
    school: str
    location: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[float] = None
    graduation: Optional[str] = None
    honors: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    title: str
    organization: Optional[str] = None
    location: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    bullets: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    visa_status: Optional[str] = None
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    skills: dict[str, list[str]] = Field(default_factory=dict)
    target_roles: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
