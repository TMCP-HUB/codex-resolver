#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_REQUIRED_TRUE = {"MACHINE_EXECUTABLE","CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS","OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS"}
DEFAULT_REQUIRED_FALSE = {"REQUIRES_THIRD_PARTY_HUMAN","REQUIRES_OWNER_MANUAL_RESEARCH","REQUIRES_EXTERNAL_HUMAN_REVIEW","REQUIRES_HUMAN_DATA_COLLECTION"}
WP_REQUIRED_FALSE = DEFAULT_REQUIRED_FALSE | {"REQUIRES_EXTERNAL_REVIEWER","REQUIRES_NEW_HUMAN_DATA"}
QUESTION_REQUIRED_FIELDS = {"QUESTION_ID","QUESTION","TARGET_CONSTRUCT","MACHINE_EXECUTABLE","AVAILABLE_MACHINE_METHODS","AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE","REQUIRES_THIRD_PARTY_HUMAN","REQUIRES_OWNER_MANUAL_RESEARCH","REQUIRES_EXTERNAL_HUMAN_REVIEW","REQUIRES_HUMAN_DATA_COLLECTION","DIRECT_MEASUREMENT_POSSIBLE","PROXY_MEASUREMENT_POSSIBLE","EXPECTED_LIMITATION","OWNER_DECISION_COMPONENT","CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS","OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS","ADMISSION_STATUS"}
WORK_PACKAGE_REQUIRED_FIELDS = {"WORK_PACKAGE_ID","QUESTION_ID","NAMESPACE","EXECUTOR_ROLE","VERIFIER_ROLE","MACHINE_EXECUTABLE","REQUIRES_THIRD_PARTY_HUMAN","REQUIRES_OWNER_MANUAL_RESEARCH","REQUIRES_EXTERNAL_REVIEWER","REQUIRES_EXTERNAL_HUMAN_REVIEW","REQUIRES_NEW_HUMAN_DATA","REQUIRES_HUMAN_DATA_COLLECTION","CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS","OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS","EXECUTION_SURFACE","SOURCE_ACCESS_METHOD","COMPUTATION_METHOD","VERIFICATION_METHOD","LIMITATIONS","PROHIBITED_OVERCLAIMS","OWNER_GATE_IF_ANY"}
AMBIGUOUS_OWNER_TERMS = ("human gate","human scope gate","human research pass","human pass","human review","human validation","human decision")
THIRD_PARTY_RESEARCH_ACTOR = r"(?:participants?|respondents?|speakers?|listeners?|people|humans?|experts?|subjects?|interviewees?|(?:human\s+)?annotators?|human\s+labelers?|(?:human\s+)?raters?|(?:human\s+)?coders?|(?:human\s+)?reviewers?|crowd(?:\s+|-)workers?|crowdworkers?|(?:human\s+)?panelists?|external\s+experts?|native[- ]speakers?)"
OWNER_OR_USER_CONTROL_ACTOR = r"(?:owner(?:/k0)?|project\s+owner|the\s+user|user)"
HUMAN_TARGET = THIRD_PARTY_RESEARCH_ACTOR
RESEARCH_LABOR_NOUN = r"(?:human\s+annotation|human\s+rating|human\s+coding|human\s+review|crowd[- ]?sourcing|crowd\s+sourcing|crowd\s+labor)"
RESEARCH_WORK_VERB = r"(?:annotate|label|rate|score|code|review|classify|assess|evaluate)"
ASSIGNMENT_VERB = r"(?:assign|hire|recruit|use|employ|contract|have)"
ACTIVE_ACTION_PATTERNS = (
    rf"\brecruit(?:ing|ed)?\b.{{0,60}}?\b{HUMAN_TARGET}\b",
    r"\b(?:participant|human|native[- ]speaker|speaker|respondent|expert)\s+recruitment\b",
    rf"\brecruitment\s+(?:of|for)\s+.{{0,40}}\b{HUMAN_TARGET}\b",
    rf"\bsurvey\b.{{0,50}}\b{HUMAN_TARGET}\b",
    rf"\bsurvey(?:ing|ed)\b.{{0,50}}\b{HUMAN_TARGET}\b",
    rf"\binterview\b.{{0,50}}\b{HUMAN_TARGET}\b",
    rf"\binterviewing\b.{{0,50}}\b{HUMAN_TARGET}\b",
    r"\b(?:conduct|run|deploy|administer|launch|start|resume|execute|perform)\b.{0,45}\b(?:survey|questionnaire|poll|interviews?|focus[ -]?groups?)\b",
    r"\b(?:survey|questionnaire|interview|focus[ -]?group)\s+(?:deployment|administration|collection)\b",
    r"\b(?:participant|respondent|human)\s+(?:data\s+)?collection\b",
    r"\b(?:collect|gather|solicit|obtain)\b.{0,45}\b(?:human\s+data|human\s+evidence|responses?|participant\s+data|respondent\s+data|ratings?)\b",
    rf"\b(?:ask|contact|consult)\b.{{0,35}}\b{HUMAN_TARGET}\b",
    r"\b(?:send|give|administer)\b.{0,30}\b(?:survey|questionnaire)\b.{0,30}\b(?:participants?|respondents?|users?|speakers?|humans?)\b",
    rf"\bhave\s+{HUMAN_TARGET}\s+(?:check|review|rate|score|validate|annotate|label|code|classify|assess|evaluate)\b",
    r"\b(?:external\s+reviewers?|human\s+reviewers?|experts?|native[- ]speakers?|participants?|respondents?)\b.{0,30}\b(?:review|validate|rate|score|annotate|label|check|code|classify|assess|evaluate)\b",
    r"\b(?:review|validation|rating|annotation|assessment|evaluation|coding)\s+by\s+(?:external\s+)?(?:experts?|humans?|reviewers?|raters?|annotators?|coders?|speakers?|participants?)\b",
    r"\bget\s+(?:community|expert|speaker|listener|participant|respondent)\s+(?:feedback|review|validation|ratings?)\b",
    rf"\btest\b.{{0,35}}\bwith\s+{HUMAN_TARGET}\b",
    rf"\bfind\s+.{{0,30}}\b{HUMAN_TARGET}\b",
    r"\b(?:focus[ -]?group|user[ -]?testing|human[ -]?in[ -]?the[- ]loop|collection[- ]surface)\b",
    r"\b(?:new|project[- ]generated)\s+(?:human|participant|respondent|speaker|user).{0,35}\b(?:survey|interviews?|data|responses?|ratings?|evidence)\b",
    r"\b(?:route|send|hand\s+off)\b.{0,30}\b(?:to\s+)?(?:humans?|participants?|external\s+reviewers?|experts?)\b",
    rf"\b{ASSIGNMENT_VERB}\b.{{0,60}}\b{THIRD_PARTY_RESEARCH_ACTOR}\b.{{0,50}}\b{RESEARCH_WORK_VERB}\b",
    rf"\b{ASSIGNMENT_VERB}\b.{{0,60}}\b{THIRD_PARTY_RESEARCH_ACTOR}\b",
    rf"\b{ASSIGNMENT_VERB}\b.{{0,60}}\b{RESEARCH_LABOR_NOUN}\b",
    rf"\b(?:requires?|mandates?|needs?)\b.{{0,40}}\b{RESEARCH_LABOR_NOUN}\b",
    rf"\b{RESEARCH_LABOR_NOUN}\b.{{0,30}}\b(?:remains?|is|are)\s+(?:strictly\s+)?mandatory\b",
    r"\bowner(?:/k0)?\b.{0,60}\b(?:manually\s+)?collect\b.{0,40}\b(?:urls?|sources?|data|responses?)\b",
    r"\bowner(?:/k0)?\b.{0,60}\bsearch\b.{0,40}\b(?:sources?|web|literature)\b",
    r"\bowner(?:/k0)?\b.{0,60}\b(?:annotate|code|rate)\b.{0,40}\b(?:dataset|items?|responses?|samples?)\b",
)
HUMAN_ACTION_MENTION_PATTERNS = ACTIVE_ACTION_PATTERNS + (
    r"\bhuman\s+recruitment\b",
    r"\bparticipant\s+recruitment\b",
    r"\bthird[- ]party\s+human\s+research\b",
    rf"\b{RESEARCH_LABOR_NOUN}\b",
    r"\bhuman\s+approval\b",
)
STATIC_SOURCE_PATTERNS = (r"\bpublished\s+(?:study|paper|survey|interviews?|dataset|corpus)\b",r"\barchived\b.{0,25}\b(?:interviews?|survey|responses?|dataset|corpus|human\s+data)\b",r"\brecorded\s+speech\s+corpus\b",r"\bexisting\s+(?:survey|human\s+annotation|expert\s+judgment|dataset|interviews?|responses?)\b",r"\bexternally\s+conducted\s+survey\b",r"\bpublic\s+dataset\b",r"\bpre[- ]?existing\b",r"\bexternal[_ -]preexisting[_ -]human[_ -]data\b",r"\bhistorical\s+corpus\b")
HISTORICAL_CUES = ("historical","legacy","archived","preserved lineage","retired compatibility","before retirement")
PROHIBITION_CUES = ("prohibited","forbidden","must not","do not","don't","never","cannot","can't","not allowed","invalid","default deny","default-deny","there is no","no third-party","must be zero","are all zero","requirements are all zero")
OWNER_CUES = ("owner/k0","owner ","owner_","owner chooses","owner accepts","owner rejects","owner adjudicat")
OWNER_DECISION_CUES = ("choose","chooses","accept","reject","defer","decision","adjudicat","gate")
SIMULATED_HUMAN_OVERCLAIM = (r"\b(?:llm|model|simulat(?:ed|ion)|synthetic)\b.{0,80}\bhuman responses?\b",r"\bhuman responses?\b.{0,80}\b(?:llm|model|simulat(?:ed|ion)|synthetic)\b")
FATAL_FINDINGS = {"ACTIVE_DEPENDENCY","PROXY_OVERCLAIM","AMBIGUOUS_HUMAN_GATE_TERMINOLOGY"}

