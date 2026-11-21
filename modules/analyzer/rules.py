"""
Rule-based cues for the baseline analyzer.

Every expectation and misconception id in ``data/units/*.json`` has a list of
regex cues here. The cues are this module's own rules, so they live in
``modules/analyzer/`` and the shared taxonomy files stay unchanged.

``tests/test_rules.py`` fails if a taxonomy id has no cues or a cue id is not
in the taxonomy, so the two stay in sync when the taxonomy is edited.

All patterns are matched case-insensitively against the student's message.
"""

from __future__ import annotations

import re

# ── Help-request intent ─────────────────────────────────────────────────
# Checked in this order: give_me_answer > debug_request > concept_question.
# Anything else is an answer_attempt.

GIVE_ME_ANSWER_CUES = [
    r"\bjust (tell|give|show|fix|write|do)\b",
    r"\bgive me the (answer|solution|fix|prompt)\b",
    r"\bwhat('?s| is) the (right |correct )?answer\b",
    r"\b(fix|write|do|solve) (it|this) for me\b",
    r"\btell me what to (write|do|put)\b",
    r"\bwhat should i (write|type|put)\b",
    r"\bcan you (just )?(fix|write|solve|rewrite|correct) (it|this|my)\b",
    r"\bskip the (questions|hints)\b",
    r"\bjust the answer\b",
    r"\bplease just (fix|give)\b",
    r"\bi want the direct answer\b",
]

DEBUG_REQUEST_CUES = [
    r"\b(doesn'?t|does not|isn'?t|is not|not) work(ing)?\b",
    r"\bbroken\b",
    r"\berror\b",
    r"\bbug(gy)?\b",
    r"\bkeeps? (giving|returning|producing|outputting|ignoring|adding)\b",
    r"\binconsistent\b",
    r"\bwrong (output|format|answer|result)s?\b",
    r"\bwhy is it (failing|breaking)\b",
    r"\bfails? to parse\b",
    r"\b(fails?|failing)\b",
    r"\bmy (prompt|output|code|response)\b.{0,40}\b(wrong|weird|different|messy|random|ignore\w*)\b",
]

# Open questions ("what is a delimiter?") are always concept questions.
WH_QUESTION_START = re.compile(
    r"^\s*(what|why|how|which|when|where|who|explain|what'?s|can you explain|"
    r"what'?s the difference|difference between)\b",
    re.IGNORECASE,
)
# Yes/no questions are concept questions unless they carry an answer
# ("Is it because we need a JSON schema?" is a hedged answer attempt).
YES_NO_QUESTION_START = re.compile(
    r"^\s*(is|are|does|do|can|could|should|would|will|isn'?t|doesn'?t)\b",
    re.IGNORECASE,
)

# ── Negation ────────────────────────────────────────────────────────────
# An expectation cue preceded closely by a negation ("you don't need JSON")
# does not count as covering the expectation.
NEGATION_BEFORE = re.compile(
    r"\b(not|no|never|without|don'?t|doesn'?t|didn'?t|isn'?t|won'?t|can'?t|cannot|"
    r"no need to)\b[^.!?;,]{0,25}$",
    re.IGNORECASE,
)

