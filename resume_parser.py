import re
import spacy
nlp = spacy.load("en_core_web_sm")

# try:
#     nlp = spacy.load("en_core_web_sm")
# except OSError:
#     import spacy.cli
#     spacy.cli.download("en_core_web_sm")
#     nlp = spacy.load("en_core_web_sm")

from spacy.matcher import PhraseMatcher

EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE = re.compile(r"(\+?\d{1,3}[-\s]?)?(\d{3}[-\s]?\d{3}[-\s]?\d{4}|\d{10})")
#PHONE = re.compile(r"\+?\d[\d\s-]{8,}\d")  # simpler and more reliable

skillSet = [
    "python","django","flask","next","mvc","asp.net","c#",
    "aws","docker","git","javascript","react",
]

skillsMatcher = PhraseMatcher(nlp.vocab, attr="LOWER")
skillsMatcher.add("SKILL", [nlp.make_doc(s) for s in skillSet])

def parse_resume(text):
    doc=nlp(text)
    # email 
    emails =list(dict.fromkeys(EMAIL.findall(text)))

        # Phones 
    phoneMatch = PHONE.findall(text)
    phones = []

    for match in phoneMatch:
        if isinstance(match, tuple):
            phones.append("".join(match))
        else:
            phones.append(match)
    phones = list(dict.fromkeys(phones))
#skills
    matches = skillsMatcher(doc)
    skills = set()
    for mid, start, end in matches:
        skills.add(doc[start:end].text.lower())
    # for s in extra_skills:
    #     if s.lower() in text.lower(): skills.add(s.lower())

     # experience detection: "3 years", "5 yrs" etc.
    expYears = 0
    m = re.search(r"(\d+)\s*\+?\s*(?:years|yrs)\b", text, re.I)
    if m:
        expYears = int(m.group(1))
    else:
        if re.search(r"\b(senior|lead|manager)\b", text, re.I):
            expYears = max(expYears, 5)

    # name heuristic: first non-empty line or PERSON entity
    # lines = [l.strip() for l in text.splitlines() if l.strip()]
    # name = None
    # if lines:
    #     first = lines[0]
    #     if 2 <= len(first.split()) <= 4:
    #         name = first
    # persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    # if not name and persons:
    #     name = persons[0]

    #     # --- Name extraction ---
    persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
    name = persons[0] if persons else None

    # fallback to first reasonable line
    if not name:
        for line in text.splitlines():
            line = line.strip()
            if (
            2 <= len(line.split()) <= 4
            and not any(c.isdigit() for c in line)
            and not re.search(r"\b(education|experience|skills|summary|contact)\b", line, re.I)
            ):
                name = line
                break
    if name:
        name = name.split("\n")[0].strip()

    return {
        "name": name,
        "emails": emails,
        "phones": phones,
        "skills": sorted(skills),
        "experience_years": expYears
    }
