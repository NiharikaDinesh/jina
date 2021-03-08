from jina.drivers.rank import Matches2DocRankDriver
from jina.executors.rankers import Match2DocRanker
from jina.proto import jina_pb2
from jina.types.sets import DocumentSet


class MockMatches2DocRankDriver(Matches2DocRankDriver):
    def __init__(self, docs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = docs

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def docs(self):
        return self._docs


class MockAbsoluteLengthRanker(Match2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(
            query_required_keys=('length',),
            match_required_keys=('length',),
            *args,
            **kwargs
        )

    def score(self, old_match_scores, query_meta, match_meta):
        new_scores = [-abs(m['length'] - query_meta['length']) for m in match_meta]
        return new_scores


def create_document_to_score():
    # doc: 1
    # |- matches: (id: 2, parent_id: 1, score.value: 2),
    # |- matches: (id: 3, parent_id: 1, score.value: 3),
    # |- matches: (id: 4, parent_id: 1, score.value: 4),
    # |- matches: (id: 5, parent_id: 1, score.value: 5),
    doc = jina_pb2.DocumentProto()
    doc.id = '1' * 20
    doc.length = 20
    for match_id, match_score, match_length in [
        (2, 3, 16),
        (3, 6, 24),
        (4, 1, 8),
        (5, 8, 16),
    ]:
        match = doc.matches.add()
        match.id = str(match_id) * match_length
        match.length = match_length
        match.score.value = match_score
    return doc


def test_chunk2doc_ranker_driver_mock_exec():
    doc = create_document_to_score()
    driver = MockMatches2DocRankDriver(DocumentSet([doc]))
    executor = MockAbsoluteLengthRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    assert len(doc.matches) == 4
    assert doc.matches[0].id == '2' * 16
    assert doc.matches[0].score.value == -4
    assert doc.matches[1].id == '3' * 24
    assert doc.matches[1].score.value == -4
    assert doc.matches[2].id == '5' * 16
    assert doc.matches[2].score.value == -4
    assert doc.matches[3].id == '4' * 8
    assert doc.matches[3].score.value == -12
    for match in doc.matches:
        assert match.score.ref_id == doc.id
        assert match.score.op_name == 'MockAbsoluteLengthRanker'