# ── Expectation cues (keyed by expectation id) ──────────────────────────
EXPECTATION_CUES: dict[str, list[str]] = {
    # Unit 1 · topic_output_formatting
    "exp_explicit_format": [
        r"\bjson\b",
        r"\bschema\b",
        r"\bmarkdown\b",
        r"\btable\b",
        r"\bbullet(ed)? (points?|list)\b",
        r"\b(specify|state|define|give|set|describe|spell out)\w* (the |an? )?"
        r"(exact |explicit |expected |output |response |target )*(format|structure)\b",
        r"\boutput format\b",
    ],
    "exp_boundary_delimiters": [
        r"\bdelimiters?\b",
        r"\bxml\b",
        r"\btags?\b",
        r"\btriple backticks?\b",
        r"```",
        r"\bseparat\w+ (the )?(instructions?|input|data|context)\b",
    ],
    "exp_role_persona": [
        r"\bpersona\b",
        r"\brole\b",
        r"\bact as\b",
        r"\byou are an? \w+",
        r"\bsystem (prompt|message)\b",
    ],
    # Unit 1 · topic_system_instructions_vs_user_data
    "exp_instruction_data_separation": [
        r"\b(isolate|separate|wrap|enclose|quote)\w* (the )?(user|untrusted|input|data)\b",
        r"\buntrusted\b",
        r"\b(user (input|data)|the input) (in|inside|within|between) .{0,15}(tags|delimiters)\b",
        r"\btreat\w* (it|the (user )?input|user (input|data)) as (plain )?data\b",
    ],
    "exp_defensive_constraints": [
        r"\bignore (any )?instructions? (in|inside|within|from)\b",
        r"\b(if|when) the (user|input|text|document) (tries|asks|says|contains|conflicts)\b",
        r"\bfall ?back\b",
        r"\bprompt injection\b",
        r"\b(refuse|reject|decline)\b",
    ],
    # Unit 2 · topic_in_context_exemplars
    "exp_representative_examples": [
        r"\b(diverse|varied|balanced|representative|different|mix of) (set of )?(examples?|exemplars?|labels?)\b",
        r"\bedge cases?\b",
        r"\b(cover|include)\w* (all|each|every|both) (the )?(classes|labels|categories|cases)\b",
        r"\bbalanc\w* (the )?(labels|classes|examples)\b",
    ],
    "exp_consistent_formatting": [
        r"\bconsistent(ly)? (format\w*|labels?|structure|delimiters?)\b",
        r"\b(same|uniform) (format|structure|labels?|delimiters?|syntax)\b",
        r"\bformat\w* (them|the examples?|each example) (the same|consistently|identically)\b",
    ],
    # Unit 2 · topic_chain_of_thought
    "exp_intermediate_token_allocation": [
        r"\bstep[- ]by[- ]step\b",
        r"\bintermediate (steps?|reasoning|tokens?)\b",
        r"\breason\w* (through|out)\b",
        r"\bbreak\w* (it|the problem|the task)? ?down\b",
        r"\bshow (its|your|the) (work|reasoning|steps)\b",
    ],
    "exp_reasoning_before_answer": [
        r"\b(reasoning|rationale|steps?|explanation|working) (comes? )?(before|first|then) (the )?(final )?answer\b",
        r"\banswer (at the end|last|after (the )?(reasoning|steps))\b",
        r"\b(reason|think) first\b",
    ],
    # Unit 3 · topic_decoding_parameters
    "exp_temperature_controls_randomness_not_facts": [
        r"\btemperature (controls?|affects?|changes?|sets?|adjusts?|scales?) (the )?"
        r"(randomness|creativity|diversity|variability|sampling|distribution|probabilit\w*)\b",
        r"\bsoftmax\b",
        r"\b(more|less) (random|deterministic)\b",
        r"\b(doesn'?t|does not|won'?t|can'?t|cannot) (make|guarantee) (it |the output |the answer )?"
        r"(factual|true|correct|accurate)\b",
    ],
    "exp_top_p_nucleus_sampling": [
        r"\btop[- ]?p\b",
        r"\bnucleus\b",
        r"\bprobability mass\b",
        r"\bcumulative probability\b",
    ],
    # Unit 3 · topic_rag_grounding
    "exp_dynamic_external_evidence": [
        r"\bretriev\w*",
        r"\b(vector|external|knowledge) (database|store|base|index|documents?|sources?)\b",
        r"\b(inject|insert|add|put|paste)\w* .{0,30}\b(into|in) (the )?(prompt|context)\b",
        r"\b(post[- ]?cutoff|knowledge cutoff|up[- ]to[- ]date|proprietary|private data)\b",
    ],
    "exp_extrinsic_hallucination_mitigation": [
        r"\bground\w*",
        r"\bcit(e|es|ed|ing|ation|ations)\b",
        r"\b(reduce|reduces|mitigate\w*|prevent\w*|fewer|less)\b.{0,15}\bhallucinat\w*",
        r"\bverif\w*",
    ],
}

