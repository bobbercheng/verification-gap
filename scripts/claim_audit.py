#!/usr/bin/env python3
"""Guard against the claim errors that recurred across the internal pre-submission reviews and the camera-ready audit.

Every one of those reviews found the same kinds of mistake, never a wrong computation:

  population   a count over a subset described with a word for the whole set, for example calling a
               figure over the 16 fatal-or-gap texts a figure over "every edited text", or a count over the 16
               sound texts (8 originals + 8 harmless edits) a count over "mutants".
  counterpart  one side of a paired outcome reported without the other, for example false accepts
               without false rejects, or referrals without what they cost.
  attribution  a pooled figure attached to a single model or procedure.
  run          a figure that holds only in the first run (P) stated without saying so, or a dominance /
               reversal / "no variance" claim with no run qualifier.
  status       a post-hoc quantity in a section that never says "post hoc".

Numbers cannot drift here, because they are generated. Sentences can. This script checks the paragraph and
sentence around each guarded macro, so the class of error fails the build rather than reaching a reader.

Two registries are checked:
  REGISTRY     hand-written entries for the v17 macros (gen/planted_macros.tex and friends);
  CR registry  gen/CR_MACROS.md, written by scripts/camera_ready_macros.py: population, grader(s), run and status
               of every \\CR... macro, from which the population, pairing, run and post-hoc rules are derived.

Rules (paragraph = blank-line separated block; sentence = split at . ; ? ! outside common abbreviations):
  population   a guarded macro's paragraph names its population;
  needs        the macros a paired outcome needs are in the same paragraph;
  mutant       no sentence carrying a sound-set macro (16 = originals + harmless) says "mutant";
  run          a P-only (or R-only, or run-once) macro, and any sentence with "dominat", "operating point",
               "no variance", "same score" or "revers", has a run qualifier in its own or the previous sentence;
  post hoc     a section using a strict-mark, flag, sweep, AUC, routing or re-query macro says "post hoc";
  post-sub     a section using a post-submission macro says it was run after submission (outside this paper's protocol);
  flips        \\FLIPRULES equals \\FLIPTOTAL and \\CRFlipRules{P,R} equal \\CRFlipTotal{P,R}.
Appendix Q (the dated change list, which quotes the reviewed wording) is skipped.

Usage: python3 scripts/claim_audit.py [--tex main.tex] [--also appendix.tex] [--quiet]
       python3 scripts/claim_audit.py --positive-control     (must flag the reviewed v17 abstract)
Exit status is 1 if any guarded use fails, so it can gate a build.
"""
import argparse, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

FATAL_GAP = ("fatal-or-gap", "broken", "fatal edit", "fatal or gap")
SOUND = ("sound", "originals", "harmless")
ORIG = ("original",)
HARMLESS = ("harmless",)

