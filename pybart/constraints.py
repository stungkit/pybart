from dataclasses import dataclass, field
from typing import Sequence, Set, List, Tuple
from enum import Enum
from math import inf
from abc import ABC, abstractmethod
import re


class FieldNames(Enum):
    WORD = 0
    LEMMA = 1
    TAG = 2
    ENTITY = 3


@dataclass(frozen=True)
class Field:
    field: FieldNames
    value: Sequence[str]  # match of one of the strings in a list


@dataclass(frozen=True)
class Label(ABC):
    @abstractmethod
    def satisfied(self, actual_labels: List[str]) -> Set[str]:
        pass


@dataclass(frozen=True)
class HasLabelFromList(Label):
    # has at least one edge with value
    value: Sequence[str]
    
    def satisfied(self, actual_labels: List[str]) -> Set[str]:
        current_successfully_matched = set()
        # at least one of the constraint strings should match, so return False only if none of them did.
        for value_option in self.value:
            # check if a regex or exact match is required
            is_regex = value_option.startswith('/') and value_option.endswith('/')
        
            # for each edged label, check if the label matches the constraint, and store it if it does,
            #   because it is a positive search (that is at least one label should match)
            for actual_label in actual_labels:
                if (is_regex and re.match(value_option[1:-1], actual_label)) or (value_option == actual_label):
                    # store the matched label
                    current_successfully_matched.add(actual_label)
        if len(current_successfully_matched) > 0:
            raise ValueError  # TODO - change to our exception
        return current_successfully_matched


@dataclass(frozen=True)
class HasNoLabel(Label):
    # does not have edge with value
    value: str
    
    def satisfied(self, actual_labels: List[str]) -> Set[str]:
        # check if a regex or exact match is required
        is_regex = self.value.startswith('/') and self.value.endswith('/')
    
        # for each edged label, check if the label matches the constraint, and fail if it does,
        #   because it is a negative search (that is non of the labels should match)
        for actual_label in actual_labels:
            if (is_regex and re.match(self.value[1:-1], actual_label)) or (self.value == actual_label):
                raise ValueError  # TODO - change to our exception
        
        return set()


@dataclass(frozen=True)
class Token:
    id: str  # id/name for the token
    capture: bool = True
    spec: Sequence[Field] = field(default_factory=list)
    optional: bool = False  # is this an optional constraint or required
    incoming_edges: Sequence[Label] = field(default_factory=list)
    outgoing_edges: Sequence[Label] = field(default_factory=list)
    is_root: bool = None  # optional field, if set, then check if this is/n't (depending on the bool value) the root


@dataclass(frozen=True)
class Edge:
    child: str
    parent: str
    label: Sequence[Label]


@dataclass(frozen=True)
class Distance:
    token1: str
    token2: str
    distance: int


@dataclass(frozen=True)
class ExactDistance(Distance):
    # 0 means no words in between... 3 means exactly words are allowed in between, etc.
    def __post_init__(self):
        if self.distance < 0:
            raise ValueError("Exact distance can't be negative")
        elif self.distance == inf:
            raise ValueError("Exact distance can't be infinity")


@dataclass(frozen=True)
class UptoDistance(Distance):
    # 0 means no words in between... 3 means up to three words are allowed in between, etc.
    #   so infinity is like up to any number of words in between (which means only the order of the arguments matters).
    def __post_init__(self):
        if self.distance < 0:
            raise ValueError("'up-to' distance can't be negative")


@dataclass(frozen=True)
class TokenTuple:  # the words of the nodes must match
    tuple_set: Set[str]  # each str is word pair separated by _


@dataclass(frozen=True)
class TokenPair(TokenTuple):  # the words of the nodes must match
    token1: str
    token2: str
    in_set: bool = True  # should or shouldn't match


@dataclass(frozen=True)
class TokenTriplet(TokenTuple):  # the words of the nodes must/n't match
    token1: str
    token2: str
    token3: str
    in_set: bool = True  # should or shouldn't match


@dataclass(frozen=True)
class Full:
    tokens: Sequence[Token] = field(default_factory=list)
    edges: Sequence[Edge] = field(default_factory=list)
    distances: Sequence[Distance] = field(default_factory=list)
    concats: Sequence[TokenTuple] = field(default_factory=list)
    
    def __post_init__(self):
        # check for no repetition
        names = [tok.id for tok in self.tokens]
        names_set = set(names)
        if len(names) != len(names_set):
            raise ValueError("used same name twice")
        
        # validate for using only names defined in tokens
        used_names = set()
        [used_names.update({edge.child, edge.parent}) for edge in self.edges]
        [used_names.update({dist.token1, dist.token2}) for dist in self.distances]
        for concat in self.concats:
            if isinstance(concat, TokenPair):
                used_names.update({concat.token1, concat.token2})
            elif isinstance(concat, TokenTriplet):
                used_names.update({concat.token1, concat.token2, concat.token3})
        
        if len(used_names.difference(names_set)) != 0:
            raise ValueError("used undefined names")


# usage examples:
#
# for three-word-preposition processing
# Full(
#     tokens=[
#         Token(id="w1", outgoing_edges=[HasNoLabel("/.*/")]),
#         Token(id="w2"),
#         Token(id="w3", outgoing_edges=[HasNoLabel("/.*/")]),
#         Token(id="proxy")],
#     edges=[
#         Edge(child="proxy", parent="w2", label=[HasLabelFromList(["/nmod|acl|advcl).*/"])]),
#         Edge(child="w1", parent="w2", label=[HasLabelFromList(["case"])]),
#         Edge(child="w3", parent="proxy", label=[HasLabelFromList(["case", "mark"])])
#     ],
#     distances=[ExactDistance("w1", "w2", distance=0), ExactDistance("w2", "w3", distance=0)],
#     concats=[TokenTriplet(three_word_preps, "w1", "w2", "w3")]
# )
#
#
# for "acl propagation" (type1)
# Full(
#     tokens=[
#         Token(id="verb", spec=[Field(FieldNames.TAG, ["/(VB.?)/"])]),
#         Token(id="subj"),
#         Token(id="proxy"),
#         Token(id="acl", outgoing_edges=[HasNoLabel("/.subj.*/")]),
#         Token(id="to", spec=[Field(FieldNames.TAG, ["TO"])])],
#     edges=[
#         Edge(child="subj", parent="verb", label=[HasLabelFromList(["/.subj.*/"])]),
#         Edge(child="proxy", parent="verb", label=[HasLabelFromList(["/.*/"])]),
#         Edge(child="acl", parent="proxy", label=[HasLabelFromList(["/acl(?!:relcl)/"])]),
#         Edge(child="to", parent="acl", label=[HasLabelFromList(["mark"])])
#     ],
# )
#
#
# for passive alternation
# Full(
#     tokens=[
#         Token(id="predicate"),
#         Token(id="subjpass"),
#         Token(id="agent", optional=True),
#         Token(id="by", optional=True, spec=[Field(FieldNames.WORD, ["^(?i:by)$"])])],
#     edges=[
#         Edge(child="subjpass", parent="predicate", label=[HasLabelFromList(["/.subjpass/"])]),
#         Edge(child="agent", parent="predicate", label=[HasLabelFromList(["/^(nmod(:agent)?)$/"])]),
#         Edge(child="by", parent="agent", label=[HasLabelFromList(["case"])]),
#         Edge(child="subjpass", parent="predicate", label=[HasNoLabel(".obj")])
#     ]
# )