# ── Misconception cues (keyed by misconception id) ──────────────────────
MISCONCEPTION_CUES: dict[str, list[str]] = {
    # Unit 1
    "misc_implicit_format_expectation": [
        r"\b(model|it|llm|ai|gpt) (will|should|can|would) (just )?(figure|know|infer|guess|work) (it )?out\b",
        r"\b(model|it|llm|ai) (will|should|can) (just )?(know|infer|guess)\b",
        r"\b(don'?t|do not|no need to|didn'?t|never) (need to |have to )?(specify|mention|say|tell|define)\w* "
        r"(it |the |a |any )?(format|structure)\b",
        r"\bwithout (specifying|giving|stating|defining) (the |a |any )?(format|structure)\b",
        r"\bone[- ]line prompt\b",
        r"\b(should|will) (always )?(be|stay|come out) (the same|consistent)\b",
    ],
    "misc_prompt_length_illusion": [
        r"\blonger prompts?\b",
        r"\bthe longer the better\b",
        r"\b(add|adding|use|using|write|writing) (more|lots of|extra) (words|adjectives|text|detail|details)\b",
        r"\bmore (words|adjectives|verbose)\b",
    ],
    "misc_confusing_instructions_with_data": [
        r"\b(follow|obey|do) what(ever)? the (user|input|document|email|text) says\b",
        r"\buser (input|message|data) (overrides?|takes priority|is (an )?instructions?)\b",
        r"\b(model|it) (should|will|must) follow (the )?(instructions?|commands?) (in|from) the "
        r"(input|data|document|email|text)\b",
        r"\buser data (is|are) (just )?(more )?instructions\b",
    ],
    # Unit 2
    "misc_majority_label_bias": [
        r"\b(all|mostly|only) (the )?(examples?|exemplars?) (are|were|from|of|with|show) "
        r"(the same|one|positive|negative)\b",
        r"\b(all|mostly) (positive|negative) (examples?|exemplars?|labels?)\b",
        r"\b(doesn'?t|does not) matter (which|what) (examples?|labels?)\b",
        r"\b(any|random) examples? (will|would|is|are) (do|fine|ok|okay)\b",
    ],
    "misc_recency_bias": [
        r"\border (doesn'?t|does not|won'?t|shouldn'?t) matter\b",
        r"\b(order|position) of (the )?(examples?|exemplars?) (doesn'?t|does not|won'?t) matter\b",
        r"\b(all|every|each) (examples?|exemplars?) (count|matter|weigh\w*|influence) (the )?(same|equally)\b",
    ],
    "misc_cot_for_factual_lookup": [
        r"\b(cot|chain[- ]of[- ]thought|step[- ]by[- ]step|thinking|reasoning) (will|can|would|should) "
        r"(fix|give|provide|find|supply|add|teach)\w* (it |the model )?(the )?(missing |correct |right )?"
        r"(facts?|knowledge|information)\b",
        r"\b(fix|solve|fill)\w* (the |a )?(missing|wrong|outdated) (facts?|knowledge|information)\b",
        r"\b(know|learn) (new )?facts\b",
    ],
    "misc_answer_before_rationale": [
        r"\banswer (first|before)\b",
        r"\b(put|give|state|write)\w* (the )?(final )?answer (first|at the (start|beginning|top)|before)\b",
        r"\b(reasoning|explanation|steps?) (after|at the end|afterwards)\b",
    ],
    # Unit 3
    "misc_zero_temp_factual_guarantee": [
        r"\btemp(erature)?\s*(=|of|to|at|is)?\s*0\b.{0,50}\b(no|never|eliminat\w*|stops?|prevents?|fix\w*|"
        r"remov\w*|guarantee\w*|always (true|correct|accurate|factual))\b",
        r"\b(zero|0) temp(erature)?\b.{0,50}\b(no|never|eliminat\w*|stops?|prevents?|fix\w*|guarantee\w*|"
        r"factual|accurate)\b",
        r"\b(lower|low|reduce|reducing|lowering) (the )?temp(erature)?\b.{0,30}\b(stop|stops|prevent\w*|fix\w*|"
        r"eliminat\w*|remov\w*|no more)\b.{0,10}\bhallucinat\w*",
    ],
    "misc_confusing_sampling_with_retrieval": [
        r"\btop[- ]?[kp] (retrieves?|fetches?|selects?|picks?|returns?|pulls?) (the )?(\w+ )?"
        r"(documents?|chunks?|sources?|passages?)\b",
        r"\btop[- ]?[kp]\b.{0,30}\b(from|in) the (database|vector|index|documents?|knowledge base)\b",
    ],
    "misc_llm_live_knowledge_assumption": [
        r"\b(llm|model|it|chatgpt|gpt|ai) (already |just |can |will )?(search(es)?|browses?|quer(y|ies)|"
        r"looks? up|access(es)?|has access to|checks?) (the )?(internet|web|database|live|latest|current|real[- ]time)\b",
        r"\b(always|already) (up[- ]to[- ]date|knows everything|has the latest)\b",
        r"\b(doesn'?t|does not|don'?t) need (rag|retrieval)\b",
    ],
}


def compile_cues(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


COMPILED_EXPECTATIONS = {k: compile_cues(v) for k, v in EXPECTATION_CUES.items()}
COMPILED_MISCONCEPTIONS = {k: compile_cues(v) for k, v in MISCONCEPTION_CUES.items()}
COMPILED_GIVE_ME_ANSWER = compile_cues(GIVE_ME_ANSWER_CUES)
COMPILED_DEBUG = compile_cues(DEBUG_REQUEST_CUES)