REGISTRY = {
    # threshold sweep: a pass mark's acceptances are meaningless without what it rejects
    "SWEEPFIVE": {"population": FATAL_GAP, "needs": ["SWEEPN"]},
    "SWEEPSIX": {"population": FATAL_GAP, "needs": ["SWEEPN"]},
    "SWEEPSEVEN": {"population": FATAL_GAP, "needs": ["SWEEPSEVENFR"]},
    "SWEEPCOMPLETE": {"population": FATAL_GAP, "needs": ["SWEEPCOMPLETEFR"]},
    "SWEEPNGOOD": {"population": SOUND, "needs": [], "sound": True},
    "SWEEPSEVENFR": {"population": SOUND, "needs": [], "sound": True},
    "SWEEPCOMPLETEFR": {"population": SOUND, "needs": [], "sound": True},
    # routing: referrals are a cost and must appear with both error kinds
    "ESCWITNESS": {"population": (), "needs": ["ESCBADWITNESS", "ESCSOUNDWITNESS"]},
    "ESCCOMPLETE": {"population": (), "needs": ["ESCBADCOMPLETE", "ESCSOUNDCOMPLETE"]},
    "ESCGRADE": {"population": (), "needs": ["ESCBADGRADE", "ESCSOUNDGRADE"]},
    "ESCGRADESEVEN": {"population": (), "needs": ["ESCBADGRADESEVEN", "ESCSOUNDGRADESEVEN"]},
    "ESCCLOSURE": {"population": (), "needs": ["ESCBADCLOSURE", "ESCSOUNDCLOSURE"]},
    "ESCFOURWITNESS": {"population": (), "needs": ["ESCFOURCOMPLETE"]},
    "ESCSOUNDWITNESS": {"population": SOUND, "needs": [], "sound": True},
    "ESCSOUNDCOMPLETE": {"population": SOUND, "needs": [], "sound": True},
    "ESCSOUNDGRADE": {"population": SOUND, "needs": [], "sound": True},
    "ESCSOUNDGRADESEVEN": {"population": SOUND, "needs": [], "sound": True},
    "ESCSOUNDCLOSURE": {"population": SOUND, "needs": [], "sound": True},
    # binary gates: acceptances of broken texts need the population named
    "PLANTFAGRADE": {"population": FATAL_GAP, "needs": []},
    "PLANTFAGRADEC": {"population": FATAL_GAP, "needs": []},
    "PLANTEXCLFOURG": {"population": FATAL_GAP + ("disputed",), "needs": ["PLANTEXCLFOURGC"]},
    "PLANTEXCLFIVEG": {"population": ("repair", "disputed"), "needs": ["PLANTEXCLFIVEGC"]},
    # false rejects are counted on the originals (the protocol's endpoint); harmless refusals on the harmless edits
    "PLANTFRWITNESS": {"population": ORIG, "needs": ["PLANTHREFUSEWITNESS"], "sound": True},
    "PLANTHREFUSEWITNESS": {"population": HARMLESS, "needs": [], "sound": True},
    "PLANTHREFUSEGRADEC": {"population": HARMLESS, "needs": [], "sound": True},
    "PLANTHREFUSEGRADE": {"population": HARMLESS, "needs": [], "sound": True},
    "PLANTHREFUSEGRADESEVEN": {"population": HARMLESS, "needs": [], "sound": True},
    # localization: the fatal-or-gap figures must not be described as covering all edits
    "COSTGRADERLOC": {"population": FATAL_GAP, "needs": ["COSTWITNESSLOC"]},
    "COSTGRADERSEC": {"population": FATAL_GAP, "needs": ["COSTWITNESSSEC"]},
    "COSTALLGRADERLOC": {"population": ("all", "edits"), "needs": ["COSTALLWITNESSLOC"]},
    # attribution: a per-grader count must not be stated as if pooled, and vice versa
    # "it passed" is banned here: that phrase names GPT's own accepted set (15 texts), not the 13 both graders passed
    "PLANTNAMEDGPT": {"population": ("both graders passed", "pass mark of 5 accepts", "both graders accepted", "passed at 5"),
                      "forbidden": ("it passed", "texts it accepted"), "needs": []},
    "PLANTNAMEDGRADE": {"population": ("at least one", "either grader", "one grader"), "needs": []},
    # first-run-only figures: the sentence must say which run
    "AUCGPT": {"population": (), "needs": ["AUCCLAUDE"], "run": True},
    "SPREADGPT": {"population": (), "needs": [], "run": True},
    "PLANTRECODE": {"population": (), "needs": [], "run": True},
    "REPPAIRSEVEN": {"population": (), "needs": [], "run": True},
    "REPPAIRCOMPLETE": {"population": (), "needs": [], "run": True},
    # convention reversal: correlated rules must not read as independent replications
    "FLIPTOTAL": {"population": (), "needs": ["FLIPAGREE"]},
}
# every PLANTFR* macro counts false rejects on the originals
for _m in ("PLANTFRGRADE", "PLANTFRCLOSURE", "PLANTFRREFADJ", "PLANTFRGRADEC", "PLANTFRGRADECGPT", "PLANTFRGRADECCLAUDE",
           "PLANTFRGRADEGPT", "PLANTFRGRADECLAUDE", "PLANTFRCLOSUREGPT", "PLANTFRCLOSURECLAUDE", "PLANTFRCLOSUREGLM",
           "PLANTFRCLOSUREGC", "PLANTFRWITNESSGPT", "PLANTFRWITNESSCLAUDE", "PLANTFRREFADJAW", "PLANTFRREFADJWIT",
           "PLANTFRREFADJWITAW", "PLANTFRREFADJGRD", "PLANTFRREFADJGRDAW", "PLANTFRREFADJWITGPT", "PLANTFRREFADJWITCLAUDE",
           "PLANTFRGRADEOTHER", "PLANTFRGRADEGPTAUTH", "PLANTFRWITNESSOTHER", "PLANTFRWITNESSGPTAUTH", "PLANTFRCLOSUREGCOTHER",
           "PLANTFRCLOSUREGCGPTAUTH", "PLANTFRREFADJWITOTHER", "PLANTFRREFADJWITGPTAUTH", "PLANTFRREFADJWITAWOTHER",
           "PLANTFRREFADJWITAWGPTAUTH", "PLANTFRGRADESEVEN"):
    REGISTRY.setdefault(_m, {"population": ORIG, "needs": [], "sound": True})
