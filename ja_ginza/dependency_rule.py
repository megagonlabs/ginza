import importlib
import re
import sys

# Traverse policy definition (needed for non top-level elements)

# Element name for traverse type elements
ARC = 'arc'

# for parents with in max_hop, match only once
PARENT = 'parent'
# for descendants with in max_hop, for all, match all
CHILDREN = 'children'
# for parents with in max_hop, for all, match all
ANCESTORS = 'ancestors'
# for descendants with in max_hop, for all, match only once
DESCENDANT = 'descendant'

# Element name for max_hop elements (default=1)
MAX_HOP = 'max_hop'

# Matching regexp pattern definition

# Element name for dependency label (token.dep_) patterns (default='.*')
LABEL = 'label'
# Element name for word (token.orth_) patterns (default='.*')
WORD = 'word'
# Element name for stop-word patterns applied to word (token.orth_) (default=None)
SW = 'sw'
# Element name for lemma (token.lemma_) patterns (default='.*')
LEMMA = 'lemma'
# Element name for part-of-speech (token.pos_) patterns (default='.*')
POS = 'pos'

# Sub rule definition

# Element name for lists which have recursive sub rule list
DEPS = 'deps'

# Candidate generation action definition

# Element name for action set definition
ACTION = 'action'

# use current token as one of the candidates if the rule matches to current token
USE = {'USE'}
# generate candidates if the rule matches to current token
POP = {'POP'}
# cancel traversing if the rule matches to current token
FAIL = {'FAIL'}
# use current token as one of the candidates if the rule does not match to current token
USE_ON_FAIL = {'USE_ON_FAIL'}
# generate candidates if the rule does rule match to current token
POP_ON_FAIL = {'POP_ON_FAIL'}
# continue traversing if the rule does not match to current token
CONTINUE_ON_FAIL = {'CONTINUE_ON_FAIL'}
GOAL = USE | POP
GREEDY = USE | POP_ON_FAIL
USE_ALWAYS = USE | USE_ON_FAIL
POP_ALWAYS = POP | POP_ON_FAIL
GOAL_ALWAYS = USE_ALWAYS | POP_ALWAYS
actions = {
    v: v for v in USE | POP | FAIL | USE_ON_FAIL | POP_ON_FAIL | CONTINUE_ON_FAIL | {
        'GOAL', 'GREEDY', 'USE_ALWAYS', 'POP_ALWAYS', 'GOAL_ALWAYS',
    }
}

# Element name for enabling debug mode (default=False)
DEBUG = 'debug'

# Element name for debug information (default='')
INFO = 'info'