@dataclass(frozen=True)
class Finding:
    classification: str
    message: str

def _norm(text: str) -> str: return re.sub(r"\s+"," ",text.lower()).strip()
POLICY_HEADING = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?(?:prohibited|forbidden|default[- ]deny(?:\s+controls?)?)(?:\*\*)?\s*:\s*(.*)$", re.I)
CONTRAST = re.compile(r"\s*(?:,\s*|\b)(?:but|however|yet|nevertheless|nonetheless)\b[,\s]*", re.I)
BULLET = re.compile(r"^\s*[-*]\s+(\S.*)$")
ATX_HEADING = re.compile(r"^ {0,3}#{1,6}(?=\s|$)")

@dataclass(frozen=True)
class ActionDisposition:
    action: str
    proposition_id: int
    source_item_index: int
    source_item_text: str
    source_item_start: int
    source_item_end: int
    action_start: int
    action_end: int
    semantic_action_index: int
    semantic_action_start: int
    semantic_action_end: int
    governor_scope_id: int | None
    governor: str | None
    disposition: str
    reason: str

@dataclass(frozen=True)
class SourceActionItem:
    source_item_index: int
    source_item_text: str
    source_item_start: int
    source_item_end: int

@dataclass(frozen=True)
class ActionOccurrence:
    source_item_index: int
    source_item_text: str
    source_item_start: int
    source_item_end: int
    semantic_action_index: int
    action: str
    action_start: int
    action_end: int
    lexical_matches: tuple[re.Match[str], ...]
    governor_scope_id: int | None = None

@dataclass(frozen=True)
class GovernorScope:
    scope_id: int
    governor_kind: str
    governor_text: str
    governor_start: int
    governor_end: int
    governed_start: int
    governed_end: int

def _policy_units(text: str) -> list[str]:
    """Assemble bounded Markdown structures without treating soft wraps as scope."""
    lines = str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    units: list[str] = []
    prose: list[str] = []

    def flush_prose() -> None:
        if prose:
            units.append(" ".join(part.strip() for part in prose))
            prose.clear()

    def bullet_item(start: int) -> tuple[str, int]:
        match = BULLET.match(lines[start])
        parts = [match.group(1)] if match else []
        cursor = start + 1
        while cursor < len(lines) and lines[cursor].strip() and not BULLET.match(lines[cursor]):
            if not lines[cursor][:1].isspace():
                break
            parts.append(lines[cursor].strip())
            cursor += 1
        return " ".join(parts), cursor

    i = 0
    while i < len(lines):
        if not lines[i].strip():
            flush_prose()
            i += 1
            continue
        if ATX_HEADING.match(lines[i]):
            flush_prose()
            i += 1
            continue
        heading = POLICY_HEADING.match(lines[i])
        if heading and not heading.group(1).strip():
            flush_prose()
            items: list[str] = []
            j = i + 1
            while j < len(lines) and not lines[j].strip(): j += 1
            while j < len(lines) and BULLET.match(lines[j]):
                item, j = bullet_item(j)
                items.append(item)
            if items:
                units.append(f"{lines[i].strip()} " + ", ".join(items))
                i = j
                continue
            units.append(lines[i].strip())
            i += 1
            continue
        if BULLET.match(lines[i]):
            flush_prose()
            item, i = bullet_item(i)
            units.append(f"- {item}")
            continue
        prose.append(lines[i])
        i += 1
    flush_prose()
    return units