# v17 macros that are post-hoc reads (the section using them must say so)
V17_POSTHOC = re.compile(r"^(SWEEP|AUC|SPREAD|ESC|REPPAIR|PLANTREP|PLANTRECODE|FLIP|PLANTFAGRADEC|PLANTFAGRADESEVEN|"
                         r"PLANTHREFUSEGRADEC|PLANTHREFUSEGRADESEVEN)")

TRIGGER_WORDS = ("dominat", "operating point", "no variance", "same score", "revers")
RUNQ_I = re.compile(r"first run|primary run|both runs|two runs|each run|each of (?:the )?two|re-?quer|re-?run|rerun|"
                    r"repeat(?:ed)? (?:call|query|run)|replicate|same-day|one run|run once|ran once|single run|stored run|"
                    r"second run|either run|neither run|later run|retest|this run|in the first|run-dependent|in both", re.I)
RUNQ_C = re.compile(r"\bin [PR]\b|\([PR]\)|\b[PR]:|\bP\+R\b|\bP and R\b|\bP, R\b|\[[PR]\]")
POSTHOC_WORDS = re.compile(r"post[- ]hoc", re.I)
POSTSUB_WORDS = re.compile(r"after submission|after the workshop review|post-submission|after review|outside this paper's protocol", re.I)
ABBREV = re.compile(r"(?:\be\.g|\bi\.e|\bet al|\bApp|\bFig|\bTab|\bvs|\bcf|\bSec|\bEq|\bno|\bresp|\bapprox|\bca)\.$", re.I)
NUMERIC = re.compile(r"-?\d+(\.\d+)?")


# ------------------------------------------------------------------------------------------------ text regions
def strip_comments(tex: str) -> str:
    """Blank out % comments (keeping offsets and line numbers)."""
    return re.sub(r"(?<!\\)%[^\n]*", lambda m: " " * len(m.group(0)), tex)


def blank_verbatim(tex: str) -> str:
    """Blank out verbatim environments (printed prompts and rubrics are quotations, not claims), keeping line numbers."""
    return re.sub(r"\\begin\{(verbatim\*?|Verbatim|lstlisting)\}.*?\\end\{\1\}",
                  lambda m: re.sub(r"[^\n]", " ", m.group(0)), tex, flags=re.S)


def appq_spans(tex: str):
    """Character spans of Appendix Q (the dated change list): the \\section whose label is app:q / app:changes /
    app:corrections / app:changelog, or whose title starts with 'Changes', up to the next \\section or \\end{document}."""
    spans = []
    secs = list(re.finditer(r"\\section\*?\{([^}]*)\}", tex))
    for i, m in enumerate(secs):
        head = tex[m.start():m.start() + 400]
        lab = re.search(r"\\label\{([^}]*)\}", head)
        title = m.group(1).strip().lower()
        if title.startswith("changes") or (lab and lab.group(1) in ("app:q", "app:changes", "app:corrections", "app:changelog")):
            end = secs[i + 1].start() if i + 1 < len(secs) else len(tex)
            e2 = tex.find("\\end{document}", m.start())
            if e2 != -1:
                end = min(end, e2)
            spans.append((m.start(), end))
    return spans


def body_region(tex: str):
    """(start, end) of the audited text: from \\begin{document} (or the start) to the bibliography (or the end)."""
    s = tex.find("\\begin{document}")
    s = 0 if s < 0 else s
    e = len(tex)
    for marker in ("\\bibliographystyle", "\\bibliography{"):
        k = tex.find(marker, s)
        if k != -1:
            e = min(e, k)
    return s, e


def paragraphs(tex: str):
    s, e = body_region(tex)
    out, pos = [], s
    for chunk in re.split(r"(\n\s*\n)", tex[s:e]):
        if chunk and not re.fullmatch(r"\n\s*\n", chunk):
            out.append((pos, chunk))
        pos += len(chunk)
    return out


def sections(tex: str):
    """(start, end) of each top-level unit: the abstract and every \\section."""
    s, e = body_region(tex)
    cuts = sorted({s, e} | {s + m.start() for m in re.finditer(r"\\section\*?\{|\\begin\{abstract\}|\\end\{abstract\}", tex[s:e])})
    return [(a, b) for a, b in zip(cuts, cuts[1:]) if b > a]