class DependencyRule:
    @staticmethod
    def _get_re(data, field, count):
        if field in data:
            return re.compile('^({})$'.format(data[field].lower())), count + 1
        else:
            return re.compile(r'^.*$'), count

    def __init__(self, data=None, nest_level=0):
        is_top = nest_level == 0
        field_count = 0

        self.nest_level = nest_level
        if ARC in data:
            if is_top:
                raise Exception('arc not allowed in top rule')
            v = data[ARC]
            if v not in [ANCESTORS, DESCENDANT, PARENT, CHILDREN]:
                raise Exception('arc must be ancestors, descendants, parent, or children: {}'.format(v))
            field_count += 1
            self.arc = v
        elif is_top:
            self.arc = None
        else:
            raise Exception('arc must be specified')

        if MAX_HOP in data:
            if is_top:
                raise Exception('max_hop not allowed in top rule')
            field_count += 1
            v = data[MAX_HOP]
            if isinstance(v, int):
                if v > 0:
                    self.max_hop = v
                else:
                    raise Exception('hop must be > 0: {}', format(v))
            else:
                raise Exception('hop must be int: {}', format(v))
        else:
            self.max_hop = 1

        if LABEL in data and is_top:
            raise Exception('label not allowed in top rule')
        self.label, field_count = DependencyRule._get_re(data, LABEL, field_count)

        self.word, field_count = DependencyRule._get_re(data, WORD, field_count)
        self.lemma, field_count = DependencyRule._get_re(data, LEMMA, field_count)
        self.pos, field_count = DependencyRule._get_re(data, POS, field_count)

        if DEPS in data:
            field_count += 1
            self.deps = [DependencyRule(sub_data, nest_level + 1) for sub_data in data[DEPS]]
        elif ACTION not in data:
            raise Exception('action must be specified if no deps')
        else:
            self.deps = None

        if ACTION in data:
            v = data[ACTION]
            if isinstance(v, list):
                self.actions = set(v)
            elif isinstance(v, set):
                self.actions = v
            else:
                self.actions = {actions[v]}
            for v in self.actions:
                if v not in actions:
                    raise Exception('invalid action: {}'.format(v))
            field_count += 1
        else:
            self.actions = set()

        if SW in data:
            self.stop_word, field_count = DependencyRule._get_re(data, SW, field_count)
        else:
            self.stop_word = None

        if DEBUG in data:
            self.debug = data[DEBUG]
            field_count += 1
        else:
            self.debug = False

        if INFO in data:
            self.info = data[INFO]
            field_count += 1
        else:
            self.info = None

        if field_count != len(data.keys()):
            print('invalid field(s) contained: {}'.format(data.keys() - {
                ARC,
                MAX_HOP,
                LABEL,
                WORD,
                LEMMA,
                POS,
                DEPS,
                ACTION,
                SW,
                DEBUG,
                INFO,
            }), file=sys.stderr)

    @staticmethod
    def _content(regexp):
        return str(regexp)[14:-4]

    def __str__(self):
        return 'DependencyRule({})'.format(','.join([
            '{}:{}'.format(f, v) if f else str(v) for f, v in [
                kv for kv in [
                    ('', self.info),
                    ('', self.arc),
                    ('max_hop', self.max_hop),
                    ('', DependencyRule._content(self.label)),
                    ('word', DependencyRule._content(self.word)),
                    ('lemma', DependencyRule._content(self.lemma)),
                    ('pos', DependencyRule._content(self.pos)),
                    ('', str(self.actions) if self.actions else ''),
                ] if kv[1]
            ]
        ]))

    def extract_candidates(self, utterance, debug=False):
        for token in utterance:
            matched_tokens = self.check_token(token, 1, {token.i}, debug)
            if matched_tokens is not None:
                return sorted(matched_tokens, key=lambda t: t.i)
        return None

    def _indent(self):
        return ' ' * ((self.nest_level + 1) * 4)

    def filter_stop_words(self, tokens, debug):
        if not self.stop_word:
            return tokens
        else:
            if debug:
                indent = self._indent()
            else:
                indent = None
            debug and print(indent + 'apply stop_word')
            result = [token for token in tokens if not self.stop_word.match(token.orth_)]
            if len(result) == len(tokens):
                return tokens
            else:
                debug and print(indent + 'stop_word matched: {}'.format(DependencyRule._content(self.stop_word)))
                return result

    def match_stop_words(self, token, debug):
        if self.stop_word:
            indent = self._indent() if debug else None
            debug and print(indent + 'apply stop_word')
            if self.stop_word.match(token.orth_.lower()):
                debug and print(indent + 'stop_word matched: {}'.format(DependencyRule._content(self.stop_word)))
                return True
        return False

    def check_token(self, token, hop, token_history, debug=False):
        debug = debug or self.debug
        indent = self._indent() if debug else None
        debug and print(indent[2:] + 'check_token({}, {}:{}, {}, {})'.format(
            str(self), token.i, token.orth_, token.lemma_, hop, token_history))
        # check word-level rules
        if (
                not self.word.match(token.orth_.lower())
        ) or (
                not self.lemma.match(token.lemma_.lower())
        ) or (
                not self.pos.match(token.pos_.lower())
        ) or (
            self.match_stop_words(token, debug=debug)
        ):
            debug and print(indent + 'word not matched')
            if not CONTINUE_ON_FAIL <= self.actions:
                debug and print(indent + 'failed')
                return None

        debug and print(indent + 'word matched')
        sub_result = []
        if self.deps:
            # dive into sub rules
            for i, sub in enumerate(self.deps):
                sub_result = sub.traverse_dependency(token, 0, token_history, debug)
                if sub_result is not None:
                    debug and print(indent + 'traverse_dependency({}, {}) -> {}'.format(
                        self,
                        token.lemma_,
                        [t.lemma_ for t in sub_result],
                    ))
                    break
        if sub_result is not None:
            debug and print(indent + 'deps matched')
            if FAIL <= self.actions:
                debug and print(indent + 'fail')
                return None
            if USE <= self.actions:
                debug and print(indent + 'use: {}'.format(token.lemma_))
                return self.filter_stop_words([token] + sub_result, debug)
            else:
                return self.filter_stop_words(sub_result, debug)
        else:
            debug and print(indent + 'deps not matched')
            result = [token]
            if POP_ON_FAIL <= self.actions:
                debug and print(indent + 'pop_on_fail: {}'.format([t.lemma_ for t in result]))
                return self.filter_stop_words(result, debug)
            debug and print(indent + 'failed')
            return None

    def traverse_dependency(self, token, hop, token_history, debug=False):
        debug = debug or self.debug
        indent = self._indent() if debug else None
        debug and print(indent[2:] + 'traverse_dependency({}, {}, {}, {})'.format(
            self, token.lemma_, hop, token_history))
        hop += 1
        # over max_hop
        if hop > self.max_hop:
            debug and print(indent + 'hop overs {}'.format(self.max_hop))
            return None

        if self.arc in [ANCESTORS, PARENT]:
            target = token.head
            debug and print(indent + 'target: {}'.format(target.lemma_))
            # in history
            if target.i in token_history:
                debug and print(indent + 'in history')
                return None
            dep = token.dep_.lower()
            debug and print(indent + '{}>{}>{}'.format(token.lemma_, dep, target.lemma_))
            result = None
            if self.label.match(dep):
                debug and print(indent + 'label matched')
                result = self.check_token(target, hop, token_history | {target.i}, debug)
                if result is None:
                    debug and print(indent + 'no result')
            else:
                debug and print(indent + 'label not matched')
            if result is None:
                return self.traverse_dependency(target, hop, token_history | {target.i}, debug)
            if self.arc == PARENT:
                return result
            sub_result = self.traverse_dependency(target, hop, token_history | {target.i}, debug)
            if sub_result is None:
                return result
            else:
                return result + sub_result
        elif self.arc in [DESCENDANT, CHILDREN]:
            all_result = None
            for target in token.children:
                debug and print(indent + 'target: {}'.format(target.lemma_))
                # in history
                if target.i in token_history:
                    debug and print(indent + 'in history')
                    continue
                dep = target.dep_.lower()
                debug and print(indent + '{}<{}<{}'.format(token.lemma_, dep, target.lemma_))
                if self.label.match(dep):
                    debug and print(indent + 'label matched')
                    result = self.check_token(target, hop, token_history | {target.i}, debug)
                    if result is None:
                        debug and print(indent + 'no result')
                    else:
                        if self.arc == CHILDREN:
                            if all_result is None:
                                all_result = result
                            else:
                                all_result += result
                            debug and print(indent + 'continue')
                        else:
                            return result
                else:
                    debug and print(indent + 'label not matched')
            return all_result
        else:
            raise Exception('arc must be ancestors, descendants, parent, or children: {}'.format(self.arc))


def parse_rule_maps(json):
    return [DependencyRule(rule) for rule in json]


def import_from_module(module_name):
    module = importlib.import_module(module_name)
    return parse_rule_maps(module.DEPENDENCY_RULES)


__all__ = [
    'DependencyRule',
    'parse_rule_maps',
    'import_from_module',
    'ARC',
    'ANCESTORS',
    'DESCENDANT',
    'PARENT',
    'CHILDREN',
    'MAX_HOP',
    'LABEL',
    'WORD',
    'LEMMA',
    'POS',
    'ACTION',
    'USE',
    'POP',
    'FAIL',
    'USE_ON_FAIL',
    'POP_ON_FAIL',
    'CONTINUE_ON_FAIL',
    'GOAL',
    'GREEDY',
    'USE_ALWAYS',
    'POP_ALWAYS',
    'GOAL_ALWAYS',
    'DEPS',
    'SW',
    'DEBUG',
    'INFO',
]
