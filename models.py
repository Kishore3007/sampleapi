from pydantic import BaseModel, Field

# Define a model for structuring job application data with dynamic fields
class Projects(BaseModel):
    project_title: str = Field(..., alias="project title")
    project_description: str = Field(..., alias="project description")
    project_company: str = Field(..., alias="project company")
    class Config:
        extra = 'allow'

class Certifications(BaseModel):
    certificate_title: str = Field(..., alias="certificate title")
    certification_provider: str = Field(..., alias="certification provider")
    class Config:
        extra = 'allow'

class JobHistory(BaseModel):
    job_title: str = Field(..., alias="job title")
    job_company: str = Field(..., alias="job company")
    job_description: str = Field(..., alias="job description")
    class Config:
        extra = 'allow'

class Education(BaseModel):
    class Config:
        extra = 'allow'

class Designation(BaseModel):
    class Config:
        extra = 'allow'

class PrimaryExperience(BaseModel):
    job_history: list[JobHistory] = Field(..., alias="job history")
    class Config:
        extra = 'allow'

class SecondaryExperience(BaseModel):
    certifications: list[Certifications]
    projects: list[Projects]
    class Config:
        extra = 'allow'

class JobApplicationData(BaseModel):
    name: str
    designation: list[Designation]
    contact_number: list[str] = Field(..., alias="contact number")
    email_address: str = Field(..., alias="email address")
    education: list[Education]
    current_company_name: str = Field(..., alias="current company name")
    current_location: str = Field(..., alias="current location")
    primary_skills: list[str] = Field(..., alias="primary skills")
    secondary_skills: list[str] = Field(..., alias="secondary skills")
    total_experience: int = Field(..., alias="total experience")
    relevant_experience_primary: list[PrimaryExperience] = Field(..., alias="relevant experience (primary skills)")
    relevant_experience_secondary: list[SecondaryExperience] = Field(..., alias="relevant experience (secondary skills)")
    applicant_description: str

    class Config:
        extra = 'allow'
        allow_population_by_field_name = True