def sentences(para: str):
    """Split a paragraph into (offset, sentence); never splits after common abbreviations."""
    out, start = [], 0
    for m in re.finditer(r"[.;?!](?=\s+[A-Z\\(`])", para):
        chunk = para[start:m.end()]
        if ABBREV.search(chunk.rstrip()):
            continue
        out.append((start, chunk))
        start = m.end()
    if start < len(para):
        out.append((start, para[start:]))
    return out


def line_of(tex: str, offset: int) -> int:
    return tex.count("\n", 0, offset) + 1


def at(chunk: str, macro: str) -> int:
    """Offset of a macro (or a trigger word) inside a chunk, so a problem is reported on its own line."""
    m = re.search(r"\\" + re.escape(macro) + r"(?![A-Za-z])", chunk)
    if m:
        return m.start()
    k = chunk.lower().find(macro.lower())
    return k if k >= 0 else len(chunk) - len(chunk.lstrip())


def has_runq(text: str) -> bool:
    return bool(RUNQ_I.search(text) or RUNQ_C.search(text))


# ------------------------------------------------------------------------------------------------ CR registry
def load_cr_registry(path: pathlib.Path):
    reg = {}
    if not path.is_file():
        return reg
    for ln in path.read_text().splitlines():
        m = re.match(r"\|\s*`\\(CR[A-Za-z]+)`\s*\|(.*)\|\s*$", ln)
        if not m:
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", m.group(2))]
        if len(cells) < 7:
            continue
        reg[m.group(1)] = {"value": cells[0], "pop": cells[1], "graders": cells[2], "run": cells[3], "status": cells[4], "did": cells[5]}
    return reg


def cr_class(name: str):
    """Population class of a CR macro from its name (the registry's population column says the same in words)."""
    n = name[2:]
    if re.search(r"SoundRej|SoundExcl|Route\w*Sound|^NSound|HRefuse|SoundMax", n):
        return "sound"
    if re.search(r"BrokenAcc|Route\w*Broken|^NBroken|BrokenMin|BrokenMax|Ladder(Pass|Strict|Flag|Witness)", n):
        return "broken"
    if re.search(r"FAcc|Fatal", n):
        return "fatal"
    if re.search(r"GAcc|^Gap|GPTGap|ClaudeGap", n):
        return "gap"
    if re.search(r"HRej|HQuote|HSeven|HBelow", n):
        return "harmless"
    if re.search(r"ORej|OrigRej|OrigSeven", n):
        return "original"
    if re.search(r"Route\w*Ref(P|R)?$|RouteRef$", n):
        return "referral"
    return None


CLASS_WORDS = {"sound": SOUND, "broken": FATAL_GAP + ("fatal", "gap", "deletion"), "fatal": ("fatal",), "gap": ("gap", "deletion", "omission"),
               "harmless": ("harmless",), "original": ORIG, "referral": ("refer",)}
POSTHOC_TAG = re.compile(r"^CR(Strict|Flag|Sweep|AUC|Route|StrictFlag|Recode|FlagDepart)")


def cr_needs(name: str, reg):
    """Paired outcomes: a strict-mark, flag or witness acceptance count needs its rejection count, and a referral count
    needs both error counts. The pass mark's broken count needs its sound count only beside a strict/flag count."""
    out = []
    m = re.fullmatch(r"CR(\w*?)BrokenAcc(\w*)", name)
    if m and "Pass" not in m.group(1) and not m.group(2).startswith(("GptBases", "OtherBases", "Excl")):
        pair = f"CR{m.group(1)}SoundRej{m.group(2)}"
        if pair in reg:
            out.append(pair)
    m = re.fullmatch(r"CR(\w*?)Route(\w+?)Ref(P|R)", name)
    if m:
        for q in ("Broken", "Sound"):
            pair = f"CR{m.group(1)}Route{m.group(2)}{q}{m.group(3)}"
            if pair in reg:
                out.append(pair)
    m = re.fullmatch(r"CR(\w*?)RouteRef", name)
    if m:
        for q in ("Broken", "Sound"):
            pair = f"CR{m.group(1)}Route{q}"
            if pair in reg:
                out.append(pair)
    return out


