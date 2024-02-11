import logging

from custom_components.mypyllant.utils import EntityList


async def test_log_on_entity_exception(caplog):
    def _raise():
        raise Exception("Init Exception")

    entities = EntityList()
    entities.append(lambda: dict(test=1))
    with caplog.at_level(logging.ERROR):
        entities.append(_raise)
    entities.append([0])
    assert len(entities) == 2
    assert "test" in entities[0]
    assert 0 in entities[1]