def _propositions(unit: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+|\s*;\s*", unit) if p.strip() for p in CONTRAST.split(p) if p.strip()]

AUTHORITY_DENIAL = re.compile(
    r"\b(?:never|does not|do not|cannot|can't)\s+"
    r"(?:create|creates|grant|grants|provide|provides|confer|confers)\s+"
    r"(?:any\s+|the\s+)?(?:authority|permission)\s+to\b",
    re.I,
)
ITEM_SEPARATOR = re.compile(r"\s*(?:,\s*(?:(?:and|or)\b\s*)?|\b(?:and|or)\b\s+)", re.I)
LEADING_GOVERNOR = re.compile(r"^(?:[-*]\s*)?(?:never|do not|does not|must not|should not|may not|cannot|can't)\b\s*", re.I)
NO_TRANSITION_GOVERNOR = re.compile(r"^(?:there (?:is no ordinary transition|are no ordinary transitions|is no authority|is no permission) to|no (?:ordinary transition|authority|permission) to)\b\s*", re.I)
BARE_HUMAN_ACTION_MENTION = re.compile(
    r"^(?:surveys?|interviews?|focus[ -]?groups?|(?:external\s+)?reviewer\s+approval|"
    r"expert\s+panels?|human\s+validation)\.?$",
    re.I,
)

def _source_action_items(proposition: str) -> list[SourceActionItem]:
    items: list[SourceActionItem] = []
    start = 0
    for separator in ITEM_SEPARATOR.finditer(proposition):
        raw_start, raw_end = start, separator.start()
        start = separator.end()
        left = len(proposition[raw_start:raw_end]) - len(proposition[raw_start:raw_end].lstrip())
        right = len(proposition[raw_start:raw_end].rstrip())
        if right > left:
            item_start, item_end = raw_start + left, raw_start + right
            items.append(SourceActionItem(len(items), proposition[item_start:item_end], item_start, item_end))
    raw = proposition[start:]
    left, right = len(raw) - len(raw.lstrip()), len(raw.rstrip())
    if right > left:
        item_start, item_end = start + left, start + right
        items.append(SourceActionItem(len(items), proposition[item_start:item_end], item_start, item_end))
    return items

def _item_action_occurrences(item: SourceActionItem) -> list[ActionOccurrence]:
    """Group overlapping raw matches into deterministic semantic occurrences."""
    raw_matches: list[re.Match[str]] = []
    seen: set[tuple[int, int]] = set()
    for pattern in ACTIVE_ACTION_PATTERNS:
        for match in re.finditer(pattern, item.source_item_text, flags=re.I | re.S):
            key = (match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            raw_matches.append(match)
    raw_matches.sort(key=lambda match: (match.start(), match.end()))
    groups: list[list[re.Match[str]]] = []
    for match in raw_matches:
        if groups and match.start() == groups[-1][0].start():
            groups[-1].append(match)
        else:
            groups.append([match])
    occurrences: list[ActionOccurrence] = []
    for semantic_action_index, matches in enumerate(groups):
        if semantic_action_index + 1 < len(groups):
            next_start = groups[semantic_action_index + 1][0].start()
            matches = [match for match in matches if match.end() <= next_start]
        if not matches:
            continue
        start = min(match.start() for match in matches)
        end = max(match.end() for match in matches)
        occurrences.append(ActionOccurrence(
            item.source_item_index, item.source_item_text, item.source_item_start, item.source_item_end,
            semantic_action_index, item.source_item_text[start:end], item.source_item_start + start,
            item.source_item_start + end, tuple(matches),
        ))
    return occurrences

def _governor_anchor(item: SourceActionItem) -> tuple[str, re.Match[str]] | None:
    candidates: list[tuple[str, re.Match[str]]] = []
    for kind, pattern in (("leading_negation", LEADING_GOVERNOR), ("no_transition", NO_TRANSITION_GOVERNOR)):
        match = pattern.search(item.source_item_text)
        if match:
            candidates.append((kind, match))
    heading = POLICY_HEADING.match(item.source_item_text)
    if heading:
        anchor_end = heading.end() - len(heading.group(1))
        candidates.append(("policy_heading", re.match(rf"^.{{{anchor_end}}}", item.source_item_text, re.S)))
    authority = AUTHORITY_DENIAL.search(item.source_item_text)
    if authority:
        candidates.append(("authority_denial", authority))
    return min(candidates, key=lambda candidate: candidate[1].start()) if candidates else None

def _resolve_governor_scopes(proposition: str) -> tuple[list[SourceActionItem], list[ActionOccurrence], list[GovernorScope], dict[tuple[int, int], int]]:
    """Resolve finite, contiguous scope before assigning lexical dispositions."""
    items = _source_action_items(proposition)
    by_item = {item.source_item_index: _item_action_occurrences(item) for item in items}
    scopes: list[GovernorScope] = []
    membership: dict[tuple[int, int], int] = {}
    active_scope: int | None = None
    for item in items:
        occurrences = by_item[item.source_item_index]
        anchor = _governor_anchor(item)
        if anchor is not None:
            kind, match = anchor
            governed_start = item.source_item_start + match.end()
            governed_occurrences = [occurrence for occurrence in occurrences if occurrence.action_start >= governed_start]
            active_scope = None
            if governed_occurrences:
                scope_id = len(scopes)
                governed_occurrence = governed_occurrences[0]
                scopes.append(GovernorScope(scope_id, kind, match.group(0).strip(),
                    item.source_item_start + match.start(), item.source_item_start + match.end(),
                    governed_start, governed_occurrence.action_end))
                membership[(item.source_item_index, governed_occurrence.semantic_action_index)] = scope_id
                active_scope = scope_id if len(governed_occurrences) == 1 else None
            continue
        if active_scope is not None and occurrences and occurrences[0].action_start == item.source_item_start:
            occurrence = occurrences[0]
            membership[(item.source_item_index, occurrence.semantic_action_index)] = active_scope
            scope = scopes[active_scope]
            scopes[active_scope] = GovernorScope(scope.scope_id, scope.governor_kind, scope.governor_text,
                scope.governor_start, scope.governor_end, scope.governed_start, occurrence.action_end)
            if len(occurrences) > 1:
                active_scope = None
        elif active_scope is not None and BARE_HUMAN_ACTION_MENTION.fullmatch(item.source_item_text):
            # Some bounded list nouns are governed human-action mentions but
            # deliberately do not create an ACTIVE action disposition alone.
            continue
        else:
            active_scope = None
    occurrences = [occurrence for item in items for occurrence in by_item[item.source_item_index]]
    occurrences = [replace(occurrence, governor_scope_id=membership.get(
        (occurrence.source_item_index, occurrence.semantic_action_index))) for occurrence in occurrences]
    return items, occurrences, scopes, membership

def _shared_governor(proposition: str) -> str | None:
    """Compatibility signal only; disposition authority lives in GovernorScope."""
    items, _, scopes, _ = _resolve_governor_scopes(proposition)
    if scopes:
        return scopes[0].governor_text
    for item in items:
        anchor = _governor_anchor(item)
        if anchor:
            return anchor[1].group(0).strip()
    t = _norm(proposition)
    if re.fullmatch(r"(?:no default role may be instantiated as an arbitrary external person\.\s*)?generic\s+`?reviewer`?,.*\bare invalid default research engine roles\.?", t): return "terminal invalid-role predicate"
    if re.fullmatch(r"migration passes only when .+\b(?:dependencies|paths|gates) must be zero\.?", t): return "terminal zero predicate"
    return None

def _local_non_active(proposition: str, match: re.Match[str]) -> str | None:
    before = proposition[:match.start()].lower()[-100:]
    after = proposition[match.end():].lower()[:100]
    matched = match.group(0).lower()
    if re.search(r"\b(?:never|do\s+not|does\s+not|must\s+not|should\s+not|may\s+not|cannot|can't)\b", matched): return "local negation"
    if re.search(r"\b(?:never|does\s+not|do\s+not|cannot|can't)\b[^,;]{0,70}$", before): return "local negation"
    if re.search(r"\b(?:is|are)\s+(?:strictly\s+)?(?:prohibited|forbidden|not allowed|invalid)\b", after): return "local prohibition predicate"
    if re.search(r"\b(?:cancel|retire)\b", before) and re.search(r"\bwithout\s+executing\b", after): return "retired without execution"
    if re.search(r"\balready[- ]collected\b", before) and re.search(r"\bhistorical\b", before + matched + after): return "historical lineage"
    return None

def _action_dispositions(proposition: str, proposition_id: int) -> list[ActionDisposition]:
    t = _norm(proposition)
    if re.fullmatch(r"(?:no default role may be instantiated as an arbitrary external person\.\s*)?generic\s+`?reviewer`?,.*\bare invalid default research engine roles\.?", t) or re.fullmatch(r"migration passes only when .+\b(?:dependencies|paths|gates) must be zero\.?", t):
        return []
    _, occurrences, scopes, membership = _resolve_governor_scopes(proposition)
    decisions = []
    for occurrence in occurrences:
        occurrence_key = (occurrence.source_item_index, occurrence.semantic_action_index)
        scope_id = membership.get(occurrence_key)
        scope = scopes[scope_id] if scope_id is not None else None
        item = SourceActionItem(occurrence.source_item_index, occurrence.source_item_text,
            occurrence.source_item_start, occurrence.source_item_end)
        for match in occurrence.lexical_matches:
            local = None if _governor_anchor(item) else _local_non_active(occurrence.source_item_text, match)
            reason = scope.governor_text if scope else local
            decisions.append(ActionDisposition(
                match.group(0), proposition_id, occurrence.source_item_index, occurrence.source_item_text,
                occurrence.source_item_start, occurrence.source_item_end,
                occurrence.source_item_start + match.start(), occurrence.source_item_start + match.end(),
                occurrence.semantic_action_index, occurrence.action_start, occurrence.action_end,
                scope_id, scope.governor_text if scope else None, "NON_ACTIVE" if reason else "ACTIVE",
                reason or "no supported non-active scope",
            ))
    return decisions

def _clause_has_static_source(clause: str) -> bool: return any(re.search(p,clause,flags=re.I) for p in STATIC_SOURCE_PATTERNS)
def _clause_has_human_prohibition(clause: str) -> bool:
    t=_norm(clause)
    if re.search(r"^[-*]\s+require human approval for every trivial change", t): return True
    if not any(c in t for c in PROHIBITION_CUES): return False
    if re.search(r"\b(?:must|should|shall)\s+be\s+(?:zero|absent|false)\b",t): return True
    if re.search(r"\b(?:is|are)\s+(?:strictly\s+)?invalid\b.{0,60}\b(?:roles?|dependencies?|paths?|gates?)\b",t): return True
    return bool(re.search(r"\b(?:human recruitment|recruitment|human research|third[- ]party human research|participant collection|human annotation|human rating|human coding|human review|crowd[- ]?sourcing|crowd sourcing|crowd labor|human approval)\s+(?:is|are)\s+(?:strictly\s+)?(?:prohibited|forbidden|not allowed|invalid)\b",t))

def classify_text(text: str) -> list[Finding]:
    findings=[]
    clauses = [p for unit in _policy_units(text) for p in _propositions(unit)]
    for proposition_id, clause in enumerate(clauses):
        t=_norm(clause)
        for p in SIMULATED_HUMAN_OVERCLAIM:
            if re.search(p,clause,flags=re.I|re.S): findings.append(Finding("PROXY_OVERCLAIM","machine/simulated output is labeled as human responses"))
        if _clause_has_static_source(clause): findings.append(Finding("STATIC_EXTERNAL_SOURCE","pre-existing human-derived evidence"))
        dispositions = _action_dispositions(clause, proposition_id)
        governed_mention = _shared_governor(clause) is not None and any(re.search(pattern, clause, flags=re.I | re.S) for pattern in HUMAN_ACTION_MENTION_PATTERNS)
        prohibited_action=any(d.disposition == "NON_ACTIVE" for d in dispositions) or governed_mention
        active_action=any(d.disposition == "ACTIVE" for d in dispositions)
        if prohibited_action or _clause_has_human_prohibition(clause): findings.append(Finding("EXPLICIT_PROHIBITION","human action is explicitly negated/prohibited"))
        if active_action: findings.append(Finding("ACTIVE_DEPENDENCY",f"active prohibited human research action: {clause[:180]}"))
        historical_only=any(c in t for c in HISTORICAL_CUES) and not active_action and not re.search(r"\b(?:run|execute|resume|deploy|start|recruit|collect|require|mandatory)\b",t)
        if historical_only and not _clause_has_static_source(clause): findings.append(Finding("HISTORICAL_REFERENCE","historical/legacy reference"))
        clause_prohibits=prohibited_action or _clause_has_human_prohibition(clause) or _shared_governor(clause) is not None
        for term in AMBIGUOUS_OWNER_TERMS:
            if term in t and not clause_prohibits and not historical_only and not _clause_has_static_source(clause): findings.append(Finding("AMBIGUOUS_HUMAN_GATE_TERMINOLOGY",f"generic authority term: {term}"))
        approval_required = bool(re.search(r"\b(?:requires?|mandates?|needs?)\s+(?:external\s+)?human\s+approval\b|\b(?:external\s+)?human\s+approval\b.{0,40}\b(?:is|remains|must\s+be)\s+(?:strictly\s+)?(?:required|mandatory|needed)\b",clause,flags=re.I))
        if approval_required and not clause_prohibits and not historical_only and not _clause_has_static_source(clause): findings.append(Finding("AMBIGUOUS_HUMAN_GATE_TERMINOLOGY","generic authority term: human approval"))
        if not active_action and any(c in t for c in OWNER_CUES) and any(c in t for c in OWNER_DECISION_CUES): findings.append(Finding("OWNER_AUTHORITY","explicit Owner/K0 project authority"))
    unique=[]; seen=set()
    for f in findings:
        k=(f.classification,f.message)
        if k not in seen: seen.add(k); unique.append(f)
    return unique

def _require_fields(obj: dict[str,Any],fields: Iterable[str])->list[str]: return [f"missing required field: {n}" for n in sorted(fields) if n not in obj]
def _reject_unknown_fields(obj: dict[str,Any],allowed:set[str])->list[str]: return [f"undeclared field not allowed: {n}" for n in sorted(set(obj)-allowed)]
def _validate_default_flags(obj:dict[str,Any],false_fields:set[str])->list[str]:
    errors=_require_fields(obj,DEFAULT_REQUIRED_TRUE|false_fields)
    for n in DEFAULT_REQUIRED_TRUE:
        if obj.get(n) is not True: errors.append(f"{n} must be true")
    for n in false_fields:
        if obj.get(n) is not False: errors.append(f"{n} must be false")
    return errors

def _iter_string_leaves(value:Any,path:str="$ ")->Iterator[tuple[str,str]]:
    if isinstance(value,str): yield path,value
    elif isinstance(value,dict):
        for k,v in value.items(): yield from _iter_string_leaves(v,f"{path}.{k}")
    elif isinstance(value,(list,tuple,set)):
        for i,v in enumerate(value): yield from _iter_string_leaves(v,f"{path}[{i}]")
def _semantic_errors(value:Any,field_name:str)->list[str]:
    errors=[]
    for path,text in _iter_string_leaves(value,field_name):
        for f in classify_text(text):
            if f.classification in FATAL_FINDINGS: errors.append(f"{path}: {f.classification}: {f.message}")
    return errors

QUESTION_SEMANTIC_FIELDS={"QUESTION","TARGET_CONSTRUCT","AVAILABLE_MACHINE_METHODS","AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE","EXPECTED_LIMITATION","OWNER_DECISION_COMPONENT"}
WORK_PACKAGE_SEMANTIC_FIELDS={"EXECUTION_SURFACE","SOURCE_ACCESS_METHOD","COMPUTATION_METHOD","VERIFICATION_METHOD","LIMITATIONS","PROHIBITED_OVERCLAIMS","OWNER_GATE_IF_ANY"}
ALLOWED_EXECUTOR_ROLES={"AI_R_MASTER","AI_EVIDENCE_EXTRACTOR","AI_SYNTHESIS_AGENT","AI_R_REPAIR","AI_ADVERSARIAL_VALIDATOR","AI_RESEARCH_RELEASE_CONTROLLER"}

def validate_question(obj:dict[str,Any])->list[str]:
    errors=_require_fields(obj,QUESTION_REQUIRED_FIELDS)+_reject_unknown_fields(obj,QUESTION_REQUIRED_FIELDS)+_validate_default_flags(obj,DEFAULT_REQUIRED_FALSE)
    if not obj.get("AVAILABLE_MACHINE_METHODS"): errors.append("AVAILABLE_MACHINE_METHODS must be non-empty")
    if obj.get("ADMISSION_STATUS")!="ADMITTED_MACHINE_RESEARCH": errors.append("ADMISSION_STATUS must be ADMITTED_MACHINE_RESEARCH for default execution")
    for n in QUESTION_SEMANTIC_FIELDS: errors+=_semantic_errors(obj.get(n),n)
    return sorted(set(errors))
def validate_work_package(obj:dict[str,Any])->list[str]:
    errors=_require_fields(obj,WORK_PACKAGE_REQUIRED_FIELDS)+_reject_unknown_fields(obj,WORK_PACKAGE_REQUIRED_FIELDS)+_validate_default_flags(obj,WP_REQUIRED_FALSE)
    if str(obj.get("NAMESPACE","")).startswith("human-research/"): errors.append("default Research Engine cannot admit human-research namespace")
    if obj.get("EXECUTOR_ROLE") not in ALLOWED_EXECUTOR_ROLES: errors.append("EXECUTOR_ROLE must be an allowed AI Research Engine role")
    if obj.get("VERIFIER_ROLE")!="AI_R_VERIFIER": errors.append("VERIFIER_ROLE must be AI_R_VERIFIER")
    gate=obj.get("OWNER_GATE_IF_ANY")
    if gate is not None and not re.fullmatch(r"OWNER_[A-Z0-9_]+",str(gate)): errors.append("OWNER_GATE_IF_ANY must be null or explicit OWNER_* authority term")
    for n in WORK_PACKAGE_SEMANTIC_FIELDS: errors+=_semantic_errors(obj.get(n),n)
    return sorted(set(errors))
def admit_question(obj):
    errors=validate_question(obj); return {"ADMISSION_STATUS":"ADMITTED_MACHINE_RESEARCH" if not errors else "REJECTED_DEFAULT_RESEARCH_ARCHITECTURE","ERROR_CODE":None if not errors else "METHOD_NOT_MACHINE_EXECUTABLE","REQUIRE_MACHINE_REDESIGN":bool(errors),"ERRORS":errors}
def admit_work_package(obj):
    errors=validate_work_package(obj); return {"ADMISSION_STATUS":"ADMITTED_MACHINE_RESEARCH" if not errors else "REJECT_METHOD","ERROR_CODE":None if not errors else "METHOD_NOT_MACHINE_EXECUTABLE","REQUIRE_MACHINE_REDESIGN":bool(errors),"ERRORS":errors}
def verify_machine_invariant(obj):
    errors=validate_work_package(obj); findings=[]
    for n in WORK_PACKAGE_SEMANTIC_FIELDS:
        for _,text in _iter_string_leaves(obj.get(n),n): findings.extend(classify_text(text))
    active=sum(f.classification=="ACTIVE_DEPENDENCY" for f in findings); ambiguous=sum(f.classification=="AMBIGUOUS_HUMAN_GATE_TERMINOLOGY" for f in findings)
    external_review=int(obj.get("REQUIRES_EXTERNAL_HUMAN_REVIEW") is not False or obj.get("REQUIRES_EXTERNAL_REVIEWER") is not False); owner_labor=int(obj.get("REQUIRES_OWNER_MANUAL_RESEARCH") is not False); human_collection=int(obj.get("REQUIRES_HUMAN_DATA_COLLECTION") is not False or obj.get("REQUIRES_NEW_HUMAN_DATA") is not False); third_party=int(obj.get("REQUIRES_THIRD_PARTY_HUMAN") is not False)+active
    return {"STATUS":"PASS" if not errors else "FAIL","MACHINE_EXECUTABLE":"PASS" if not errors else "FAIL","THIRD_PARTY_HUMAN_DEPENDENCY":third_party,"OWNER_MANUAL_RESEARCH_DEPENDENCY":owner_labor,"EXTERNAL_HUMAN_REVIEW_DEPENDENCY":external_review,"HUMAN_COLLECTION_PATH":human_collection,"AMBIGUOUS_HUMAN_GATE_TERMINOLOGY":ambiguous,"ERRORS":errors}

HUMAN_AUTH_FIELDS={"AUTHORIZATION_ID","OWNER_DECISION_RECORD_REF","OWNER_AUTHORITY_ROLE","PROJECT_ID","QUESTION_ID","SCOPE","NAMESPACE","NON_TRANSITIVE","CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE","DEFAULT_RESEARCH_MODE_UNCHANGED"}
OWNER_AUTH_DECISION_KIND="CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"; OWNER_AUTH_SELECTED_OPTION="AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM"
OWNER_DECISION_REQUIRED={"artifact_type","artifact_id","produced_by_role","assignment_id","input_state_ref","status","provenance","related_artifacts","question_ref","options_presented","selected_option","owner_constraints","consequences_acknowledged","authority_role","decision_kind","project_id","authorized_question_id","authorized_scope","authorized_namespace","authorization_id","non_transitive","default_research_mode_unchanged"}
OwnerDecisionResolver=Callable[[str],dict[str,Any]|None]

def _validate_durable_owner_record(record:dict[str,Any],auth:dict[str,Any])->list[str]:
    errors=_require_fields(record,OWNER_DECISION_REQUIRED)
    checks=((record.get("artifact_type")=="OWNER_DECISION_RECORD","referenced record is not OWNER_DECISION_RECORD"),(record.get("artifact_id")==auth.get("OWNER_DECISION_RECORD_REF"),"OWNER_DECISION_RECORD_REF does not match record identity"),(record.get("produced_by_role")=="owner-interface","Owner decision record is not produced by owner-interface"),(record.get("status")=="RECORDED","Owner decision record is not durable RECORDED state"),(record.get("authority_role")=="OWNER_K0","Owner decision record authority is not OWNER_K0"),(record.get("decision_kind")==OWNER_AUTH_DECISION_KIND,"Owner decision does not authorize separate human research"),(record.get("selected_option")==OWNER_AUTH_SELECTED_OPTION,"Owner selected option does not authorize separate human research"),(record.get("project_id")==auth.get("PROJECT_ID"),"Owner decision project differs from authorization"),(record.get("authorized_question_id")==auth.get("QUESTION_ID"),"Owner decision question differs from authorization"),(record.get("authorized_scope")==auth.get("SCOPE"),"Owner decision scope does not exactly bound authorization"),(record.get("authorized_namespace")==auth.get("NAMESPACE"),"Owner decision namespace differs from authorization"),(record.get("authorization_id")==auth.get("AUTHORIZATION_ID"),"Owner decision authorization identity differs"),(record.get("non_transitive") is True and auth.get("NON_TRANSITIVE") is True,"human research authorization must be non-transitive"),(record.get("default_research_mode_unchanged") is True and auth.get("DEFAULT_RESEARCH_MODE_UNCHANGED") is True,"authorization must not modify default Research mode"))
    for ok,msg in checks:
        if not ok: errors.append(msg)
    for n in ("assignment_id","input_state_ref","question_ref"):
        if not isinstance(record.get(n),str) or not record.get(n): errors.append(f"durable Owner decision requires non-empty {n}")
    for n in ("provenance","related_artifacts","options_presented"):
        v=record.get(n)
        if not isinstance(v,list) or not v or not all(isinstance(x,str) and x for x in v): errors.append(f"durable Owner decision requires non-empty string list {n}")
    for n in ("owner_constraints","consequences_acknowledged"):
        v=record.get(n)
        if not isinstance(v,list) or not all(isinstance(x,str) for x in v): errors.append(f"durable Owner decision requires string list {n}")
    if record.get("selected_option") not in (record.get("options_presented") or []): errors.append("Owner selected option must be present in options_presented")
    if not any(re.search(r"(?:owner|k0)",x,flags=re.I) for x in (record.get("provenance") or []) if isinstance(x,str)): errors.append("Owner decision provenance must contain an Owner/K0 authority reference")
    return errors

def validate_human_research_authorization(auth:dict[str,Any],owner_decision_resolver:OwnerDecisionResolver|None=None)->list[str]:
    errors=_require_fields(auth,HUMAN_AUTH_FIELDS)+_reject_unknown_fields(auth,HUMAN_AUTH_FIELDS)
    for n in {"NON_TRANSITIVE","CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE","DEFAULT_RESEARCH_MODE_UNCHANGED"}:
        if auth.get(n) is not True: errors.append(f"{n} must be true")
    if auth.get("OWNER_AUTHORITY_ROLE")!="OWNER_K0": errors.append("OWNER_AUTHORITY_ROLE must be OWNER_K0")
    if not str(auth.get("NAMESPACE","")).startswith("human-research/"): errors.append("human research authorization requires human-research/ namespace")
    for n in ("AUTHORIZATION_ID","OWNER_DECISION_RECORD_REF","PROJECT_ID","QUESTION_ID","SCOPE"):
        if not auth.get(n): errors.append(f"{n} must be non-empty")
    if owner_decision_resolver is None: errors.append("OWNER_DECISION_RECORD_REF requires governed durable Owner-decision resolver"); return sorted(set(errors))
    ref=str(auth.get("OWNER_DECISION_RECORD_REF","") )
    try: record=owner_decision_resolver(ref)
    except Exception as exc: errors.append(f"Owner decision resolver failed closed: {type(exc).__name__}"); return sorted(set(errors))
    if record is None: errors.append("OWNER_DECISION_RECORD_REF does not resolve to a durable Owner decision record"); return sorted(set(errors))
    if not isinstance(record,dict): errors.append("governed Owner decision resolver returned invalid record type"); return sorted(set(errors))
    errors+=_validate_durable_owner_record(record,auth); return sorted(set(errors))
def validate_separate_human_work_package(obj:dict[str,Any],auth:dict[str,Any],owner_decision_resolver:OwnerDecisionResolver|None=None)->list[str]:
    errors=validate_human_research_authorization(auth,owner_decision_resolver)
    if errors: return errors
    if obj.get("NAMESPACE")!=auth.get("NAMESPACE"): errors.append("work package namespace differs from OWNER authorization")
    if obj.get("QUESTION_ID")!=auth.get("QUESTION_ID"): errors.append("work package question differs from OWNER authorization")
    if obj.get("PROJECT_ID")!=auth.get("PROJECT_ID"): errors.append("work package project differs from OWNER authorization")
    return sorted(set(errors))

SOURCE_FIELDS={"SOURCE_ID","PROVENANCE_CLASS","ORIGIN","HUMAN_ORIGIN","PROJECT_GENERATION_PROHIBITED","DESCRIPTION","SOURCE_URI"}; SOURCE_REQUIRED_FIELDS=SOURCE_FIELDS-{"SOURCE_URI"}
SOURCE_CLASSES={"PRIMARY_EXTERNAL_DATA","PUBLIC_DATASET","CORPUS","SCHOLARLY_ANALYSIS","DICTIONARY_REFERENCE","OFFICIAL_REFERENCE","COMMUNITY_ARCHIVE","EXTERNAL_PREEXISTING_HUMAN_DATA","SOFTWARE_DATASET","PROXY","OTHER","LEGACY_HUMAN_TEST"}; SOURCE_ORIGINS={"EXTERNAL_PREEXISTING","PROJECT_MACHINE_GENERATED","LEGACY_PRESERVED","UNKNOWN"}; HUMAN_ORIGIN_TEXT=re.compile(r"\b(?:human|participant|respondent|speaker|listener|interview|survey|questionnaire|human-derived)\b",re.I)
def validate_source(obj:dict[str,Any])->list[str]:
    errors=_require_fields(obj,SOURCE_REQUIRED_FIELDS)+_reject_unknown_fields(obj,SOURCE_FIELDS); provenance=obj.get("PROVENANCE_CLASS"); origin=obj.get("ORIGIN"); human_origin=obj.get("HUMAN_ORIGIN"); prohibited=obj.get("PROJECT_GENERATION_PROHIBITED"); description=obj.get("DESCRIPTION")
    if provenance not in SOURCE_CLASSES: errors.append("PROVENANCE_CLASS is not recognized")
    if origin not in SOURCE_ORIGINS: errors.append("ORIGIN is not recognized")
    if not isinstance(human_origin,bool): errors.append("HUMAN_ORIGIN must be boolean")
    if not isinstance(prohibited,bool): errors.append("PROJECT_GENERATION_PROHIBITED must be boolean")
    if not isinstance(description,str) or not description: errors.append("DESCRIPTION must be a non-empty string")
    if provenance=="LEGACY_HUMAN_TEST":
        if prohibited is not True: errors.append("LEGACY_HUMAN_TEST requires PROJECT_GENERATION_PROHIBITED=true")
        if human_origin is not True or origin!="LEGACY_PRESERVED": errors.append("LEGACY_HUMAN_TEST must be HUMAN_ORIGIN=true and ORIGIN=LEGACY_PRESERVED")
    if provenance=="EXTERNAL_PREEXISTING_HUMAN_DATA":
        if prohibited is not True: errors.append("EXTERNAL_PREEXISTING_HUMAN_DATA requires PROJECT_GENERATION_PROHIBITED=true")
        if human_origin is not True or origin!="EXTERNAL_PREEXISTING": errors.append("EXTERNAL_PREEXISTING_HUMAN_DATA must prove external pre-existing human origin")
    if human_origin is True and origin=="PROJECT_MACHINE_GENERATED": errors.append("human-origin source cannot be project machine-generated")
    if provenance=="OTHER":
        text_indicates_human=isinstance(description,str) and bool(HUMAN_ORIGIN_TEXT.search(description))
        if text_indicates_human and human_origin is not True: errors.append("OTHER source description indicates human origin but HUMAN_ORIGIN is not true")
        if human_origin is True and (prohibited is not True or origin not in {"EXTERNAL_PREEXISTING","LEGACY_PRESERVED"}): errors.append("OTHER human-origin source must be provably external/legacy and project-generation-prohibited")
        if origin=="UNKNOWN": errors.append("OTHER source cannot use ambiguous UNKNOWN origin")
    errors+=_semantic_errors(description,"DESCRIPTION")
    if obj.get("SOURCE_URI") is not None: errors+=_semantic_errors(obj.get("SOURCE_URI"),"SOURCE_URI")
    return sorted(set(errors))

FORBIDDEN_HUMAN_KEYS={"participants","participant","participant_id","participant_age","participant_cohort","participant_plan","consent","recruitment","sample_recruitment","participant_compensation","human_subject_privacy","respondents","respondent","reviewers","human_reviewers","human_raters","human_annotators","interviewees","survey_respondents"}
MACHINE_EXPERIMENT_REQUIRED={"EXPERIMENT_ID","RUN_ID","METHOD_VERSION","METHOD_STATUS","FREEZE_ID","INPUT_DATASET","INPUT_VERSION","INPUT_HASH","MODEL_OR_TOOL","MODEL_OR_TOOL_VERSION","PROMPT_OR_RULESET_VERSION","RANDOM_SEED","N_RUNS","BENCHMARK_SET","HOLDOUT_SET","PERTURBATION_SET","ADVERSARIAL_CASES","ERROR_METRIC","AGGREGATION_METHOD","UNCERTAINTY_METHOD","CROSS_METHOD_AGREEMENT","CROSS_MODEL_DISAGREEMENT","OUTPUT_HASH","REPRODUCTION_POINTER","LIMITATIONS","PROHIBITED_OVERCLAIMS"}
def _normalize_key(key:Any)->str: return re.sub(r"[^a-z0-9]+","_",str(key).lower()).strip("_")
def _forbidden_key_errors(value:Any,path:str="$ ")->list[str]:
    errors=[]
    if isinstance(value,dict):
        for k,v in value.items():
            child_path=f"{path}.{k}"
            if _normalize_key(k) in FORBIDDEN_HUMAN_KEYS: errors.append(f"forbidden human-research key at {child_path}")
            errors+=_forbidden_key_errors(v,child_path)
    elif isinstance(value,(list,tuple)):
        for i,v in enumerate(value): errors+=_forbidden_key_errors(v,f"{path}[{i}]")
    return errors
def validate_experiment(obj:dict[str,Any])->list[str]:
    errors=_require_fields(obj,MACHINE_EXPERIMENT_REQUIRED)+_reject_unknown_fields(obj,MACHINE_EXPERIMENT_REQUIRED)+_forbidden_key_errors(obj)
    for k,v in obj.items(): errors+=_semantic_errors(v,k)
    n=obj.get("N_RUNS")
    if not isinstance(n,int) or isinstance(n,bool) or n<1: errors.append("N_RUNS must be integer >= 1")
    return sorted(set(errors))
METHOD_FREEZE_REQUIRED={"FREEZE_ID","QUESTION_ID","METHOD_VERSION","METHOD_STATUS","INPUT_IDENTITY","METHOD","MODEL_OR_TOOL_VERSION","PROMPT_OR_RULESET_VERSION","DATASET_SAMPLING","RANDOM_SEED_POLICY","METRICS","AGGREGATION","THRESHOLDS","LIMITATIONS","PLANNED_SENSITIVITY_ANALYSIS","METHOD_FROZEN","MACHINE_EXECUTABLE","REQUIRES_THIRD_PARTY_HUMAN","REQUIRES_OWNER_MANUAL_RESEARCH","REQUIRES_EXTERNAL_HUMAN_REVIEW","REQUIRES_HUMAN_DATA_COLLECTION"}
def validate_method_freeze(obj:dict[str,Any])->list[str]:
    errors=_require_fields(obj,METHOD_FREEZE_REQUIRED)+_reject_unknown_fields(obj,METHOD_FREEZE_REQUIRED)
    if obj.get("METHOD_FROZEN") is not True: errors.append("METHOD_FROZEN must be true only after machine-only validation")
    if obj.get("MACHINE_EXECUTABLE") is not True: errors.append("MACHINE_EXECUTABLE must be true")
    for n in DEFAULT_REQUIRED_FALSE:
        if obj.get(n) is not False: errors.append(f"{n} must be false")
    errors+=_forbidden_key_errors(obj)
    for k,v in obj.items(): errors+=_semantic_errors(v,k)
    return sorted(set(errors))

def lint_active_repository(root:Path=ROOT)->list[str]:
    errors=[]; active=[root/"AGENTS.md",root/"ROUTER.md",root/"SYSTEM_MANIFEST.yaml",root/"README.md",root/"ARCHITECTURE_MIGRATION_MAP.md",root/"contracts",root/"kernel",root/"protocols",root/"roles",root/"schemas",root/"engines/research"]; files=[]
    for item in active:
        if item.is_file(): files.append(item)
        elif item.is_dir(): files.extend(p for p in item.rglob("*") if p.is_file() and p.suffix.lower() in {".md",".yaml",".yml",".json"})
    for path in sorted(set(files)):
        for f in classify_text(path.read_text(encoding="utf-8",errors="replace")):
            if f.classification in FATAL_FINDINGS: errors.append(f"{path.relative_to(root)}: {f.classification}: {f.message}")
    return sorted(set(errors))

def _base_wp(): return {"WORK_PACKAGE_ID":"WP-001","QUESTION_ID":"Q-001","NAMESPACE":"research/default","EXECUTOR_ROLE":"AI_R_MASTER","VERIFIER_ROLE":"AI_R_VERIFIER","MACHINE_EXECUTABLE":True,"REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,"REQUIRES_EXTERNAL_REVIEWER":False,"REQUIRES_EXTERNAL_HUMAN_REVIEW":False,"REQUIRES_NEW_HUMAN_DATA":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,"CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS":True,"OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS":True,"EXECUTION_SURFACE":"local machine runtime","SOURCE_ACCESS_METHOD":"public machine-accessible corpus","COMPUTATION_METHOD":"deterministic structural analysis","VERIFICATION_METHOD":"automated reproducibility check","LIMITATIONS":[],"PROHIBITED_OVERCLAIMS":["Do not claim direct population measurement."],"OWNER_GATE_IF_ANY":None}
def _base_question(): return {"QUESTION_ID":"Q-001","QUESTION":"What structural pattern is supported?","TARGET_CONSTRUCT":"structural pattern","MACHINE_EXECUTABLE":True,"AVAILABLE_MACHINE_METHODS":["deterministic corpus analysis"],"AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE":["Published survey may be used as static evidence."],"REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,"REQUIRES_EXTERNAL_HUMAN_REVIEW":False,"REQUIRES_HUMAN_DATA_COLLECTION":False,"DIRECT_MEASUREMENT_POSSIBLE":False,"PROXY_MEASUREMENT_POSSIBLE":True,"EXPECTED_LIMITATION":"Direct population measurement remains unavailable.","OWNER_DECISION_COMPONENT":None,"CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS":True,"OWNER_AUTHORITY_ONLY_FOR_PROJECT_DECISIONS":True,"ADMISSION_STATUS":"ADMITTED_MACHINE_RESEARCH"}
def _owner_auth_pair():
    auth={"AUTHORIZATION_ID":"HRA-001","OWNER_DECISION_RECORD_REF":"ODR-001","OWNER_AUTHORITY_ROLE":"OWNER_K0","PROJECT_ID":"P-1","QUESTION_ID":"Q-H1","SCOPE":"one bounded recognition study","NAMESPACE":"human-research/P-1/Q-H1","NON_TRANSITIVE":True,"CREATE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM":True,"REAL_NON_OWNER_HUMANS_MAY_PARTICIPATE":True,"DEFAULT_RESEARCH_MODE_UNCHANGED":True}
    record={"artifact_type":"OWNER_DECISION_RECORD","artifact_id":"ODR-001","produced_by_role":"owner-interface","assignment_id":"A-OWNER-001","input_state_ref":"state:pre-human-research","status":"RECORDED","provenance":["OWNER_K0 explicit authorization decision"],"related_artifacts":["P-1","Q-H1"],"question_ref":"Q-H1","options_presented":["AUTHORIZE_SEPARATE_HUMAN_RESEARCH_WORKSTREAM","DO_NOT_AUTHORIZE"],"selected_option":OWNER_AUTH_SELECTED_OPTION,"owner_constraints":["bounded scope only"],"consequences_acknowledged":["default Research remains machine-only"],"authority_role":"OWNER_K0","decision_kind":OWNER_AUTH_DECISION_KIND,"project_id":"P-1","authorized_question_id":"Q-H1","authorized_scope":"one bounded recognition study","authorized_namespace":"human-research/P-1/Q-H1","authorization_id":"HRA-001","non_transitive":True,"default_research_mode_unchanged":True}
    return auth,record
def _resolver_for(record): return lambda ref: record if ref==record.get("artifact_id") else None
def _base_experiment(): return {"EXPERIMENT_ID":"EXP-1","RUN_ID":"RUN-1","METHOD_VERSION":"1.0","METHOD_STATUS":"FROZEN","FREEZE_ID":"FRZ-1","INPUT_DATASET":"public machine-readable corpus","INPUT_VERSION":"1","INPUT_HASH":"sha256:input","MODEL_OR_TOOL":"python","MODEL_OR_TOOL_VERSION":"3","PROMPT_OR_RULESET_VERSION":"rules-1","RANDOM_SEED":1,"N_RUNS":1,"BENCHMARK_SET":[],"HOLDOUT_SET":[],"PERTURBATION_SET":[],"ADVERSARIAL_CASES":[],"ERROR_METRIC":"exact mismatch","AGGREGATION_METHOD":"deterministic","UNCERTAINTY_METHOD":"sensitivity bounds","CROSS_METHOD_AGREEMENT":"not applicable","CROSS_MODEL_DISAGREEMENT":"not applicable","OUTPUT_HASH":"sha256:output","REPRODUCTION_POINTER":"runs/RUN-1","LIMITATIONS":["Proxy only."],"PROHIBITED_OVERCLAIMS":["Do not claim direct population recognition."]}
def _base_freeze(): return {"FREEZE_ID":"FRZ-1","QUESTION_ID":"Q-1","METHOD_VERSION":"1.0","METHOD_STATUS":"FROZEN","INPUT_IDENTITY":"public corpus v1","METHOD":"deterministic computational analysis","MODEL_OR_TOOL_VERSION":"python-3","PROMPT_OR_RULESET_VERSION":"rules-1","DATASET_SAMPLING":"deterministic full-corpus pass","RANDOM_SEED_POLICY":"fixed seed","METRICS":["exact agreement"],"AGGREGATION":"mean","THRESHOLDS":{"minimum":0.8},"LIMITATIONS":["Proxy only."],"PLANNED_SENSITIVITY_ANALYSIS":"parameter sweep","METHOD_FROZEN":True,"MACHINE_EXECUTABLE":True,"REQUIRES_THIRD_PARTY_HUMAN":False,"REQUIRES_OWNER_MANUAL_RESEARCH":False,"REQUIRES_EXTERNAL_HUMAN_REVIEW":False,"REQUIRES_HUMAN_DATA_COLLECTION":False}

def machine_only_regression_results()->dict[str,str]:
    r={}; check=lambda c,cond:r.__setitem__(c,"PASS" if cond else "FAIL")
    check("T01",any(f.classification=="ACTIVE_DEPENDENCY" for f in classify_text("Recruit native speakers."))); check("T02",any(f.classification=="ACTIVE_DEPENDENCY" for f in classify_text("Recruit native speakers. Do not overclaim.")))
    f=classify_text("Do not recruit native speakers."); check("T03",any(x.classification=="EXPLICIT_PROHIBITION" for x in f) and not any(x.classification=="ACTIVE_DEPENDENCY" for x in f)); f=classify_text("Published survey."); check("T04",any(x.classification=="STATIC_EXTERNAL_SOURCE" for x in f) and not any(x.classification=="ACTIVE_DEPENDENCY" for x in f)); check("T05",any(x.classification=="ACTIVE_DEPENDENCY" for x in classify_text("Use a published survey, then recruit 20 respondents."))); check("T06",any(x.classification=="ACTIVE_DEPENDENCY" for x in classify_text("Analyze archived interviews and interview five new speakers.")))
    wp=_base_wp(); wp["PARTICIPANT_PLAN"]="Recruit 50 speakers."; check("T07",bool(validate_work_package(wp))); wp=_base_wp(); wp["METADATA"]={"execution":{"reviewers":"external experts"}}; check("T08",bool(validate_work_package(wp))); q=_base_question(); q["AVAILABLE_MACHINE_METHODS"]=["Recruit native speakers"]; check("T09",bool(validate_question(q))); q=_base_question(); q["AVAILABLE_EXTERNAL_PREEXISTING_EVIDENCE"]=["Published survey, then recruit 20 new respondents."]; check("T10",bool(validate_question(q)))
    wp=_base_wp(); wp["COMPUTATION_METHOD"]="MODEL_PROXY ensemble comparison, explicitly labeled proxy-only."; check("T11",not validate_work_package(wp)); wp=_base_wp(); wp["COMPUTATION_METHOD"]="Use simulated LLM outputs as human responses."; check("T12",bool(validate_work_package(wp))); wp=_base_wp(); wp["OWNER_GATE_IF_ANY"]="OWNER_ACCEPTANCE"; wp["LIMITATIONS"]=["Owner accepts or rejects the project decision after machine evidence."]; check("T13",not validate_work_package(wp)); wp=_base_wp(); wp["REQUIRES_OWNER_MANUAL_RESEARCH"]=True; wp["SOURCE_ACCESS_METHOD"]="Owner must manually collect 100 URLs."; check("T14",bool(validate_work_package(wp)))
    auth,record=_owner_auth_pair(); resolver=_resolver_for(record); check("T15",bool(validate_human_research_authorization(auth))); fake=dict(auth); fake["OWNER_DECISION_RECORD_REF"]="ODR-NOT-FOUND"; check("T16",bool(validate_human_research_authorization(fake,resolver))); mismatch=True
    for field,value in (("project_id","P-OTHER"),("authorized_question_id","Q-OTHER"),("authorized_scope","broader study")):
        bad=dict(record); bad[field]=value; mismatch=mismatch and bool(validate_human_research_authorization(auth,_resolver_for(bad)))
    check("T17",mismatch); human_wp={"PROJECT_ID":"P-1","QUESTION_ID":"Q-H1","NAMESPACE":"human-research/P-1/Q-H1"}; default_wp=_base_wp(); default_wp["NAMESPACE"]=human_wp["NAMESPACE"]; check("T18",not validate_human_research_authorization(auth,resolver) and not validate_separate_human_work_package(human_wp,auth,resolver) and bool(validate_work_package(default_wp)))
    s={"SOURCE_ID":"SRC-1","PROVENANCE_CLASS":"EXTERNAL_PREEXISTING_HUMAN_DATA","ORIGIN":"EXTERNAL_PREEXISTING","HUMAN_ORIGIN":True,"PROJECT_GENERATION_PROHIBITED":False,"DESCRIPTION":"Published survey dataset."}; check("T19",bool(validate_source(s))); s={"SOURCE_ID":"SRC-2","PROVENANCE_CLASS":"OTHER","ORIGIN":"PROJECT_MACHINE_GENERATED","HUMAN_ORIGIN":False,"PROJECT_GENERATION_PROHIBITED":False,"DESCRIPTION":"Recruit participants and collect new human responses."}; check("T20",bool(validate_source(s)))
    e=_base_experiment(); e["INPUT_DATASET"]="Recruit 20 participants and collect responses."; check("T21",bool(validate_experiment(e))); e=_base_experiment(); e["INPUT_DATASET"]={"metadata":{"collection_plan":{"participants":"Recruit 20 participants."}}}; check("T22",bool(validate_experiment(e))); e=_base_experiment(); e["INPUT_DATASET"]="Archived public interview corpus."; check("T23",not validate_experiment(e)); fr=_base_freeze(); fr["METHOD"]="Recruit 50 speakers and survey them."; check("T24",bool(validate_method_freeze(fr))); check("T25",not validate_method_freeze(_base_freeze())); wp=_base_wp(); wp["SOURCE_ACCESS_METHOD"]="No suitable public evidence is currently available."; wp["COMPUTATION_METHOD"]="Return UNKNOWN / INSUFFICIENT_PUBLIC_EVIDENCE."; check("T26",not validate_work_package(wp)); check("T27",any(x.classification=="ACTIVE_DEPENDENCY" for x in classify_text("Do not recruit native speakers; nevertheless recruit 20 participants."))); check("T28",any(x.classification=="ACTIVE_DEPENDENCY" for x in classify_text("Use a published survey; then recruit 20 respondents.")))
    negative_cases=("Ask the user again if required project authority is missing.","Contact the user for the missing repository identifier.","Consult Owner/K0 before accepting the project decision.","Never recruit human participants.","This workflow never creates authority to recruit humans.","Human annotation is prohibited.","The legacy workflow used human annotation before retirement.")
    for i,text in enumerate(negative_cases,29): check(f"T{i:02d}",not any(x.classification in FATAL_FINDINGS for x in classify_text(text)))
    positive_cases=("Hire five human annotators to label the dataset.","Assign human annotators to label the dataset.","Use human raters to score the responses.","Employ human coders to code the samples.","Contract crowdworkers to classify the dataset.","The legacy pipeline requires human annotation for every new sample.","In the legacy pipeline, human annotation remains mandatory.")
    for i,text in enumerate(positive_cases,36): check(f"T{i:02d}",any(x.classification=="ACTIVE_DEPENDENCY" for x in classify_text(text)))
    return r

def run_machine_only_regressions()->list[str]: return [f"{c}: machine-only regression failed" for c,v in machine_only_regression_results().items() if v!="PASS"]
def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if not argv or argv==["--repo"]:
        errors=lint_active_repository(); errors.extend(run_machine_only_regressions())
        if errors:
            print("Research machine-only policy: FAIL"); [print(f"- {e}") for e in errors]; return 1
        print("Research machine-only policy: PASS"); return 0
    print("usage: research_policy.py [--repo]",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