# ------------------------------------------------------------------------------------------------ audit
def audit(tex, where, checked, problems, cr=None):
    cr = cr or {}
    tex = blank_verbatim(strip_comments(tex))
    skip = appq_spans(tex)
    in_skip = lambda off: any(a <= off < b for a, b in skip)
    macro_re = re.compile(r"\\([A-Za-z]+)")
    for off, para in paragraphs(tex):
        if in_skip(off):
            continue
        used_all = set(macro_re.findall(para))
        used = {u for u in used_all if u.isupper() and len(u) > 1}
        crs = {u for u in used_all if u.startswith("CR") and u in cr}
        low = re.sub(r"\s+", " ", para).lower()
        # --- v17 registry (paragraph level)
        for macro in sorted(used & set(REGISTRY)):
            checked += 1
            spec = REGISTRY[macro]
            pops = spec["population"]
            if pops and not any(p.lower() in low for p in pops):
                problems.append((where, line_of(tex, off + at(para, macro)), macro, "population not named; expected one of " + ", ".join(repr(p) for p in pops)))
            for bad in spec.get("forbidden", ()):
                if bad.lower() in low:
                    problems.append((where, line_of(tex, off + at(para, macro)), macro, f"population misnamed: {bad!r} describes a different set"))
            for need in spec["needs"]:
                if need not in used:
                    problems.append((where, line_of(tex, off + at(para, macro)), macro, f"paired outcome missing: \\{need} is not in the same paragraph"))
        # --- CR registry (paragraph level)
        for macro in sorted(crs):
            info = cr[macro]
            if not NUMERIC.fullmatch(info["value"]):
                continue            # ids, dates and text macros
            checked += 1
            cls = cr_class(macro)
            if cls and not any(w.lower() in low for w in CLASS_WORDS[cls]):
                problems.append((where, line_of(tex, off + at(para, macro)), macro, f"population not named ({info['pop']}); expected one of " + ", ".join(repr(w) for w in CLASS_WORDS[cls])))
            for need in cr_needs(macro, cr):
                if need not in crs:
                    problems.append((where, line_of(tex, off + at(para, macro)), macro, f"paired outcome missing: \\{need} is not in the same paragraph"))
            m = re.fullmatch(r"CRPassBrokenAcc(P|R)", macro)
            if m and any(re.fullmatch(r"CR(Strict|Flag)BrokenAcc(P|R)", u) for u in crs):
                pair = f"CRPassSoundRej{m.group(1)}"
                if pair in cr and pair not in crs:
                    problems.append((where, line_of(tex, off + at(para, macro)), macro, f"contrast with the strict mark or flag without the pass mark's sound side: \\{pair} missing"))
        # --- sentence level: 'mutant' beside a sound-set count; run qualifiers
        sents = sentences(para)
        for i, (so, s) in enumerate(sents):
            sm = set(macro_re.findall(s))
            sound = [u for u in sm if REGISTRY.get(u, {}).get("sound") or (u in cr and cr_class(u) == "sound")]
            if sound and re.search(r"\bmutant", s, re.I):
                problems.append((where, line_of(tex, off + so + at(s, sorted(sound)[0])), sorted(sound)[0],
                                 "sentence carries a sound-set count (originals + harmless) and says 'mutant'"))
            window = s + " " + (sents[i - 1][1] if i else "")
            need_run = [u for u in sm if REGISTRY.get(u, {}).get("run")]
            need_run += [u for u in sm if u in cr and NUMERIC.fullmatch(cr[u]["value"]) and re.search(r"^[PR]$|differs|run once", cr[u]["run"])]
            if need_run and not has_runq(window):
                problems.append((where, line_of(tex, off + so + at(s, sorted(need_run)[0])), sorted(need_run)[0],
                                 "a figure that holds only in one run (or a gate run once) has no run qualifier in its sentence"))
            sl = s.lower()
            trig = [w for w in TRIGGER_WORDS if w in sl]
            if trig and not has_runq(window):
                problems.append((where, line_of(tex, off + so + at(s, trig[0])), trig[0].upper().replace(" ", ""), f"'{trig[0]}' without a run qualifier in its sentence"))
    # --- section level: post hoc and post-submission labels
    for a, b in sections(tex):
        if in_skip(a):
            continue
        sec = tex[a:b]
        used = set(macro_re.findall(sec))
        ph = sorted(u for u in used if (u in REGISTRY or V17_POSTHOC.match(u)) and V17_POSTHOC.match(u)
                    or (u in cr and cr[u]["status"] == "post hoc" and NUMERIC.fullmatch(cr[u]["value"])
                        and (POSTHOC_TAG.match(u) or cr[u]["run"].startswith("R"))))
        if ph and not POSTHOC_WORDS.search(sec):
            problems.append((where, line_of(tex, a), ph[0], "section uses a post-hoc quantity (strict mark, flag, sweep, AUC, routing or re-query) and never says 'post hoc'"))
        ps = sorted(u for u in used if u in cr and cr[u]["status"] == "post-sub")
        if ps and not POSTSUB_WORDS.search(sec):
            problems.append((where, line_of(tex, a), ps[0], "section uses a post-submission figure and never says it was run after submission"))
    return checked, problems


def flips_check(problems):
    """\\FLIPRULES must equal \\FLIPTOTAL ('all three' is then safe), and the same for the camera-ready macros."""
    vals = {}
    for p in sorted((ROOT / "gen").glob("*.tex")):
        for m in re.finditer(r"\\newcommand\{\\(FLIPRULES|FLIPTOTAL|CRFlipRulesP|CRFlipTotalP|CRFlipRulesR|CRFlipTotalR)\}\{([^}]*)\}", p.read_text()):
            vals[m.group(1)] = m.group(2)
    for a, b in (("FLIPRULES", "FLIPTOTAL"), ("CRFlipRulesP", "CRFlipTotalP"), ("CRFlipRulesR", "CRFlipTotalR")):
        if a in vals and b in vals and vals[a] != vals[b]:
            problems.append(("gen", 0, a, f"\\{a} = {vals[a]} differs from \\{b} = {vals[b]}: 'all' would overstate the reversal"))
    return problems


def run(files, cr, quiet=False, label=None):
    problems, checked = [], 0
    for name, tex in files:   # audited separately: slicing one file at its bibliography marker would drop the other
        checked, problems = audit(tex, name, checked, problems, cr)
    problems = flips_check(problems)
    if not quiet:
        print(f"claim audit{(' (' + label + ')') if label else ''}: {checked} guarded macro uses in {', '.join(n for n, _ in files)}"
              f"{'; camera-ready registry: ' + str(len(cr)) + ' macros' if cr else ''}")
        for where, ln, macro, msg in problems:
            print(f"  {where} line {ln}: \\{macro}: {msg}")
        print("  all guarded uses pass" if not problems else f"  {len(problems)} problem(s)")
    return problems


def positive_control():
    """The reviewed abstract put a count over 8 originals + 8 harmless edits in a sentence about 'mutants', and gave the
    flag's routing without its sound side; the extended guard must flag it before it is trusted on the camera-ready."""
    try:
        v17 = subprocess.run(["git", "-C", str(ROOT), "show", "v17-submission:main.tex"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print("positive control: cannot read v17-submission:main.tex from git", file=sys.stderr)
        return 1
    probs = run([("v17 main.tex", v17)], {}, quiet=True)
    s_line = v17[:v17.find("\\begin{abstract}")].count("\n") + 1
    e_line = v17[:v17.find("\\end{abstract}")].count("\n") + 1
    hits = [p for p in probs if s_line <= p[1] <= e_line]
    mutant = [p for p in hits if "mutant" in p[3]]
    print(f"positive control: {len(probs)} problem(s) on v17 main.tex, {len(hits)} in its abstract"
          f" ({len(mutant)} 'mutant' beside a sound-set count)")
    for where, ln, macro, msg in hits:
        print(f"  {where} line {ln}: \\{macro}: {msg}")
    if not mutant:
        print("positive control FAILED: the guard does not flag the reviewed abstract's population error", file=sys.stderr)
        return 1
    print("positive control: passed (the reviewed abstract is flagged)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default=str(ROOT / "main.tex"))
    ap.add_argument("--also", default=str(ROOT / "appendix.tex"), help="a second file to audit; pass '' to skip")
    ap.add_argument("--registry", default=str(ROOT / "gen" / "CR_MACROS.md"), help="camera-ready macro registry")
    ap.add_argument("--positive-control", action="store_true", help="audit the reviewed v17 main.tex; exit 1 unless its abstract is flagged")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.positive_control:
        return positive_control()
    cr = load_cr_registry(pathlib.Path(a.registry))
    files = [pathlib.Path(a.tex)]
    if a.also and pathlib.Path(a.also).is_file() and a.also != a.tex:
        files.append(pathlib.Path(a.also))
    problems = run([(p.name, p.read_text()) for p in files], cr, quiet=a.quiet)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
